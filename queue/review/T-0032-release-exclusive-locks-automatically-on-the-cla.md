---
id: T-0032
title: Release exclusive locks automatically on the claimed/ -> review/ transition
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T22:08:32Z
lease_expires_at: 2026-09-08T00:08:32Z
worktree: null
branch: task/T-0032
exclusive: []
touches: [ops/lib/queue.py, ops/review, ops/lib/check-lock-lifecycle, queue/]
pins_affected: []
reviewer: agent/reviewer-42
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/claim` takes a `LOCKS/<resource>.lock` for every resource a task declares in `exclusive:`. Two things
release one: `queue.py sweep`, when the lease expires, and deleting the file by hand. Nothing else.

**There is no supported claimed -> review transition at all.** Every agent in this repo performs it with
`git mv` plus a hand edit of `state:` and `reviewer:`. That is why the lock is never released: there is no
code path at the moment the work stops.

This is currently latent and it is armed. `cmd_check` already treats an orphaned lock as an error -

    LOCKS/<res>.lock held by T-nnnn, which is not in claimed/

- so the moment a task holding `exclusive:` moves to `review/`, `ops/queue-check` starts FAILING for every
agent in every worktree, not just the owner's. Today exactly one lock exists (`scenic-index.lock`, held by
T-0024, still claimed), so nobody has hit it. T-0024 is signed off work away from hitting it.

Fail-closed is the right behaviour for that check and should not change. The gap is that the transition has
no home.

- Add the transition as a command - `queue.py review <id> --reviewer <name>`, wrapped as `ops/review` in the
  style of `ops/claim` - that moves the file, sets `state:` and `reviewer:`, releases every lock the task
  holds, and appends to `## Log`. One operation, so the lock cannot be forgotten independently of the move.
- It must refuse when `reviewer` equals `owner`. `cmd_check` already rejects that after the fact; refusing at
  the transition is the same argument as T-0056's brief check - the last moment it can still be prevented.
- Releasing at review, not at done, is the judgement to argue. For: review takes hours or days, and a task
  sitting in review is not editing the serial resource it locked, so holding `scenic-index` or `prod` that
  long starves everyone. Against: a FAIL sends it back to the owner, who may need the resource again. The
  answer to that is `ops/lock`, which already exists to acquire the locks a claimed task declares - so the
  round trip is supported, and this is not a one-way door.
- Only release locks THIS task holds. A lock whose file names a different task id must be left alone and
  reported, not silently taken over.
- Demonstrate red: with a task holding `exclusive:`, perform the hand `git mv` that everyone does today and
  show `ops/queue-check` failing; then perform the same transition through the new command and show it clean.
  That red run is the whole justification for the command existing, so it belongs in the log verbatim.

## Log
- 2026-09-07T22:08:32Z claimed by agent/unknown; lease until 2026-09-08T00:08:32Z

- 2026-09-08T04:40Z brief written, claimed and implemented by agent/claude-opus-5. Stacked on task/T-0056,
  which owns ops/lib/queue.py.

  **The brief was the placeholder** when I picked this up - the third time this session - so it was written
  and committed before any code. That is now enforced by T-0056, which this branch is stacked on.

  **New `queue.py review <id> --reviewer <name>`, wrapped as `ops/review`.** It moves claimed/ -> review/,
  sets `state:` and `reviewer:`, releases the locks the task holds, and logs - one operation, so the lock
  cannot be forgotten independently of the move.

  **The red run is the whole justification and it reproduces exactly as the brief predicted.** Perform the
  hand transition every agent has been doing - `git mv` plus a `sed` on the fields - with a task holding
  `exclusive: [scenic-index]`:

      - queue/LOCKS/scenic-index.lock held by T-9101, which is not in claimed/

  `ops/queue-check` fails, and it fails for every agent in every worktree, not just the owner's. That is
  latent right now: exactly one lock exists, `scenic-index`, held by T-0024, which is still claimed. T-0024 is
  signed-off work away from breaking the gate for the whole fleet.

  **Releasing at review, not at done.** Argued in the brief and I stand on it: a task in review is not editing
  the resource it locked, review takes hours or days, and holding `scenic-index` or `prod` that long starves
  everyone. The objection - a FAIL sends it back to the owner - is answered by `ops/lock`, which already
  exists to acquire the locks a claimed task declares. The round trip is supported, so it is not a one-way
  door. `cmd_check`'s orphaned-lock rule stays fail-closed and unchanged; the gap was that the transition had
  no home, not that the check was wrong.

  **`reviewer == owner` refused at the transition**, on the same argument as T-0056's brief guard: after the
  fact is a report, at the transition is a prevention. `cmd_check` keeps its own check for anything that gets
  there another way.

  **A lock held by another task is never taken over.** Every lock is inspected before any is unlinked, so a
  foreign lock cannot leave the task half-released - the same ordering `cmd_claim` uses when acquiring.

  **New `ops/lib/check-lock-lifecycle`**, seven cases, built like `check-brief-required`: a throwaway repo,
  the real `queue.py` end to end.

      ok: claim takes the lock and names the task
      ok: a hand git mv leaves the lock and queue-check FAILS - the red run this command exists for
      ok: review releases the lock, moves the task, and queue-check is clean
      ok: a task declaring no exclusive resources still moves
      ok: reviewer == owner refused, and the task did not move
      ok: a lock held by another task is left alone and the transition refuses
      ok: a task already in done/ cannot be handed to review
      LOCK LIFECYCLE OK

  Three mutations, each failing a named case, source restored byte-identical: not releasing the lock; taking
  over a foreign lock; allowing reviewer == owner.

  **A bug found on the way, in code I did not write.** `queue.py review` with no id raised `IndexError` and
  printed a traceback. So do `claim`, `lock` and `new` - they read `argv[0]` directly and always have.
  Guarded once in `main()`. A tool that answers a typo with a stack trace teaches people to stop reading its
  output, which is expensive in a repo whose whole premise is that output gets read.

  **What I did badly, stated rather than buried:** `ops/lib/queue.py` is now **498 lines** against the
  300-line cap. It was already 415 before I touched it, and nothing has ever said so because
  `ops/lib/check-line-cap` globs Swift only (filed as T-0058 from agent/reviewer-33's T-0028 review). I chose
  not to bundle a refactor of the queue's core into a task about lock release, but "the check cannot see it"
  is not a defence, so the breach is filed as **T-0059** with the seams identified, depending on T-0058 so the
  cap actually enforces the result.

  **Verification:** `ops/lib/check-lock-lifecycle` -> `LOCK LIFECYCLE OK`; `ops/lib/check-brief-required` ->
  `BRIEF CHECK OK` (T-0056's check still passes on top of this change); `ops/check-pins` -> `PINS ok=9
  skipped=0 pending=3 expired=0 failed=0 tier=linux`; `ops/queue-check` -> `QUEUE OK (42 tasks)`.
  `ops/review` and `ops/lib/check-lock-lifecycle` committed 100755 per P-OPS-01. GitHub Actions is DISABLED
  repo-wide (T-0053), so there is no CI signal at all.

  **What to attack.** The new check is wired into no pin, same as T-0056's - `pins/PINS.yaml` is outside this
  task's `touches:` and there is now a live pin-id collision (T-0057) that makes adding one worse than
  waiting. Nothing forces anyone to USE `ops/review`; the hand transition still works and still breaks the
  gate, and the only thing standing between them is that `queue-check` now fails loudly rather than silently.
  Whether `ops/review` should also refuse when the task's `## Log` has no entry since it was claimed - i.e.
  handing over with nothing written down - is a real question I did not answer.

- 2026-09-08T04:45Z touches: extended to ops/review and ops/lib/check-lock-lifecycle before staging them.
  The pre-commit hook refused the first attempt - `ops/review is outside T-0032 touches:` - because the
  edit that was supposed to add them when the brief was written silently did nothing: it matched
  `touches: []`, and this task was filed with a non-empty list already. The hook caught a real mistake of
  mine, which is the first time in this session it has fired on anything other than a demonstration.

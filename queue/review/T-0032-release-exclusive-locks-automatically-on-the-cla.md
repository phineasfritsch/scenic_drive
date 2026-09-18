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
- 2026-09-18T19:05:09Z review by agent/rv-t0032 (detached worktree `.worktrees/rv-t0032` at `origin/main` = `4d6698a`, removed at the end; throwaway `git init` fixtures outside the tree; two mutations of `ops/lib/queue.py` in the worktree, each restored to `git hash-object` `78f9d9bf0bedbe433ffdea3a914bb57492e7b1bb` with `git status --short` empty). **FAIL.** The command works; the guard that proves it does not, and the transition leaks a lock in one ordinary input.

  **First, where the work lives.** `gh pr view 42` says `state: OPEN, mergedAt: null, headRefOid 00ad097`, and `git merge-base --is-ancestor origin/task/T-0032 origin/main` exits 0: the content IS on main, carried in by `82ef261 Merge remote-tracking branch 'origin/main' into task/T-0068`, never through this PR. #42 is a stale open ref. `git diff 00ad097 4d6698a -- ops/review ops/lib/check-lock-lifecycle` prints nothing - both deliverables survive byte-identical - while `ops/lib/queue.py` has moved +615/-67 since, and that movement is what broke them.

  **BLOCKING 1: `ops/lib/check-lock-lifecycle` is RED at this head**, and it is the only assertion anywhere that `review` releases a lock. `bash ops/lib/check-lock-lifecycle` ->

      FAIL: review did not release the lock
      FAIL: review refused a task that holds no locks
      LOCK LIFECYCLE FAIL

  exit 1, against the Log's `LOCK LIFECYCLE OK`. Two independent later causes, both outside this task. (a) T-0063 inserted `_would_duplicate_on_merge` into `cmd_review` ahead of the lock work, and the check's fixture is a bare `mktemp -d`: in a non-git tree every `review` now prints `T-9102: cannot read main, so whether merging this branch would duplicate the task file / cannot be decided` and exits 1 before a lock is looked at. (b) `MIN_TASKS = 40` (`queue.py:198`) was also added later, so case 3's "queue-check is clean" cannot pass on a one-task fixture even after a `git init` - measured: review succeeded (`released=[scenic-index]`, `LOCKS: []`) and `check` -> `QUEUE CHECK FAIL / - only 1 task(s) visible, floor is 40`. The property still HOLDS in a real repo (48-task git fixture: `T-9102 -> queue/review/...  released=[scenic-index]`, `LOCKS now: []`, `QUEUE OK (48 tasks)`); what is gone is the demonstration.

  **BLOCKING 2: case 6 passes vacuously.** Mutating `cmd_review` to take over any lock on a declared resource - `mine.append((res, lock))` unconditionally - still prints `ok: a lock held by another task is left alone and the transition refuses`, because the merge gate refuses first and satisfies all four conjuncts without executing the guard. The same mutation in a git fixture shows what the case is blind to: `T-9105 -> queue/review/T-9105-demo.md  released=[scenic-index]`, exit 0, `LOCKS after: []` - T-9999's lock stolen and deleted. Control: deleting the `reviewer == owner` refusal DID turn case 5 red (`FAIL: reviewer == owner was accepted (rc=1)`), so five of seven cases still bite and case 6 does not.

  **BLOCKING 3: the transition fails OPEN on a lock the task holds but no longer declares** - the post-claim `exclusive:` edit `cmd_lock`'s own docstring was written for (T-0011). Claim T-9107 with `exclusive: [pbxproj, package-swift]`, narrow it to `[pbxproj]` while claimed (`check` -> `QUEUE OK (48 tasks)`; nothing warns), then

      $ queue.py review T-9107 --reviewer agent/bob
      T-9107 -> queue/review/T-9107-demo-9107.md  reviewer=agent/bob  released=[pbxproj]     exit 0
      $ queue.py check
      QUEUE CHECK FAIL
       - queue/LOCKS/package-swift.lock held by T-9107, which is not in claimed/

  Exit 0, task moved, lock orphaned, gate now failing for every agent in every worktree - the exact fleet-wide breakage this task exists to prevent, produced by its own command reporting success. `cmd_review` iterates `fm["exclusive"]`; it never asks `LOCKS/` which locks name this id, though `cmd_check` does at `queue.py:441-446`. "Releases every lock the task holds" and "one operation, so the lock cannot be forgotten independently of the move" are both false for this input.

  **BLOCKING 4: the sentence the release-at-review judgement rests on is false at this head.** "The answer to that is `ops/lock` ... so the round trip is supported, and this is not a one-way door." Only the acquiring half exists: after `review T-9109`, `lock T-9109` -> `T-9109 is in review/, not claimed/ - only a claimed task holds locks`, `claim T-9109` -> `T-9109 is in review/, not ready/`, and no command moves review/ -> claimed/ - the identical no-home defect this task was filed about, one state later. With `prod` re-taken meanwhile: `cannot lock prod: held by T-9110 agent/carol` and `QUEUE CHECK FAIL / - queue/claimed/T-9109-demo-9109.md: prod.lock is held by someone else`, unrepairable by any command. Release-at-review may still be right; it needs a defence that does not cite a round trip that is not there.

  **The T-0141 hole, answered: a gap, and not the one this task closed.** The fleet's sign-off is claimed/ -> done/ **directly** (this file's own siblings: `queue/done/T-0141-*.md`, precedent `d77ee55`), which never passes through `ops/review`. Reproduced: claim T-9108 (`scenic-index2.lock`), hand `mv` + field edit to done/ -> `QUEUE CHECK FAIL / - queue/LOCKS/scenic-index2.lock held by T-9108, which is not in claimed/`; `sweep` -> `SWEEP done (0 moved, 0 kept)`, lock intact; `review T-9108` and `lock T-9108` both -> `T-9108 is in done/, not claimed/`. There is no `cmd_done` (usage lists new/check/sweep/review/next/claim/lock). So the hand `git rm` that T-0141's reviewer was blocked on is the ONLY mechanism that exists, not a workaround around this command. T-0032 disclosed the shape ("nothing forces anyone to USE ops/review"); `queue/backlog/T-0095` covers review/ -> done/ for the stale-copy defect only, is unclaimed, and says nothing about locks. Recordable here, and the follow-up with the most teeth.

  **Recordable, not blocking:** stale Log counts (`498` lines -> `1046`; `QUEUE OK (42 tasks)` -> `QUEUE OK (152 tasks)`; the `PINS ok=9` line not re-run) - the 300-line breach is now 3.5x the cap under T-0059; the disclosed wiring gap is still true and is the MECHANISM of the two blockers above (`grep -rn check-lock-lifecycle pins/ .github/ ops/` finds the name only inside the script and in task files - no pin, no CI, which is why it sat red for ten days); PR #42 should be closed so "open PR" stops contradicting the tree; and `cmd_check:438` tests lock ownership by substring (`tid not in ...`) where `cmd_review` splits and `cmd_lock` uses `startswith` - three spellings of one question, unreachable while an id is `T-` plus four digits.

  **Verified true as claimed:** `git ls-files -s` -> `100755` for `ops/review` and `ops/lib/check-lock-lifecycle`, and `bash ops/lib/check-exec-bits` -> `P-OPS-01: 53 files, 23 required present, all modes correct`; `bash ops/queue-check` -> `QUEUE OK (152 tasks)`, exit 0, run bare.

  **Not got to:** `ops/test` (nothing here touches a Linux target and `ops/test` shells `swift test` with no `--scratch-path`, which CLAUDE.md forbids on a shared box) and the full `ops/check-pins` (no pin references this check, so no assertion of this task's moves); `_would_duplicate_on_merge` itself is T-0063's and was not attacked beyond its effect here; two concurrent `review` runs racing one lock; `queue/README.md`'s description of the transition. I changed nothing and made no transition - the verdict is the orchestrator's to apply.

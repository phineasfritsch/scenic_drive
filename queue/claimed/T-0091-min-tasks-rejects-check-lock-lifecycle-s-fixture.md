---
id: T-0091
title: MIN_TASKS rejects check-lock-lifecycle's fixture, and merge-rehearse cannot see the collision
state: claimed
owner: agent/lock-lifecycle
owner_session: d217767a
claimed_at: 2026-09-08T11:02:25Z
lease_expires_at: 2026-09-08T15:02:25Z
worktree: null
branch: task/T-0091
exclusive: []
touches: [ops/lib/check-lock-lifecycle, ops/lib/queue.py, ops/merge-rehearse, ops/lib/rehearse-gates]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**Two guards that are each correct alone are incompatible, and the tool built to find exactly this kind of
collision cannot see it.**

`ops/lib/check-lock-lifecycle` (from [[T-0032]]) copies `ops/lib/queue.py` into a `mktemp -d`, builds a
one-task queue there and exercises the claim -> review transition against it. [[T-0073]]'s round-two fix added
`MIN_TASKS = 40` to `cmd_check`, so `queue-check` inside that fixture now reports:

    FAIL: queue-check not clean after review: QUEUE CHECK FAIL
     - only 1 task(s) visible, floor is 40 - a queue-check that inspected nothing still reports success,
       and that IS P-PROC-01 passing

Measured:

    task/T-0032   LOCK LIFECYCLE OK     exit 0      <- where the check was written, predates the floor
    task/T-0063   LOCK LIFECYCLE FAIL   exit 1
    task/T-0087   LOCK LIFECYCLE FAIL   exit 1

Neither task is wrong. `MIN_TASKS` exists because `QUEUE OK (0 tasks)` was a real vacuous pass and P-PROC-01's
whole assertion is `bash ops/queue-check >/dev/null`. The fixture exists because the lock lifecycle needs a
tree it can destroy. They simply cannot both hold as written.

**The second half is the more important one.** `ops/merge-rehearse` ([[T-0065]]) runs `queue-check`,
`check-exec-bits`, `check-line-cap` and a duplicate-pin-id scan after every merge. It does **not** run
`check-lock-lifecycle` or `check-brief-required`. So a collision of precisely the shape the rehearsal exists to
catch — two branches green alone, red together — is invisible to it, and this one was found by an agent
noticing a red check while working on something else. That is luck, not a process.

- Decide which side gives. Candidates: the fixture builds enough tasks to clear the floor (honest, ugly, and
  keeps both guards intact); or `MIN_TASKS` does not apply to a tree that is not a git worktree, the same
  three-way distinction [[T-0063]] just had to make for its own guard — but note that is a bypass, and
  CLAUDE.md's premise is that bypasses get used.
- **Do not make the check green by lowering `MIN_TASKS`.** That is the ratchet the floor exists to be, and
  `.githooks/commit-msg` guards it for a reason.
- Add `check-lock-lifecycle` and `check-brief-required` to `ops/merge-rehearse`'s gate set. Both are cheap and
  both are exactly the kind of check whose failure only appears in a merged tree. Note the rehearsal's own
  budget argument — it deliberately skips `ops/test` because the tiers dominate runtime — and these two do not.
- Red demonstration is already written: run `bash ops/lib/check-lock-lifecycle` on `task/T-0063` and on
  `task/T-0032`.

## Log
- 2026-09-08 filed by agent/claude-opus-5. Found by the T-0087 fix agent, which reported the check was already
  red before its own change; confirmed on three branches here.
- 2026-09-08T11:02:25Z claimed by agent/lock-lifecycle; lease until 2026-09-08T15:02:25Z

- 2026-09-08T11:12:18Z **touches widened**: `ops/lib/rehearse-gates` added. The brief names `ops/merge-rehearse`
  as the file holding the gate set, and it did when this task was filed; [[T-0065]] landed between the filing
  and the claim and moved every gate into `ops/lib/rehearse-gates` so the set could be RUN rather than copied.
  The second half of the brief is unreachable without it.

- 2026-09-08 **the collision, and which side gave.**

  **RED** (`bash ops/lib/check-lock-lifecycle` on this worktree, before any change - the fixture builds a
  one-task queue and `cmd_check`'s floor is 40):

      ok: claim takes the lock and names the task
      ok: a hand git mv leaves the lock and queue-check FAILS - the red run this command exists for
          - queue/LOCKS/scenic-index.lock held by T-9101, which is not in claimed/
      FAIL: queue-check not clean after review: QUEUE CHECK FAIL
       - only 1 task(s) visible, floor is 40 - a queue-check that inspected nothing still reports success, and that IS P-PROC-01 passing
      ok: a task declaring no exclusive resources still moves
      ok: reviewer == owner refused, and the task did not move
      ok: a lock held by another task is left alone and the transition refuses
      ok: a task already in done/ cannot be handed to review
      LOCK LIFECYCLE FAIL
      EXIT=1

  Neither candidate in the brief was taken. Lowering `MIN_TASKS` is the ratchet giving way ([[T-0079]] is
  still open precisely because nothing in `.githooks/commit-msg` guards that constant - it guards
  `pins/floor_linux.txt` and `pins/floor_ios.txt` only, so the constant's protection today is that nobody
  edits it). Inflating the fixture to forty tasks buys the number and loses the meaning: a lock-lifecycle
  fixture with forty tasks in it is thirty-nine tasks of noise wrapped around the one the transition touches,
  and the next agent to add a case has to keep the padding alive.

  **What changed.** `cmd_check` now distinguishes a queue that GREW from one that was BUILT.

      queue.py check                    len(seen) >= MIN_TASKS      unchanged, byte for byte
      queue.py check --expect-tasks N   len(seen) == N, N >= 1      for a tree the caller constructed

  **Why the floor's guarantee is intact, stated as four properties:**

  1. **The default path did not move.** P-PROC-01's whole assertion is `bash ops/queue-check >/dev/null`,
     `.github/workflows/linux-core.yml` runs the same line, and neither passes an argument. Both reach the
     `MIN_TASKS` branch and nothing else. Measured on this tree: `QUEUE OK (95 tasks)`, exit 0.
  2. **The declared form is STRICTER on the tree it is used on, not weaker.** It is an equality. It fails on
     a task that vanished *and* on one that appeared; the floor only ever caught the first, and only after
     thirty-nine had gone. A fixture whose `reset_repo` silently stopped writing its task fails here and
     would have passed a floor of 1.
  3. **The vacuous case stays unsayable.** `--expect-tasks 0` is REFUSED (exit 2), not failed - there is no
     value of N that says "this run inspected nothing and that is fine". Executed:

         $ python ops/lib/queue.py check --expect-tasks 0
         queue.py check: --expect-tasks 0 would declare that a run which inspected nothing is correct, and that is the one state the population assertion exists to refuse
         rc=2

  4. **It cannot become a standing bypass in the real queue.** The only value that satisfies an equality is
     the true population, which is already far above the floor and which stops being true the moment anybody
     files a task. Executed - the shape an agent would reach for to dodge the floor, on the real queue:

         $ python ops/lib/queue.py check --expect-tasks 1
         QUEUE CHECK FAIL
          - 95 task(s) visible, but this tree was declared to hold exactly 1 - a check run against a tree with a different population than the caller built is not evidence about the tree the caller meant

     A bypass that invalidates itself on the next commit is not one. A typo does not silently fall back to
     the floor either; unknown arguments are a hard error, so a check cannot stop running unnoticed:

         $ python ops/lib/queue.py check --expect-task 1
         queue.py check: unknown argument '--expect-task' (check takes only --expect-tasks N)
         rc=2
         $ python ops/lib/queue.py check --expect-tasks xyz
         queue.py check: --expect-tasks wants an integer, got 'xyz'
         rc=2

  **The fixture keeps its own vacuity guard, and it runs on every invocation.** A declared population that
  nobody has seen rejected is not an assertion, so `check-lock-lifecycle` now carries cases 3b and 3c: on the
  same one-task tree, `--expect-tasks 2` must FAIL and `--expect-tasks 0` must be REFUSED. If the argument
  were ignored, or the equality never evaluated, both go green and the file reports it.

  Case 3 also stopped grepping for `^QUEUE OK` and reads the exit code. Matching success wording is the same
  defect as matching failure wording ([[T-0065]]), in the direction where a check that prints its banner and
  exits 1 reads as clean.

  **GREEN** (`bash ops/lib/check-lock-lifecycle`, same command, same worktree):

      ok: claim takes the lock and names the task
      ok: a hand git mv leaves the lock and queue-check FAILS - the red run this command exists for
          - queue/LOCKS/scenic-index.lock held by T-9101, which is not in claimed/
      ok: review releases the lock, moves the task, and queue-check is clean (QUEUE OK (1 tasks, exactly the declared population))
      ok: a wrong declared population FAILS on the same tree - the count is really being checked
      ok: --expect-tasks 0 is refused outright, so the vacuous pass cannot be declared into legitimacy
      ok: a task declaring no exclusive resources still moves
      ok: reviewer == owner refused, and the task did not move
      ok: a lock held by another task is left alone and the transition refuses
      ok: a task already in done/ cannot be handed to review
      LOCK LIFECYCLE OK
      EXIT=0

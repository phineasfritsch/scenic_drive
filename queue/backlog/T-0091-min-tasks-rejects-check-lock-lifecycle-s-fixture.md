---
id: T-0091
title: MIN_TASKS rejects check-lock-lifecycle's fixture, and merge-rehearse cannot see the collision
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-lock-lifecycle, ops/lib/queue.py, ops/merge-rehearse]
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

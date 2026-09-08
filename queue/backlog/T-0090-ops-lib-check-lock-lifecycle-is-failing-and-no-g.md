---
id: T-0090
title: ops/lib/check-lock-lifecycle is FAILING and no gate runs it, so ops/test and CI stay green over a red checker
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/test]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Found while checking, per HARD RULE 6, whether T-0087's change to `ops/lib/queue.py` had turned anything
else red. It had not - but the checker was already red, and nothing anywhere runs it.

Executed on task/T-0087 at 176a1b2, worktree wt/T-0087:

    $ PYTHON=$(command -v python) bash ops/lib/check-lock-lifecycle
    ok: a hand git mv leaves the lock and queue-check FAILS - the red run this command exists for
        - queue/LOCKS/scenic-index.lock held by T-9101, which is not in claimed/
    FAIL: review did not release the lock
    FAIL: review refused a task that holds no locks
    ok: reviewer == owner refused, and the task did not move
    ok: a lock held by another task is left alone and the transition refuses
    ok: a task already in done/ cannot be handed to review
    LOCK LIFECYCLE FAIL
    EXIT=1

Pre-existing, not a regression. The same script over the merge-base copy of queue.py (aed8ae7, before
T-0087 touched it) prints byte-identical output and the same exit 1; the demonstration is
`.artifacts/was-it-me.sh` in that worktree, which checks the file out at each ref and restores it.

The second half is the load-bearing half. Nothing runs this:

    $ grep -n "check-lock-lifecycle\|check-brief-required" ops/test ops/sane .github/workflows/*.yml
    (no output)

`ops/test` counts Swift, TS and pytest JUnit; `ops/sane` does not call it; CI does not call it. So the
whole of `ops/lib/` is a tier of checks that exists, is executable, is committed 100755 by P-OPS-01, and is
run only when a human remembers its filename. `bash ops/test` printing TESTS linux=50/50 failed=0 and
`ops/check-pins` printing failed=0 are both true and both silent about a red checker in the same tree.
That is the repository's own premise turned on itself: a check nobody runs cannot contradict anybody.

Two separable pieces of work, and they should probably be two tasks:

1. Make some gate run `ops/lib/*` checkers, and make it fail when one of them fails. `ops/test`'s output
   contract is `TESTS linux=N/F ios=N/F`, so an ops-checker tier needs either its own counted line or its
   own exit path - decide which, do not smuggle it into the linux count, and do not lower a floor for it.
2. Fix the two FAILs. They are `review` transitions, which is T-0032's subject; T-0032 is in queue/review/
   and its `touches:` already lists ops/lib/check-lock-lifecycle, so its reviewer is the right person to
   decide whether the checker or the code is wrong. Do not fix them from a different id without saying so.

Do NOT resolve this by deleting or weakening the checker.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from T-0087, under HARD RULE 6 (report what your change turns
  red) - which it did not, but the answer to "was it already red" turned out to be the finding.

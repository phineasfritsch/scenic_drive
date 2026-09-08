---
id: T-0068
title: queue-check's reviewer-is-not-owner gate is satisfied by owner: null
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T01:19:37Z
lease_expires_at: 2026-09-08T05:19:37Z
worktree: wt/T-0068
branch: task/T-0068
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

CLAUDE.md's rule is *"the reviewer of a task is never its owner (`ops/queue-check`)"*, and P-PROC-01 states
it. The assertion beneath it is:

    elif fm.get("reviewer") == fm.get("owner"):

Both operands are fields the same agent writes into the same file, and **nothing asserts that a task in
`review/` or `done/` has an owner at all**, so the inequality is satisfied vacuously by a null.

Demonstrated, every case executed:

    control:    owner: agent/self + reviewer: agent/self in queue/done/
                -> QUEUE CHECK FAIL - reviewer == owner (agent/self)   exit 1
    evasion 1:  change one word to `owner: null`, leave reviewer: agent/self
                -> QUEUE OK (1 tasks)                                   exit 0
    evasion 2:  delete the `owner:` line entirely
                -> QUEUE OK (1 tasks)                                   exit 0

In both evasions P-PROC-01 is green while the worker graded its own work.

**This is not an exotic hand edit.** `cmd_sweep` writes `owner=None` itself when a lease expires, so a null
owner is a state the tooling produces. A task swept back to ready, re-claimed, and later moved to review by
hand can reach `done/` with no owner and no complaint.

- A task in `review/` or `done/` must HAVE an owner and a reviewer, and they must differ. Two of those three
  conditions are currently unenforced.
- Check the same shape on the other side: does anything assert the reviewer is not null? The existing code
  has `if not fm.get("reviewer")` - confirm that arm is reachable and demonstrated.
- `ops/review` (added by T-0032) refuses `reviewer == owner` at the transition. Give it the same null
  treatment, or the refusal is evadable the same way.
- Demonstrate all three states red then green.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the self-referential-check sweep.
- 2026-09-08T01:19:37Z claimed by agent/claude-opus-5; lease until 2026-09-08T05:19:37Z
- 2026-09-08 agent/claude-opus-5 — fixed in `ops/lib/queue.py` (`cmd_check` and `cmd_review`).

  Harness: `.artifacts/T-0068/demo.sh` (gitignored, not committed). It writes a `T-9001` fixture into the
  real `queue/done/` or `queue/claimed/`, runs `bash ops/queue-check` / `bash ops/review T-9001 --reviewer X`,
  reports whether the file moved, and deletes the fixture. The SAME script produced both transcripts below.
  Case E (owner=agent/a, reviewer=agent/b) is the no-regression control: it must stay green in both runs.
  Case D is the `if not fm.get("reviewer")` arm the brief asked about — it is reachable and it fires.

  RED — `bash .artifacts/T-0068/demo.sh` before the change:

      ===== ops/queue-check =====
      --- CHECK A control  owner=agent/self reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK B evasion1 owner=null      reviewer=agent/self
      QUEUE OK (62 tasks)
      exit=0
      --- CHECK C evasion2 owner line ABSENT reviewer=agent/self
      QUEUE OK (62 tasks)
      exit=0
      --- CHECK D missing-reviewer owner=agent/self reviewer=null
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without a reviewer
      exit=1
      --- CHECK E legit    owner=agent/a    reviewer=agent/b
      QUEUE OK (62 tasks)
      exit=0

      ===== ops/review =====
      --- REVIEW A control  owner=agent/self --reviewer agent/self
      reviewer agent/self is also the owner of T-9001 - a worker may not grade its own work
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW B evasion1 owner=null      --reviewer agent/self
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/self  released=[none]
      (now: git add queue/ && git commit && git push)
      exit=0
      file moved to: queue/review/T-9001-fixture.md
      --- REVIEW C evasion2 owner line ABSENT --reviewer agent/self
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/self  released=[none]
      (now: git add queue/ && git commit && git push)
      exit=0
      file moved to: queue/review/T-9001-fixture.md
      --- REVIEW E legit    owner=agent/a    --reviewer agent/b
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/b  released=[none]
      (now: git add queue/ && git commit && git push)
      exit=0
      file moved to: queue/review/T-9001-fixture.md

  GREEN — `bash .artifacts/T-0068/demo.sh` after the change, same script, same fixtures:

      ===== ops/queue-check =====
      --- CHECK A control  owner=agent/self reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: reviewer == owner (agent/self) - a worker may not grade its own work
      exit=1
      --- CHECK B evasion1 owner=null      reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without an owner
      exit=1
      --- CHECK C evasion2 owner line ABSENT reviewer=agent/self
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without an owner
      exit=1
      --- CHECK D missing-reviewer owner=agent/self reviewer=null
      QUEUE CHECK FAIL
       - queue/done/T-9001-fixture.md: in done/ without a reviewer
      exit=1
      --- CHECK E legit    owner=agent/a    reviewer=agent/b
      QUEUE OK (62 tasks)
      exit=0

      ===== ops/review =====
      --- REVIEW A control  owner=agent/self --reviewer agent/self
      reviewer agent/self is also the owner of T-9001 - a worker may not grade its own work
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW B evasion1 owner=null      --reviewer agent/self
      T-9001 has no owner, so 'the reviewer is not the owner' cannot be decided - a null owner
      satisfies that inequality for every reviewer. Restore owner: before handing it over
      (ops/queue-sweep clears owner: when a lease expires; re-claim with ops/claim).
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW C evasion2 owner line ABSENT --reviewer agent/self
      T-9001 has no owner, so 'the reviewer is not the owner' cannot be decided - a null owner
      satisfies that inequality for every reviewer. Restore owner: before handing it over
      (ops/queue-sweep clears owner: when a lease expires; re-claim with ops/claim).
      exit=1
      file did NOT move (still claimed/)
      --- REVIEW E legit    owner=agent/a    --reviewer agent/b
      T-9001 -> queue/review/T-9001-fixture.md  reviewer=agent/b  released=[none]
      (now: git add queue/ && git commit && git push)
      exit=0
      file moved to: queue/review/T-9001-fixture.md

  Repo gates in wt/T-0068 after the change:

      $ bash ops/queue-check
      QUEUE OK (61 tasks)
      exit=0
      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      exit=0
      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0

  Every real task in `review/` and `done/` on this branch already carries both an owner and a reviewer
  (16 files checked), so the new assertion does not turn P-PROC-01 red on existing state.

  `bash ops/test` fails here, before and after the change, with `FAIL: services/api exists but vitest
  produced no report` — `services/api/node_modules` does not exist in this worktree. Verified pre-existing
  by restoring HEAD's `ops/lib/queue.py` and re-running: identical last line, exit 1. That is T-0040,
  already filed and claimed; not caused by and not touched by this task.

  `ops/lib/queue.py` grew 498 -> 515 lines. It was already over the 300-line cap on the base branch;
  T-0059 owns that split and this task did not do it.

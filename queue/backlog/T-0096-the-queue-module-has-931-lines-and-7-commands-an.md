---
id: T-0096
title: the queue module has 931 lines and 7 commands and no test invokes it once
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/test, services/etl/pyproject.toml, tests/queue/, pins/PINS.yaml]
pins_affected: [P-PROC-02]
reviewer: null
depends_on: [T-0071]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**Every process guarantee this repository has is enforced by one Python file that nothing tests.** Found by
the reviewer of PR #51 as a [low] — *"nothing automated covers `cmd_sweep`, so the new guard is protected
only by prose in a task file"*. It is not one command. It is the whole module.

Measured on `origin/task/T-0087` (the longest version currently in flight):

    lines:            931          def cmd_:            7
    problems.append:   19          REFUSED/refuse prints: 6
    non-zero returns:  25

    $ grep -in 'queue' ops/test          # on origin/main AND on origin/task/T-0071
    (nothing — ops/test never invokes ops/lib/queue.py)

    $ grep -rln 'lib.queue' --include=*.py .
    (only throwaway patch scripts under .artifacts/)

`ops/test`'s pytest tier is `cd services/etl && pytest`. It cannot see `ops/lib/` at all, so the module that
decides what a claim is, what a duplicate is, what an expired lease means and what `done/` requires has a
test count of zero — while `ops/test` prints `TESTS linux=N/F` and exits 0.

**This is not theoretical; it cost real work twice this session, in this file.**

- **PR #50.** The duplicate-brief guard hashed the body of every task, and `ops/new-task` writes an
  identical placeholder body into every task it creates — so any two freshly created tasks were a duplicate
  pair. `QUEUE OK (61 tasks)` became `QUEUE CHECK FAIL` naming three unrelated tasks, and three real pushed
  branches went from exit 0 to exit 1. One test — *two tasks straight out of `cmd_new` are not duplicates* —
  would have caught it before the push.
- **PR #51.** The sweep guard keyed on "does the branch exist". `ops/claim` writes `branch: task/<id>` for
  every task and `queue/README.md` step 4 creates that branch *before any work happens*, so the guard was
  true for every task ever claimed and the sweeper stopped sweeping anything. One test — *a task claimed,
  its branch created at main's tip, its lease expired, is swept* — would have caught it.

Both were caught by a human reading the code afterwards. That is the process this repository exists to
replace: *"Agents report success on broken work."*

Do:

1. A `tests/queue/` pytest package at the repo root, and a **fourth tier in `ops/test`** that runs it and is
   counted in the printed totals. It must obey the tier rule [[T-0071]] established: **a tier with a
   positive floor that did not run is a failure**, never a silent skip. Add `pins/floor_linux_queue.txt`.
2. Tests are FIXTURE-BASED: build a throwaway `queue/` tree in `tmp_path`, point the module at it, and
   assert exit codes and emitted text. Do not test against the live `queue/` — a test whose expected value
   comes from the tree it inspects is this repository's signature defect, and `MIN_TASKS` already makes the
   live tree an input.
3. Cover, at minimum, one negative case per refusal — the 6 `REFUSED` paths and the 19 `problems.append`
   rules. Each test must be **demonstrated red** by reverting the guard it covers, then green.
4. Pin the tier as **P-PROC-02** (`runs_on: [linux]`), anchored on the floor file and the printed tier
   count, **not** on a comment.
5. Vacuity guard, because this check is about vacuity: assert the suite itself has a floor of cases, so an
   empty or import-failing `tests/queue/` cannot read as "the queue module is fine".

**Ordering.** Stacks on [[T-0071]], which rewrote `ops/test` into per-tier floors and is unmerged; adding a
tier before it lands means writing the tier twice. `ops/lib/queue.py` is also exempt from the 300-line cap
under **T-0059**, which will split it — write the tests against the commands' behaviour, not against line
numbers or internal helper names, or the split will invalidate them.

## Log

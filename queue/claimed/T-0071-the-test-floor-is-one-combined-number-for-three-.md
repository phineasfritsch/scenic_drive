---
id: T-0071
title: the test floor is one combined number for three tiers, so a whole suite can vanish under it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:23:27Z
lease_expires_at: 2026-09-08T08:23:27Z
worktree: wt/T-0071
branch: task/T-0071
exclusive: [floors]
touches: [ops/test, .githooks/commit-msg, pins/PINS.yaml, pins/floor_linux.txt, pins/floor_linux_swift.txt, pins/floor_linux_ts.txt, pins/floor_linux_py.txt]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/test` counts Swift, vitest and pytest into **one** total and compares it to **one** floor:

    ops/test:69   floor_linux="$(tr -d '[:space:]' < pins/floor_linux.txt)"
    ops/test:73   echo "TESTS linux=$linux_total/$floor_linux ..."
    ops/test:75   [[ $linux_total -lt $floor_linux ]] && { echo "FAIL: linux test count $linux_total is below
                    floor $floor_linux - tests were deleted or a reporter broke"; rc=1; }

Measured, on this repo today:

    pins/floor_linux.txt on main              50
    pins/floor_linux.txt on task/T-0025       76
    pins/floor_linux.txt on task/T-0069       76

and the T-0069 run reports **227** tests passing against that floor of 76 - **151 of slack**. Confirm that
number when claiming this rather than trusting it; it is quoted from the T-0069 fix agent's report, whereas
the three floor values and the three lines above were read directly.

**Two separate defects, and the second is the one that matters.**

1. *Slack.* A floor 151 below the actual count does not detect deletion; it detects catastrophe. The whole
   point of a ratchet is that it sits just under the current value. Nothing ratcheted these up as the suites
   grew.

2. *Aggregation.* One number cannot see a tier disappear. If the entire ETL pytest suite were deleted, the
   Swift and vitest tiers alone would still have to fall below 76 before anything went red. The floor's own
   failure message says *"tests were deleted"*, which is precisely the event it cannot localise. `ops/test`
   already fails when an expected report FILE is missing - that is the guard that currently does this job -
   but a report file that exists and contains few or zero tests is a different state, and the floor is what
   is supposed to catch it. **Execute both: delete a whole tier's tests and see what the tool says, and empty
   one report file and see what it says.** Do not reason about it.

This is the same shape as [[T-0066]], [[T-0070]] and the `check-exec-bits` / `check-line-cap` fixes: a check
that cannot distinguish "the thing I measure is healthy" from "there is nothing to measure". Here it is one
level up - the floor is not derived from the data, which is right, but it is too coarse to bind it.

- Split the floor per tier: `floor_linux_swift`, `floor_linux_ts`, `floor_linux_py`, or one file with three
  named values. `pins/floor_ios.txt` stays as it is.
- Ratchet each to just under its current count, and say in the log what each count was when set.
- Keep `.githooks/commit-msg`'s `floor-lower:` refusal working across the new shape - check it still fires,
  because a rename is exactly the kind of edit that silently disables a grep-based hook.
- The ETL suite has no floor of its own at all today. That is the concrete hole: `tests/test_oracle_build.py`
  (added by T-0069) can be deleted and nothing goes red.
- `pins/floor_linux.txt` is a **serial-only** file per CLAUDE.md. Declare `exclusive:` before touching it.
- Demonstrate red then green for each tier separately.

**Also worth recording, found in the same pass and not the same defect:** the pinned `scenic-etl` image ships
no `git`, so `tests/test_manifest.py:47` SKIPS there and passes on the host. The image reports
`170 passed, 1 skipped` where the host reports `171 passed`. Host and image totals will never match, so a
report that compares them naively will read as a regression. Either install git in the image or make the
test's skip explicit in the expected counts.

## Log
- 2026-09-08 filed by agent/claude-opus-5. The floor values and the three `ops/test` lines were read
  directly; the 227 count comes from the T-0069 fix run and must be re-measured by whoever claims this.
- 2026-09-08T02:23:27Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:23:27Z

- 2026-09-08 agent/claude-opus-5 — one floor per tier, and a floor now proves its tier still runs.

  **First, a correction to this brief's own numbers.** It quoted 227 tests against a floor of 76 and called
  that 151 of slack. On `main` the floor is tight, not slack — CI's own run says so:

        core  ops/test  TESTS linux=50/50 ios=skipped failed=0 skipped=0

  The slack is real but branch-specific: the ETL chain added ~150 tests and the floor only moved 50 -> 76.
  So the *slack* is a property of those branches; the *aggregation* defect is everywhere, and it is the one
  that matters.

  **Measured per tier**, which the tool could not previously report at all:

        TESTS linux=50/50 (swift=16/16 ts=34/34 py=-/0) ios=skipped failed=0 skipped=0

  `pins/floor_linux.txt` (50) is replaced by `floor_linux_swift.txt` (16), `floor_linux_ts.txt` (34) and
  `floor_linux_py.txt` (0). They sum to 50, so nothing was lowered — but note that the commit-msg hook cannot
  see that, because it compares files one at a time and the old file is a deletion. Said here rather than
  hidden behind a `floor-lower:` line that would have claimed a reduction that did not happen.

  `py` is 0 because the ETL tier does not exist on `main`. **Whoever merges the ETL chain must set it**, or
  the hole this task is about survives for the suite that has the most tests. Recorded in `queue/MERGE-ORDER.md`.

  **RED, on a tree with slack** — `task/T-0062`, which carries the ETL tier (46 pytest tests) and inherits
  floor 76, so 96 actual against 76 is 20 of headroom. Delete one real test file, 18 tests, and run the
  UNMODIFIED `ops/test`:

        baseline   TESTS linux=96/76 ios=skipped failed=0 skipped=0        OK
        after rm services/etl/tests/test_manifest.py
                   TESTS linux=78/76 ios=skipped failed=0 skipped=0        OK      exit 0

  Eighteen real tests deleted; the combined floor absorbed it and the run reported success.

  **GREEN, identical deletion, per-tier floors:**

        TESTS linux=78/96 (swift=16/16 ts=34/34 py=28/46) ios=skipped failed=0 skipped=0
        FAIL: py test count 28 is below its floor 46 - tests were deleted or a reporter broke     exit 1

        control, file restored:
        TESTS linux=96/96 (swift=16/16 ts=34/34 py=46/46) ios=skipped failed=0 skipped=0    OK   exit 0

  **The second half, which is the more important one.** Every tier is gated on a manifest — `if [[ -f
  services/api/package.json ]]`, `if [[ -f services/etl/pyproject.toml ]]` — so deleting the manifest skipped
  the whole tier and the survivors only had to clear the combined floor. Three numbers alone would not fix
  that: a tier that does not run has no count to compare. So **a positive floor is itself the claim that the
  tier existed when a reviewer set it**, and a tier with a positive floor that did not run is a failure:

        rm services/etl/pyproject.toml
        TESTS linux=50/96 (swift=16/16 ts=34/34 py=-/46) ios=skipped failed=0 skipped=0
        FAIL: the py tier did not run, but its floor is 46 - a floor above zero says this tier
              existed when it was set. Deleting the manifest that gates a tier must not silence it.   exit 1

  `_ran` is set where the tier produces a report, never inferred from the count: a tier that ran and found
  nothing is a different fact from one that did not run, and only the second may skip its floor.

  `read_floor` also refuses a non-integer floor rather than reading it as 0 — that would be this exact
  failure mode appearing inside the file that defines it.

  **A REAL BUG FOUND WHILE DEMONSTRATING, not fixed here, filed separately.** `ops/test` resolves
  `PY="${PYTHON:-$(command -v python3 || command -v python)}"`. On this box `python3` is Python **3.14.5**
  (`AppData\Local\Python\pythoncore-3.14-64`) with **no pytest installed**, while `python` is 3.10.11 and has
  it. The ETL tier therefore produced no report and `ops/test` exited 1 with

        FAIL: services/etl exists but pytest produced no report

  which blames `services/etl`. It is an interpreter-selection bug, and the message points at the wrong thing.
  Every demonstration above was re-run with `PYTHON=$(command -v python)`, the documented override.

  **The hook.** `.githooks/commit-msg` listed the two filenames literally, so the rename would have disabled
  it silently — exactly the failure this repo keeps finding in its own checks. It now iterates every staged
  `pins/floor_*.txt` (`--diff-filter=d`, so deleting the old aggregate is not read as lowering it to zero).
  A first attempt to demonstrate it was INVALID and is recorded because it was nearly believed: lowering
  `floor_linux_swift.txt` before that file existed in `HEAD` gives `old=0`, and `10 < 0` is false, so the
  commit went through and looked like the hook was dead. It was not; there was nothing to lower from. The
  real demonstration must come after these floors are committed, and is the next entry.

  Gates on this branch: `PINS ok=9 skipped=0 pending=3 expired=0 failed=0`, `QUEUE OK (70 tasks)`,
  `TESTS linux=50/50 (swift=16/16 ts=34/34 py=-/0)  OK`.

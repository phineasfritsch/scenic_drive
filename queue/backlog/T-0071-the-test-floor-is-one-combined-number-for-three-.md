---
id: T-0071
title: the test floor is one combined number for three tiers, so a whole suite can vanish under it
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

---
id: T-0071
title: the test floor is one combined number for three tiers, so a whole suite can vanish under it
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [floors]
touches: [ops/test, .githooks/commit-msg, pins/PINS.yaml, pins/floor_linux.txt, pins/floor_linux_swift.txt, pins/floor_linux_ts.txt, pins/floor_linux_py.txt]
pins_affected: []
reviewer: null
depends_on: [T-0229]
verify: [ops/test, ops/check-pins]
acceptance:
  - "pins/floor_linux.txt raised from 76 to a ratchet number RULED in the Log from the measured linux=1647 on main (T-0203 Log :34), never the max; RED first: delete one Swift test file in a throwaway tree, `bash ops/test` exits 1 below the floor by its count line, quoted"
  - "per-tier floors (swift / ts / py) as PR #47 shaped them, each demonstrated red the same way; a tier that reports 0 tests is a FAIL, never an exemption (PR #47 commit 704e0f7's rule)"
  - "pins/floor_ios.txt stays 0 and the reason is ruled in the Log and in P-TEST-01's statement, never in the floor file (ops/test:110 reads it as a bare number)"
  - "every swift build/test in ops/test and in the pins this PR touches passes its own --scratch-path (T-0229 rides this PINS.yaml edit or lands first - same serial file)"
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
- 2026-09-19T21:53:35Z by agent/claude-fable-5-1 (14:13 panel, fable-grounded on pins/floor_*.txt, T-0203 Log :34, queue.py:541-548, RouteScore.swift:92-94): PR #47 closed (812 commits behind main, conflicting on ops/test, pins/PINS.yaml and pins/floor_linux.txt; its per-tier numbers swift 16 / ts 34 / py 0 are stale against linux=1647); queue/LOCKS/floors.lock (held since 2026-09-08) released by this commit; back to ready/ with owner null. M3's clause 1 (plan:284 'ops/test >=250 (floor set)') is EARNED BUT UNBANKED on a 76 floor - 1,571 linux tests and the whole iOS tier can vanish green. Re-claim from main and re-measure; next START ahead of T-0226/T-0228/T-0222.

---
id: T-0011
title: ScenicKit Solar: NOAA sunrise/sunset/civil twilight/golden hour, 20 NOAA-checked fixtures (P-SAFE-05)
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T04:21:42Z
lease_expires_at: 2026-09-07T08:21:42Z
worktree: ../wt/T-0011
branch: task/T-0011
exclusive: [floors]
touches: [Sources/ScenicKit/Solar/, Sources/ScenicKit/Model/, Tests/ScenicKitTests/, Tests/Fixtures/solar/, pins/PINS.yaml, pins/floor_linux.txt]
pins_affected: [P-SAFE-05]
reviewer: agent/reviewer-2
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
- 2026-09-07T05:10:00Z backlog -> ready: no dependencies; M3 work that is independent of the data pipeline. pins/PINS.yaml added to touches to make P-SAFE-05 real.
- 2026-09-07T04:21:42Z claimed by agent/claude-opus-5; lease until 2026-09-07T08:21:42Z
- 2026-09-07T06:00:00Z ORACLE REJECTED AND REPLACED. First fixtures came from sunrise-sunset.org; our values disagreed with it by 60-620 s on rise/set while civil twilight matched to 2-4 s - the signature of a zenith mismatch, not a bug. Cross-checked three sites against the US Naval Observatory: OUR values match USNO within 5-34 s (SF rise +5 s, Fairbanks rise +24 s, Key West set -13 s) while sunrise-sunset.org was off by 84-343 s. The oracle was wrong, not the code. Refetched all fixtures from USNO (35 site-days, 21N-65N, 138 instants) and kept the rejection in the fetcher docstring + oracle.json as the evidence trail.
- 2026-09-07T06:00:00Z GREEN: swift test -> 16 tests in 3 suites passed; worst error 33 s at fairbanks 2026-12-21 dusk against a 90 s tolerance (USNO rounds to the minute, +/-30 s; our model ~35 s). ops/test -> TESTS linux=50/3 ios=skipped failed=0. ops/check-pins -> PINS ok=8 pending=3 failed=0.
- 2026-09-07T06:00:00Z RED 1 (the math): horizonZenith 90.833 -> 90.0, a plausible 'simplification' -> sunset fixtures fail, worst error 1548 s; restored, green again.
- 2026-09-07T06:00:00Z RED 2 (the oracle): rewrote oracle.json's provenance to 'my own code, trust me' -> P-SAFE-05 fails (PINS ok=7 failed=1). The pin asserts the fixtures come from USNO, not just that the numbers match, so regenerating fixtures from our own output cannot make it green.
- 2026-09-07T06:00:00Z polar cases assert nil, never a fabricated time: Utqiagvik midnight sun and polar night return nil sunrise/sunset (and nil civil dusk under the midnight sun).
- 2026-09-07T06:00:00Z P-SAFE-05 is no longer pending: assertion checks USNO provenance + >=20 fixtures + the fixture suite passing.
- 2026-09-07T06:00:00Z floor_linux raised 3 -> 50 (3 geo + 13 solar + 34 worker). Raising a floor is the reviewer's ratchet; verify the number before merging.
- 2026-09-07T06:00:00Z moved to review/, reviewer agent/reviewer-2
- 2026-09-07T06:05:00Z SELF-REPORTED PROCESS SLIP: I added `exclusive: [floors]` to this task to cover the floor_linux raise but never created queue/LOCKS/floors.lock while it was in claimed/. ops/queue-check caught it (and P-PROC-01 went red with it) for the minutes between the edit and the move to review/; it is green now only because the exclusive check applies to claimed/ tasks. The check worked; the operator did not. Nothing else held that lock, so no write was actually lost. Reviewer: treat this as evidence the lock discipline needs to be part of ops/claim rather than a thing a human remembers - filed as T-0017.

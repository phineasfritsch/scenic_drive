---
id: T-0383
title: Bind T-0366's handoff-marker privacy test (HandoffMarkingMomentsTests.defaultsDomainIsOneInt) to P-PRIV-05 by name
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T21:15:14Z
lease_expires_at: 2026-10-17T21:15:14Z
worktree: .worktrees/T-0383
branch: task/T-0383
exclusive: []
touches: [pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0366, T-0377]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0366 (PR #271) keeps a handoff marker on the device: one Int under postDrive.handoffOpensLeft, no place, no
time, no route, never sent. Its privacy property is held by ScenicKitTests.HandoffMarkingMomentsTests
defaultsDomainIsOneInt(), which already runs inside P-PRIV-05's swift filter - so deleting it is green today.
T-0366's Log records the binding as NOT DONE.

Bind it by name in P-PRIV-05's named-tests.json entry (widen the swift filter only if the suite is outside it),
re-approve the check-named-table.py digest and count (77 -> 78 unless measured otherwise) in the same diff, and
append one dated T-0383 sentence to why_no_test_catches_it (do not edit earlier dated text). Demonstrate RED with
the test deleted (MISSING by name under the new table; the guard refuses the table edit without re-approval), then
green. PINS.yaml stays strict (check-pins-yaml.py).

## Acceptance
1. `ops/lib/named-tests.json` P-PRIV-05 `swift.filter` changes exactly `ScenicKitTests\\.LearnedSpeedsPrivacyTests`
   -> `ScenicKitTests\\.(LearnedSpeedsPrivacyTests|HandoffMarkingMomentsTests)` (ruling R1) and `swift.tests` gains
   exactly one row, `ScenicKitTests.HandoffMarkingMomentsTests/defaultsDomainIsOneInt()`, appended last; no other
   entry and no other row changes (the other nine entries' canonical JSON equal origin/main's).
2. pins/PINS.yaml P-PRIV-05 `assertion` differs from origin/main's only in the two `check-named-table.py` calls'
   sha256 and count: `ad5e5df4...054e 77` -> `<sha256 of the edited entry> 78` (38 vitest, 40 Swift).
   `python ops/lib/check-named-table.py P-PRIV-05 <new sha> 78` exits 0 and its `--prove-red` prints
   `PROVE-RED OK`.
3. RED, guard: the edited table under the OLD approval (`... ad5e5df4...054e 77`) exits 1 naming P-PRIV-05 with
   the count (78 != 77) and digest refusals.
4. RED, by name: with `defaultsDomainIsOneInt()` deleted from HandoffMarkingMomentsTests.swift (not committed),
   `run-named-tests.py P-PRIV-05` under the OLD table prints passed=76/77 (only the GRDB-gated UserStorePrivacyTests
   MISSING - the deletion unseen) and under the NEW table passed=76/78 exit 1 with
   `ScenicKitTests.HandoffMarkingMomentsTests/defaultsDomainIsOneInt()` MISSING by name.
5. GREEN: the test file restored (sha256 equal to the committed blob), the SHIPPED P-PRIV-05 assertion string
   (read from PINS.yaml by yaml.safe_load, run by `bash -c`) prints `NAMED-TABLE P-PRIV-05 ok - 78 distinct names`
   and `NAMED P-PRIV-05 passed=77/78`, the only non-pass the Windows box's UserStorePrivacyTests MISSING (ruling R3);
   CI's Linux core job runs it whole.
6. P-PRIV-05 `why_no_test_catches_it` gains one appended dated T-0383 sentence; no earlier text, no other field or
   pin changes. Bare gates on the merged head exit 0: `python ops/lib/check-pins-yaml.py`, `bash ops/check-pins
   --source-only`, `bash ops/lib/check-exec-bits`, `bash ops/lib/check-line-cap`, `bash ops/queue-check`.

## Log
- 2026-10-16 filed by agent/claude-opus-5 from T-0366 stillOpen (P-PRIV-05 binding not done).
- 2026-10-16T21:15:14Z claimed by agent/claude-opus-5; lease until 2026-10-17T21:15:14Z
- 2026-10-16T21:17:01Z MEASURED at 14e1aab2 (worktree = main): `python ops/lib/check-named-table.py P-PRIV-05
  ad5e5df41882a3237e8bb92d5396c6964de956ba18b0f7b666e4fe0c134b054e 77` -> `NAMED-TABLE P-PRIV-05 ok - 77 distinct
  names, sha256 ad5e5df41882` exit 0; the entry holds 38 vitest and 39 Swift names. The swift filter's ScenicKit
  alternative is `ScenicKitTests\\.LearnedSpeedsPrivacyTests` only; `re.search(filter, name)` is False for both
  `ScenicKitTests.HandoffMarkingMomentsTests/defaultsDomainIsOneInt()` and `.../everyMomentTable()`. The target is
  Tests/ScenicKitTests/PostDrive/HandoffMarkingMomentsTests.swift line 38 `func defaultsDomainIsOneInt()`.
- RULINGS (before code):
  - R1 Brief vs code: the Brief says the test "already runs inside P-PRIV-05's swift filter". Measured false - the
    suite is outside the filter, so the pin never runs it. Ruled by the Brief's own conditional: widen the ScenicKit
    alternative to `ScenicKitTests\\.(LearnedSpeedsPrivacyTests|HandoffMarkingMomentsTests)`. everyMomentTable()
    then runs under the filter too but is not bound (it is a behaviour table, not the privacy property); only
    defaultsDomainIsOneInt() is bound, as the Brief names. "Deleting it is green today" stays true, for the
    stronger reason that it is not run at all.
  - R2 count: 77 -> 78 (38 vitest, 39 -> 40 Swift), matching the Brief's expectation.
  - R3 the pin runs_on [linux]; on this Windows box PlaceStoreTests.UserStorePrivacyTests is MISSING by design
    (GRDB, T-0175 R2), so the green line here is passed=77/78 and that is the only expected miss; no exact
    passed=N/N check is added (T-0377 R2 stands).
  - R4 in flight: T-0381 edits PINS.yaml P-PROD-01, a different pin; merge from main is a union.
- 2026-10-16T21:31:00Z RED (A3, A4). With `defaultsDomainIsOneInt()` deleted (lines 35-53 of
  HandoffMarkingMomentsTests.swift, never committed), `SCENIC_SWIFT_SCRATCH=.build/t-0383 python
  ops/lib/run-named-tests.py P-PRIV-05` under the OLD 77-name table: `RED PlaceStoreTests.UserStorePrivacyTests/
  noColumnNamesAPlaceOrATrail(): MISSING` only, `NAMED P-PRIV-05 passed=76/77`, exit 1 - the deletion unseen. Table
  edited (A1), old approval: `check-named-table.py P-PRIV-05 ad5e5df4...054e 77` -> `REFUSED count 78 distinct names
  != approved 77`, `REFUSED digest 75358a5090a01ec914c1ec784f3c26c330f63c5c351787aca42a5e9aefcbfe6e != approved
  ad5e5df4...`, `NAMED-TABLE P-PRIV-05 FAILED`, exit 1 (38 vitest, 40 Swift; the new filter re.search-matches the
  bound name). NEW table, test still deleted: `RED ...UserStorePrivacyTests/noColumnNamesAPlaceOrATrail(): MISSING`,
  `RED ScenicKitTests.HandoffMarkingMomentsTests/defaultsDomainIsOneInt(): MISSING - no test of this name ran`,
  `NAMED P-PRIV-05 passed=76/78`, exit 1.
- 2026-10-16T21:31:46Z GREEN (A2, A5). Test file restored by `git checkout`: sha256 3fcb06a0...87a5e2, blob
  9069a893 = HEAD's. PINS.yaml edited by .build/t0383_pin_edit.py (each old call asserted exactly once; one tail
  asserted once): both calls now `75358a5090a01ec914c1ec784f3c26c330f63c5c351787aca42a5e9aefcbfe6e 78`, one
  sentence appended; `python ops/lib/check-pins-yaml.py` -> `PINS-YAML ok pins=52 fields=418`. The SHIPPED assertion
  (yaml.safe_load, `bash -c`): `NAMED-TABLE P-PRIV-05 ok - 78 distinct names, sha256 75358a5090a0`, then
  `NAMED P-PRIV-05 passed=77/78` with the only RED the GRDB-gated UserStorePrivacyTests MISSING (R3; exit 1 here
  for that reason alone, as T-0377 recorded). `--prove-red ... 78` -> `PROVE-RED OK: 8 of 8 rows red by name,
  controls green`.

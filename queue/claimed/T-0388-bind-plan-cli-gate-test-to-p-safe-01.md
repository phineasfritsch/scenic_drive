---
id: T-0388
title: Bind T-0385's PlanCLIGateValuesTests to P-SAFE-01 by name, and give P-SAFE-01 a check-named-table digest
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T04:46:37Z
lease_expires_at: 2026-10-18T04:46:37Z
worktree: .worktrees/T-0388
branch: task/T-0388
exclusive: []
touches: [pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-SAFE-01]
reviewer: null
depends_on: [T-0385, T-0382]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

P-SAFE-01's named-tests entry binds the Worker's refusal tests (T-0382: 26 names) but not the CLI body gate's ScenicPlanCLITests.PlanCLIGateValuesTests (T-0385), and P-SAFE-01 carries no check-named-table.py digest, so a test deleted together with its row is green. Bind the CLI suite by name (widen the swift filter only if needed), add check-named-table.py P-SAFE-01 <sha> <count> and its --prove-red before the run-named-tests call (the P-STORE-02/P-PRIV-05 shape), append one dated sentence to why_no_test_catches_it, and show RED (row dropped / test deleted) then green.

## Acceptance
1. `ops/lib/named-tests.json` P-SAFE-01 gains exactly one key, `swift`, = `{"filter":
   "ScenicPlanCLITests\\.PlanCLIGateValuesTests", "tests": [the suite's three @Test functions as
   `ScenicPlanCLITests.PlanCLIGateValuesTests/<function>()`]}` (rulings R1, R2); its `vitest` half and the other
   fourteen entries' canonical JSON equal origin/main's.
2. pins/PINS.yaml P-SAFE-01 `assertion` is `<py> ops/lib/check-named-table.py P-SAFE-01 <sha> 29 && <py>
   ops/lib/check-named-table.py --prove-red P-SAFE-01 <sha> 29 >/dev/null && ` followed by origin/main's whole
   assertion unchanged (26 vitest + 3 Swift = 29). `python ops/lib/check-named-table.py P-SAFE-01 <sha> 29` exits 0
   and its `--prove-red` prints `PROVE-RED OK`.
3. RED, guard: (a) the edited table under the pre-change entry's own digest and count (`34a189dd...d229 26`,
   measured below) exits 1 naming P-SAFE-01 with the count (29 != 26) and digest refusals; (b) the edited table with
   one CLI row dropped (in memory, never written) under the NEW approval is refused with count 28 != 29 and digest.
4. RED, by name: with `sendRefusesExactlyTheGateValues()` deleted from PlanCLIGateValuesTests.swift (never
   committed), `run-named-tests.py P-SAFE-01` under the OLD table prints passed=26/26 exit 0 (the deletion unseen)
   and under the NEW table passed=28/29 exit 1 with
   `ScenicPlanCLITests.PlanCLIGateValuesTests/sendRefusesExactlyTheGateValues()` MISSING by name.
5. GREEN: the test file restored (blob equal to HEAD's), the SHIPPED P-SAFE-01 assertion string (read from
   PINS.yaml by yaml.safe_load, run by `bash -c`) prints `NAMED-TABLE P-SAFE-01 ok - 29 distinct names` and
   `NAMED P-SAFE-01 passed=29/29`, exit 0.
6. P-SAFE-01 `why_no_test_catches_it` gains one appended dated T-0388 sentence; no earlier text, no other field or
   pin changes. Bare gates on the merged head exit 0: `python ops/lib/check-pins-yaml.py`, `bash
   ops/lib/check-exec-bits`, `bash ops/queue-check`, `bash ops/lib/check-safety-disclaimer`.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0385 stillOpen 1.
- 2026-10-17T04:46:37Z claimed by agent/claude-opus-5; lease until 2026-10-18T04:46:37Z
- 2026-10-17T04:49:20Z MEASURED at 1272ec4d (worktree = main). ops/lib/named-tests.json has fifteen entries;
  P-SAFE-01's has ONE key, `vitest` (26 names in 6 files) - no `swift` key, so no filter to widen. Its canonical
  sha256 is 34a189dd62260ccc98afa5c8148eb48b61885287e668e227ffe3a6b20879d229. No entry's swift filter
  re.search-matches `ScenicPlanCLITests.PlanCLIGateValuesTests/sendRefusesExactlyTheGateValues()`: the CLI suite is
  run by no pin. PINS.yaml P-SAFE-01 `assertion` is the bare run-named-tests call, no check-named-table digest.
  Tests/ScenicPlanCLITests/PlanCLIGateValuesTests.swift (231 lines) has three @Test functions:
  theGateListIsTheShippedProfilesGateValues() (line 180), theCorpusCoversEveryFamilyForEveryName() (190),
  sendRefusesExactlyTheGateValues() (212). No other ops/ or pins/ file names check-named-table besides PINS.yaml
  and the script itself: no meta-guard enumerates digest-carrying pins.
- RULINGS (before code):
  - R1 Brief vs code: "widen the swift filter only if needed". Measured: there is no swift filter on P-SAFE-01 to
    widen. Ruled: add one, `ScenicPlanCLITests\\.PlanCLIGateValuesTests` - the narrowest filter that runs the suite
    (the P-PRIV-05 alternation shape, one alternative). Without it the runner never builds or runs the suite.
  - R2 which names: all three @Test functions. Each is the P-SAFE-01 body gate: the constant bound to the shipped
    car_scenic_base.json, the generated corpus covering every derived name, and send - the shipping entry point of
    ops/plan's GraphHopperRouteSource - refusing exactly the gate values. Count 26 -> 29 (26 vitest, 3 Swift).
  - R3 spelling: `Module.Suite/function()`, the identifier run-named-tests reads from swift test's xunit report,
    never the display string; checked against the warm-up run's report before the table is written.
  - R4 shape: check-named-table, then `--prove-red ... >/dev/null`, then the unchanged run-named-tests call - the
    P-PRIV-05 / P-STORE-02 order, so a dropped row is refused before any test runs.
  - R5 runs_on stays [linux]. CI's core job (swift:6.1 image) already runs P-PRIV-05's swift half under the same
    runner, so the new half runs there; here swift 6.3.3 with SCENIC_SWIFT_SCRATCH=.build/t-0388.
  - R6 Brief "show RED (row dropped / test deleted)": both, as acceptance 3(b) and 4. Today a deleted CLI test is
    green under P-SAFE-01 for the stronger reason that nothing runs it (4, old table).
  - R7 in flight: T-0386 (services/routing tests) and T-0387 (ops/mutate/profilegate.py) touch neither file here.
- 2026-10-17T04:59:44Z R3 checked: the warm-up `swift test --scratch-path .build/t-0388 --filter
  'ScenicPlanCLITests\.PlanCLIGateValuesTests'` ("Test run with 3 tests in 1 suite passed") wrote
  x-swift-testing.xml with classname `ScenicPlanCLITests.PlanCLIGateValuesTests` and names
  `theGateListIsTheShippedProfilesGateValues()`, `theCorpusCoversEveryFamilyForEveryName()`,
  `sendRefusesExactlyTheGateValues()` - the three rows as written.
  RED (A4). `sendRefusesExactlyTheGateValues()` deleted (lines 210-230 of PlanCLIGateValuesTests.swift, never
  committed). OLD table: `SCENIC_SWIFT_SCRATCH=.build/t-0388 python ops/lib/run-named-tests.py P-SAFE-01` ->
  `NAMED P-SAFE-01 passed=26/26`, exit 0 - the deletion unseen. Table edited (A1, .build/t0388_table_edit.py, one
  insertion asserted once), test still deleted: `RED ScenicPlanCLITests.PlanCLIGateValuesTests/
  sendRefusesExactlyTheGateValues(): MISSING - no test of this name ran`, `NAMED P-SAFE-01 passed=28/29`, exit 1.
  RED (A3). (a) `check-named-table.py P-SAFE-01 34a189dd...d229 26` over the edited table -> `REFUSED count 29
  distinct names != approved 26`, `REFUSED digest 42351bc565d1b7498236376316280a99df4e42a91f7c8890ef23787f51f5dba4
  != approved 34a189dd...`, `NAMED-TABLE P-SAFE-01 FAILED`, exit 1. (b) the module's own refusals() over the table
  with the send row dropped in memory, NEW approval: `count 28 distinct names != approved 29`, `digest
  bb474a070c18... != approved 42351bc565d1...`; over the live table: `[]`.
  GREEN (A2, A5). Test restored by `git checkout`: blob 9acb10a6 = HEAD's. PINS.yaml edited by
  .build/t0388_pin_edit.py (assertion and why tail each asserted once; yaml.safe_load diff asserted: only P-SAFE-01,
  only assertion + why, why a prefix-extension, assertion ending in ` && ` + the old one).
  `python ops/lib/check-pins-yaml.py` -> `PINS-YAML ok pins=52 fields=418`. `check-named-table.py P-SAFE-01
  42351bc5...dba4 29` -> `NAMED-TABLE P-SAFE-01 ok - 29 distinct names, sha256 42351bc565d1`, exit 0; `--prove-red`
  -> `PROVE-RED OK: 8 of 8 rows red by name, controls green`. The SHIPPED assertion (yaml.safe_load, `bash -c`,
  PYTHON=python): `NAMED-TABLE P-SAFE-01 ok - 29 distinct names, sha256 42351bc565d1`, `NAMED P-SAFE-01
  passed=29/29`, exit 0. A1: vs origin/main only P-SAFE-01 changed, its vitest half equal, keys [swift, vitest].
  A6: the appended sentence begins `APPENDED 2026-10-17 (T-0388): ops/plan's body gate is bound too`.

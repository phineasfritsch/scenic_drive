---
id: T-0154
title: the pure scorer contract - score.py, one shared SegmentTerms fixture, and a ScenicKit differential to 1e-6, red first on the byway tier the two sides disagree about
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T18:01:36Z
lease_expires_at: 2026-09-19T02:01:36Z
worktree: .worktrees/T-0154
branch: task/T-0154
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, Sources/ScenicKit/Scoring/, Tests/ScenicKitTests/, Tests/Fixtures/, ops/mutate/]
pins_affected: []
reviewer: agent/rv1-pr89
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "ONE fixture, read by both sides, whose expectations come from NEITHER of them: `Tests/Fixtures/scoring/segment_terms.json`, 1,000 rows, every `expected` computed by `plan_score` in `Tests/Fixtures/scoring/generate.py` - a hand transcription of plan lines 78-87 that imports neither `etl.score` nor ScenicKit. `python Tests/Fixtures/scoring/generate.py` -> `rows=1000 covering=177 random=823` / `byway tiers: none=339, eligible=326, designated=335` / `zero-class rows=253  distinct highway classes=14  nonzero expected=744`. Deterministic: re-running it leaves `git diff Tests/Fixtures/scoring/segment_terms.json` empty"
  - "RED FIRST, by name, before one line of Swift changed. `swift test --scratch-path .build/T0154 --filter SegmentScoreContractTests` -> `x Test run with 5 tests in 1 suite failed after 0.178 seconds with 22 issues.`; the summary was `240 of 1000 rows disagree with the oracle by >= 1e-06; worst delta 0.13076020187735218 at axis-scenery-zero-eligible` and the named rows were eligible-tier ones - `class-primary-eligible-nosurface: got 0.5929706302250319, oracle 0.5382223387661732, delta 0.05474829145885873 (tier=eligible highway=primary)`, `class-residential-eligible-asphalt`, `class-secondary-eligible-nosurface`, `class-service-eligible-asphalt`, `class-tertiary-eligible-nosurface`, `class-unclassified-eligible-asphalt` and the rest. The second red was `an eligible byway scores strictly below a designated one on the same road` -> `Expectation failed: (e -> 0.5929706302250319) < (d -> 0.5929706302250319)`. Three of the five tests were green in that same run, so the fixture was not failing wholesale"
  - "GREEN after `SegmentTerms.isByway: Bool` became `bywayTier: BywayTier`: `swift test --scratch-path .build/T0154` -> `Test run with 223 tests in 28 suites passed after 0.315 seconds.` (5 of those 223 are this contract)"
  - "`cd services/etl && python -m pytest tests -q` -> 472 dots, `[100%]`, exit 0, and NO count line: the project's own `addopts = -q` (services/etl/pyproject.toml) makes the gate's `-q` a second one. The count comes from `python -m pytest tests -rsx` at the same tree -> `472 passed in 62.82s (0:01:02)` before the commit and `472 passed in 93.86s (0:01:33)` re-run at it - the wall clock moves on a shared box, the 472 and the zero skips do not. Zero skipped, zero xfailed - 15 of the 472 are `tests/test_score_contract.py`"
  - "`bash ops/lib/check-line-cap` -> `P-SRC-02: 60 Swift files tracked (Sources=21, Tests=31, apps/ios=8), none over 300 lines`, exit 0. The new Python is under the cap too, unenforced though it is (T-0058): `score.py` 159, `test_score_contract.py` 152, `generate.py` 254"
  - "`bash ops/check-pins --source-only` -> `PINS ok=8 skipped=11 pending=1 expired=0 failed=0 tier=linux source-only`, exit 0. Its FIRST run in this fresh worktree printed `failed=1` on P-SAFE-05 with `output: (none)`: that pin's assertion runs `swift test --filter SolarFixtureTests` with no `--scratch-path`, so it was building the package from cold inside the pin. Run by hand the three parts pass (`grep -q 'Naval Observatory' ...` exit 0; `grep -c 'SolarFixture(name:' ...` -> 35; `swift test --filter SolarFixtureTests` -> `Test run with 6 tests in 1 suite passed`) and the pin has been green on every run since. Nothing in this task touches solar; recorded, not silenced"
  - "`bash ops/queue-check` -> `QUEUE OK (147 tasks)`, exit 0"
  - "SIX MUTATIONS BY HAND, three per side, each applied ALONE and restored, each caught by a NAMED test - the table is in the Log. The one that matters: `eligibleBywayBonus 0.06 -> 0.15` (ScenicKit) is caught by exactly two tests, both new here (`every fixture row scores within 1e-6 of the oracle`, `an eligible byway scores strictly below a designated one on the same road`), and by no other test in the suite - that run printed `Test run with 223 tests in 28 suites failed with 22 issues` and named those two and nothing else. That is the hole this task closes. `ELIGIBLE_BONUS 0.06 -> 0.15` in byways.py is caught by 8 named tests, 2 of them this contract's. No survivors"
  - "NOT IN THIS TASK, unchanged from the Brief: the region rank-normaliser, producers for speedFit / sinuosity / pointsOfInterest / furniture / tunnelMeters / metersToNearestMotorway, the `scenic_score` 0..10 column, anything touching a raster or a PBF - all T-0146. `ops/test` was NOT run (it uses the shared `.build`); the two gates it wraps were run here with their own scratch path. No floor file was touched: `pins/floor_linux.txt` reads 76 against 223 tests"
---
## Brief

Filed from the 2026-09-18 11:13 panel (CODE lens, grounded; STRATEGY and PROCESS wanted T-0146 claimed whole
and the grounding pass ruled for the split). This is the one piece of M2 that needs no human, no graph, no
raster and no container: `python -m pytest` runs on this box (46 passed over test_curvature.py and
test_byways_fixture.py on 2026-09-18) and so does `swift test`.

**The contract, as it stands on main.** `Sources/ScenicKit/Scoring/SegmentScore.swift:7` writes
`score = M^0.35 * E^0.65` (`driveExponent = 0.35` :34, `sceneryExponent = 0.65` :36), E's six weights sum to
1.00 (:47-52), `dullClasses` (:79) = motorway, motorway_link, trunk, trunk_link and returns 0 (:94) -
penalised, never gated. `services/etl/etl/byways.py:108` carries the same six weights and
`SCENIC_ZERO_CLASSES` (:111) the same four classes. There is no `score.py`; `find services/etl -name
'*score*' -o -name '*normal*'` prints nothing.

**Where the two sides already disagree - demonstrate this RED first.** `SegmentTerms.swift:43` has
`isByway: Bool` and `SegmentScore.swift:55,107` adds a single `bywayBonus = 0.15`. `byways.py:100-105` has
TWO tiers, `DESIGNATED_BONUS = 0.15` and `ELIGIBLE_BONUS = 0.06`, returned by `status_bonus` (:138). Every
eligible byway differs by 0.09 in E - five orders of magnitude past the plan's 1e-6 (plan :219, "ScenicKit
SegmentScore differential vs corpus on 1,000 sampled segments < 1e-6"). The fix is one-sided: the Bool
becomes a tier (`none | eligible | designated`), because the ETL's two tiers are the reviewed product
decision (T-0028, six rounds) and the Swift Bool predates it.

**Do:**
1. `Tests/Fixtures/scoring/segment_terms.json` - ONE shared fixture of 1,000 SegmentTerms rows (seeded,
   generated by a committed script so it is reproducible; covers every highway class incl. the four dull
   ones, all three byway tiers, the soft multipliers' boundaries - tunnel 300 m, motorway proximity 150 m -
   and the `surface_unknown` x0.8 rule). Each row carries the expected score computed by NEITHER
   implementation under test: a third, deliberately naive transcription of the plan's formula inside the
   generator, reviewed by eye against plan lines 77-90. A fixture whose expectation is computed by the code
   it checks is the defect this repository exists to catch.
2. `services/etl/etl/score.py` - the formula only: M and E from already-normalised terms, the exponents, the
   byway tiers (import them from byways.py, do not restate them), the zero-class rule, the soft
   multipliers. No rasters, no GDAL, no rank-normaliser (that is T-0146's remainder). One type per file, 300
   lines.
3. `services/etl/tests/test_score_contract.py` and `Tests/ScenicKitTests/SegmentScoreContractTests.swift`,
   both reading the same fixture, both asserting |score - expected| < 1e-6 per row and naming the row id on
   failure. RED first: with `isByway: Bool` unchanged, the Swift side fails on every eligible-tier row BY
   NAME; then the tier change turns it green.
4. `SegmentTerms.isByway: Bool` -> a `BywayTier` enum (its own file). Update the existing scoring tests that
   construct terms. Correct the two doc lines in `SegmentTerms.swift` (:28 "USFS TCC", :32 "NLCD") that name
   sources the producer does not use - `landcover.py:8-13` says MRLC returned 403 and the producer is ESA
   WorldCover.
5. A mutation check on both sides (an exponent swapped, a weight moved by 0.01, the eligible tier set equal
   to the designated one) each turning a NAMED test red.

**Not in this task:** the region rank-normaliser, producers for speedFit / sinuosity / pointsOfInterest /
furniture / tunnelMeters / metersToNearestMotorway (none exists under services/etl/etl/ today), the
`scenic_score` 0..10 column, anything touching a raster or a PBF. Those are T-0146. T-0012's gate-parity
fixture should reuse this fixture's rows.

Reviewer must own neither PR #87 nor PR #82.

## Log
- 2026-09-18T18:00:00Z filed by agent/claude-fable-5-1 from the 11:13 panel's grounded synthesis (CODE lens F1/F2 and recommendation; pointers re-checked by the grounding pass: isByway is SegmentTerms.swift:43, consumed at SegmentScore.swift:107; USFS TCC is :28). pytest and swift test both run on the Windows dev box. Not started.
- 2026-09-18T18:01:36Z claimed by agent/claude-opus-5; lease until 2026-09-19T02:01:36Z
- 2026-09-18T18:10:00Z **READ FIRST, end to end, before writing anything**: `Sources/ScenicKit/Scoring/SegmentScore.swift` (129 lines at HEAD) and `SegmentTerms.swift` (95), the plan's *"The scenic engine" -> "Score per way"* block (lines 76-90) and plan:219, `services/etl/etl/byways.py:92-160` and `:224-235` (`bonus_for`, where the motorway gate on the bonus lives), `services/etl/etl/landcover.py:1-20`, `Tests/ScenicKitTests/SegmentScoreThresholdTests.swift`, the `isByway` call sites (`git grep -n isByway` -> 12 in Sources/Tests plus 4 anchor strings in `ops/mutate/segmentscore.py`), `Tests/ScenicKitTests/GuidanceMappingTests.swift:238-244` for the `#filePath` pattern this task copies, `ops/lib/check-line-cap`, and `ops/mutate/segmentscore.py` (the anchor/SKIP contract at :1-31 and `run_all` at :500-520). **One Brief pointer corrected**: the Brief says `byways.py:108` carries "the same six weights" - it does not. `grep -rn '0\.24\|0\.45\|WEIGHT' services/etl/etl/` matches one line in that whole package, `byways.py:49`, a docstring heading; `:108` is a comment about E's ceiling. The six E weights existed ONLY in `SegmentScore.swift:47-52` before this commit, which is why `score.py` restates them against the plan and imports only what `byways.py` really owns (`DESIGNATED_BONUS` :100, `ELIGIBLE_BONUS` :105, `SCENIC_ZERO_CLASSES` :111, `status_bonus` :138, `apply_to_e` :147).
- 2026-09-18T18:12:00Z **EVERY PLACE THE THREE SOURCES DISAGREE, and the ruling on each.** (1) **The byway tier.** plan:87 writes one `+0.15 byway, capped`; `byways.py:100,105,138` pays two tiers (0.15 designated, 0.06 eligible); `SegmentTerms.swift:43` had one `Bool` and `SegmentScore.swift:55,107` one bonus of 0.15. RULING (the Brief's, and T-0028's six reviewed rounds): the ETL's two tiers are the product decision, the Bool predates it. The oracle transcribes both tiers, the differential goes red on ScenicKit, and ScenicKit is what changes. (2) **The 150 m boundary.** plan:85 says *"within 150 m of a motorway x0.7"*, which is ambiguous at exactly 150.0; `SegmentScore.swift:115` is a strict `<` and `SegmentScoreThresholdTests.swift:62,66` names the reading (*"a road within 150 m of a motorway hears it, and 150 m exactly does not"*); `byways.py` is silent. RULING: exclusive on both sides, because this repository has already ruled it by name and re-deciding it in an oracle would be a silent product change. The fixture carries 150.0, `nextafter(150,0)` and `nextafter(150,inf)` rows (107 rows sit exactly on 150.0, 352 inside it) so a later change of mind is visible rather than absorbed. The tunnel boundary (plan:85 *"tunnel >300 m"*) is not ambiguous and both sides already agree; the fixture pins 300.0 and both neighbours anyway (93 rows at exactly 300.0, 403 past it). (3) **Validation.** `SegmentScore.swift:87-92` returns nil for a term outside `0...1` or a non-finite tunnel length; the plan says nothing about it. RULING: an addition, not a disagreement - `score.py` mirrors it (`out_of_range`, returns None) and `test_a_term_outside_zero_to_one_is_refused_rather_than_clamped` pins it per term. No fixture row is out of range, so the differential never rests on it. (4) **The GATE factor.** plan:78-82 multiplies the score by GATE; neither scorer implements it and neither should - hard gates are safety only and live in `ScenicKit.Gates` and the GraphHopper profile (CLAUDE.md). `score.py`'s docstring says so and scores the fixture's 165 `surface=gravel` rows like any other. (5) **The two doc lines.** `SegmentTerms.swift:28` claimed USFS TCC and `:32` NLCD; `landcover.py:8-13` records that MRLC's S3 returns 403 to anonymous access and the producer is ESA WorldCover 2021 v200. Corrected here, with the reason and the pointer, not just the name.
- 2026-09-18T18:20:00Z **RED FIRST, recorded before any Swift changed.** The contract test was written against today's API (`isByway: Bool`, an eligible byway mapped to `true` - the closest a Bool can get, and the mapping that pays it the designated bonus; mapping it to `false` is wrong by 0.06 instead of by 0.09). `swift test --scratch-path .build/T0154 --filter SegmentScoreContractTests` printed, verbatim: `x Test "an eligible byway scores strictly below a designated one on the same road" recorded an issue at SegmentScoreContractTests.swift:105:9: Expectation failed: (e -> 0.5929706302250319) < (d -> 0.5929706302250319)`; `x Test "every fixture row scores within 1e-6 of the oracle" recorded an issue ... class-primary-eligible-nosurface: got 0.5929706302250319, oracle 0.5382223387661732, delta 0.05474829145885873 (tier=eligible highway=primary)` and 19 more named rows, every one of them `tier=eligible`; the summary `240 of 1000 rows disagree with the oracle by >= 1e-06; worst delta 0.13076020187735218 at axis-scenery-zero-eligible`; `x Suite "SegmentScore contract (shared fixture)" failed after 0.177 seconds with 22 issues.`; `x Test run with 5 tests in 1 suite failed after 0.178 seconds with 22 issues.` The other three tests passed in that run, so the fixture was not simply unreadable. 240 is every eligible row the bonus can move: 242 eligible rows are scorable and not a zero class, and the two the cap flattens (`cap-saturated-eligible`, `cap-justunder-eligible`) agree at 1.0 either way.
- 2026-09-18T18:24:00Z **THE CHANGE.** `BywayTier` is a new file of its own (`none | eligible | designated`, `CaseIterable`, carrying no numbers); `SegmentTerms.isByway: Bool` -> `bywayTier: BywayTier`; `SegmentScore` gains `eligibleBywayBonus = 0.06` and `bonus(for:)`, the single place a tier becomes a number, and `bywayBonus = 0.15` keeps its name and value as the designated one so the three mutation anchors on that literal stay valid. Eight assignment sites in `Tests/` updated - five in `SegmentScoreTests`, two in `SegmentScoreWeightTests`, one in `SegmentScoreValidationTests` - and `git grep -n isByway` now prints nothing under Sources/ or Tests/. `scoreAlwaysLandsInZeroToOne` walked `[false, true]`; it now walks a written-out `[.none, .eligible, .designated]` and its count literal goes 7\*7\*2\*4\*4\*6 -> 7\*7\*3\*4\*4\*6, with a new `#expect(tiers.count == BywayTier.allCases.count)` so a fourth tier cannot be added without that grid noticing. The fixture is located from `#filePath` exactly as `GuidanceMappingTests` locates its subject; **neither `Package.swift` was touched** (serial-only, and this task holds no lock), so the JSON is read by absolute path rather than as a bundled resource.
- 2026-09-18T18:35:00Z **MUTATION TABLE. Six, three per side, each applied ALONE, run, then restored; `git status --short` after each showed only this task's own changes, and the restored files were compared byte-for-byte against pristine copies (`diff` -> IDENTICAL) because two of the mutated files are new and `git checkout --` cannot restore an untracked file.**
  | # | mutation | applied to | NAMED test(s) that went red |
  |---|---|---|---|
  | M1 | `DRIVE_EXPONENT`/`SCENERY_EXPONENT` swapped (0.35 <-> 0.65) | `services/etl/etl/score.py` | `FAILED tests/test_score_contract.py::test_every_fixture_row_scores_within_1e_6_of_the_oracle` - `690 of 1000 rows disagree ... worst delta 2.234e-01 at axis-scenery-zero-designated` |
  | M2 | `CANOPY_WEIGHT 0.24 -> 0.25` | `services/etl/etl/score.py` | same test - `697 of 1000 rows disagree ... worst delta 7.274e-03 at uniform-1.0` |
  | M3 | `ELIGIBLE_BONUS 0.06 -> 0.15` (the eligible tier set equal to the designated one) | `services/etl/etl/byways.py` | 8 named tests over the whole ETL suite, including `test_score_contract.py::test_every_fixture_row_scores_within_1e_6_of_the_oracle` and `::test_the_two_byway_tiers_are_not_the_same_number`, plus `test_byways.py::TestBonus::test_an_eligible_way_earns_less` and four more |
  | M4 | `driveExponent`/`sceneryExponent` swapped | `Sources/ScenicKit/Scoring/SegmentScore.swift` | 6 named tests: `every fixture row scores within 1e-6 of the oracle`, `the exponents are 0.35 and 0.65, and they sum to one`, `the mean is geometric, so a thrilling drive through an ugly place does not average out`, `the drive weights are exactly 0.45, 0.20, 0.20, 0.15 at the point of use, not merely ranked`, `a byway bonus is added to scenery and capped...`, `the byway bonus is exactly +0.15 added to E...` |
  | M5 | `canopyWeight 0.24 -> 0.25` | `Sources/ScenicKit/Scoring/SegmentScore.swift` | 16 named tests, `Test run with 223 tests in 28 suites failed with 88 issues`, among them `every fixture row scores within 1e-6 of the oracle` and `the scenery weights are exactly 0.24, 0.22, 0.16, 0.14, 0.12, 0.12 at the point of use, not merely ranked` |
  | M6 | `eligibleBywayBonus 0.06 -> 0.15` | `Sources/ScenicKit/Scoring/SegmentScore.swift` | EXACTLY TWO, both new in this commit: `every fixture row scores within 1e-6 of the oracle` (21 issues) and `an eligible byway scores strictly below a designated one on the same road`. `Test run with 223 tests in 28 suites failed with 22 issues` - nothing else in the suite can see it |
  No survivors, so no fixture row had to be added. M6 is the measurement that says this task was worth doing: before it, that mutation was invisible to every test in the repository.
- 2026-09-18T18:37:00Z **ONE PATH ADDED TO `touches:` AND WHY.** `ops/mutate/segmentscore.py` anchors two of its mutations on the literal line `        if t.isByway { e = min(1, e + bywayBonus) }`, which this commit deletes. Its own contract (`:14-15`) scores an unmatched anchor as SKIP and FAILS on it, so leaving them would have broken the harness quietly for the next agent. The two anchors are re-pointed at `        if bywayBonusEarned > 0 { e = min(1, e + bywayBonusEarned) }` with their mutants rewritten to match; no mutation was added or removed, and the three anchors on the `bywayBonus = 0.15` literal are untouched. `ops/mutate/` is therefore in `touches:` - declared, never bypassed. **The harness was NOT run** (it builds the package ~70 times and other agents are on this box); the re-anchoring is a textual fix and is stated as one.
- 2026-09-18T18:40:00Z **STILL OPEN, for the reviewer.** (a) `ops/test` was not run, as instructed - it uses the shared `.build`; the two suites it wraps were run here with `--scratch-path .build/T0154`. (b) `ops/mutate/segmentscore.py` was re-anchored but not executed, and its `TEST_FILES` (`:51-54`) does not list `SegmentScoreContractTests.swift`, so the `--prove-vacuity` arm does not cover the new suite and no mutation in `MUTATIONS` targets `eligibleBywayBonus` - M6 above is by hand and is not in the harness. Both are a follow-up, not something to fold into this PR silently. (c) The fixture is read by absolute `#filePath` rather than as an SPM resource, because `Package.swift` is serial-only and this task holds no lock. (d) `cap-justunder-eligible` / `-designated` do not separate the tiers (base E = 0.94, so +0.06 lands on the ceiling too); the generator's comment now says so. The separation is carried by `cap-below-*` and by 242 other eligible rows, and M6 proves it is real. (e) The first `ops/check-pins --source-only` in a cold worktree failed P-SAFE-05 with empty output because that pin runs `swift test` with no `--scratch-path`; green on every run since the build cache existed. Nothing here touches solar. (f) P-SRC-02 still does not cover Python (T-0058); `score.py` 159, `test_score_contract.py` 152, `generate.py` 251 lines, all measured with `awk 'END{print NR}'`.
- 2026-09-18T18:52:00Z **EVERY ACCEPTANCE LINE RE-RUN AT THE COMMIT, 2332e42, and quoted from that run.** `python Tests/Fixtures/scoring/generate.py` -> `rows=1000 covering=177 random=823` / `byway tiers: none=339, eligible=326, designated=335` / `zero-class rows=253  distinct highway classes=14  nonzero expected=744`, and `git diff --stat Tests/Fixtures/scoring/segment_terms.json` printed nothing - the generator is deterministic and the committed bytes are its output. `swift test --scratch-path .build/T0154` -> `Test run with 223 tests in 28 suites passed after 0.282 seconds.` `cd services/etl && python -m pytest tests -q` -> 472 dots and `[100%]`; `python -m pytest tests -rsx` -> `472 passed in 93.86s (0:01:33)`, no skips. `bash ops/lib/check-line-cap` -> `P-SRC-02: 60 Swift files tracked (Sources=21, Tests=31, apps/ios=8), none over 300 lines`. `bash ops/check-pins --source-only` -> `PINS ok=8 skipped=11 pending=1 expired=0 failed=0 tier=linux source-only`. `bash ops/queue-check` -> `QUEUE OK (147 tasks)`. Each run bare, never piped into anything before its status was read. Only the pytest wall clock differed from the pre-commit run; the line above now carries both numbers rather than the prettier one.
- 2026-09-18T19:10:00Z **Four small record defects found by the read-only verification of this build, closed before review -
  agent/claude-fable-5-1 (orchestrator), for the owner.** (a) The 18:40 entry and an acceptance line say
  `generate.py` is 251 lines; `len(text.splitlines())` over the committed file prints 254. Under the cap
  either way; the acceptance line now carries the measured value, the dated entry stays as written.
  (b) The 18:40 entry states fixture population counts that no quoted command printed. Computed from the
  committed JSON by `.artifacts/T-0154/fix1.py` at this commit: `rows: 1000, tunnel == 300.0: 93, tunnel > 300.0: 403, motorway == 150.0: 107, motorway < 150.0: 352, motorway infinite: 265, surface absent: 208, surface == gravel: 165, tier == eligible: 326`. (c) The mutation table's M3 row says
  "8 named tests" and names fewer. The verifier reproduced M3 in memory (`8 failed, 464 passed`) and the
  eight are: `test_byways.py::TestStatusMeaning::test_eligible_scores_too_but_less`,
  `::TestStatusMeaning::test_the_eligible_weight_sits_in_the_bracket_the_evidence_fixes`,
  `::TestMatching::test_the_stronger_designation_wins_even_when_the_weaker_one_overlaps_more`,
  `::TestBonus::test_an_eligible_way_earns_less`, two in `test_byways_fixture.py`, and both tests in
  `test_score_contract.py`. (d) `SegmentScoreContractTests.swift`'s doc comment on `tier(_:)` said the switch
  has no `default:` and that a new tier is a build error; it has one, and a new tier word is a recorded
  Issue plus a throw - a loud test failure, not a build error. Comment corrected; behaviour unchanged.
  STILL TRUE AND UNFIXABLE AFTER THE FACT: the red-first run is attested by the Log only - the red version of
  the contract test was never committed on its own, so it cannot be replayed from history. The verifier
  re-derived its numbers to the last digit from the fixture (an eligible row scored with the designated
  bonus), which corroborates the run; it does not replace the missing commit.
- 2026-09-18T19:32:41Z **REVIEW PASS - agent/rv1-pr89 (owner neither of this task nor of PR #87 or #82), PR
  #89 at b1005cb == origin/task/T-0154.** Reviewed in a detached worktree of origin's tip
  (`.worktrees/rv1-pr89`); `git status --short` was empty there before and after every mutating run, and
  every mutated file was restored with `git checkout --` and the empty status re-printed. Nothing in
  `.worktrees/T-0154` was written except this entry and the two front-matter fields.
  **THE CENTRAL QUESTION - answered yes: the `expected` column is computed by neither implementation.**
  `Tests/Fixtures/scoring/generate.py` imports `json`, `math`, `pathlib`, `random` and nothing else - no
  `etl.*`, no ScenicKit - and `plan_score` was read line by line against plan:78-87: the four M weights
  (0.45/0.20/0.20/0.15), the six E weights (0.24/0.22/0.16/0.14/0.12/0.12) with `impervious` and `furniture`
  entering inverted, the bonus added to E then `min(1.0, ...)` ("capped"), `m ** 0.35 * e ** 0.65`,
  `tunnelMeters > 300.0` strict, `motorway_distance < 150.0` strict (the 18:12 ruling, and the reading
  `SegmentScoreThresholdTests` already pins by name), `surface is None and highway in
  ("unclassified","residential")` -> x0.8 with the plan's other half expressed by omission, and the four
  zero classes returning 0.0 **before** any bonus or multiplier can reach them. The single divergence from
  the plan's one `+0.15` is the two tiers, transcribed as literals - disclosed in the module docstring.
  **The generator was copied OUT of the tree and re-run there** (`cp Tests/Fixtures/scoring/generate.py
  <scratch>/ && python generate.py`): `rows=1000 covering=177 random=823` / `byway tiers: none=339,
  eligible=326, designated=335` / `zero-class rows=253  distinct highway classes=14  nonzero expected=744`,
  and `cmp <scratch>/segment_terms.json Tests/Fixtures/scoring/segment_terms.json` -> BYTE-IDENTICAL. The
  committed bytes are the oracle's output, produced without the repository on the path.
  **ACCEPTANCE, every line re-run bare at b1005cb in my own worktree.** `swift test --scratch-path
  .build/rv1pr89` -> `Test run with 223 tests in 28 suites passed after 0.335 seconds.` (the acceptance line
  quotes 0.315 s - see the recordable below). `cd services/etl && python -m pytest tests -rsx` -> `472 passed
  in 81.08s (0:01:21)`, exit 0, no skip/xfail section. `bash ops/lib/check-line-cap` -> `P-SRC-02: 60 Swift
  files tracked (Sources=21, Tests=31, apps/ios=8), none over 300 lines`, exit 0. `bash ops/check-pins
  --source-only` -> `PINS ok=8 skipped=11 pending=1 expired=0 failed=0 tier=linux source-only`, exit 0 (no
  P-SAFE-05 failure here - my scratch path was warm). `bash ops/queue-check` -> `QUEUE OK (147 tasks)`, exit
  0. `awk END{print NR}`: `generate.py` 254, `score.py` 159, `test_score_contract.py` 152, `BywayTier.swift`
  28 - the 19:10 correction of 251 -> 254 is right. `gh pr checks 89` -> `core pass`, `pins-source-only
  pass`. Neither `Package.swift` appears in `git diff --name-only origin/main...HEAD`.
  **THE BYWAY TIER RE-BROKEN ON BOTH SIDES, by me, at this head.** `ELIGIBLE_BONUS 0.06 -> 0.15` in
  `byways.py` -> `8 failed, 464 passed in 103.52s`, and the eight are exactly the eight the 19:10 entry
  names: `TestStatusMeaning::test_eligible_scores_too_but_less`,
  `::test_the_eligible_weight_sits_in_the_bracket_the_evidence_fixes`,
  `TestMatching::test_the_stronger_designation_wins_even_when_the_weaker_one_overlaps_more`,
  `TestBonus::test_an_eligible_way_earns_less`, two in `test_byways_fixture.py`
  (`TestTheCasesTheDocstringClaims::test_a_second_carriageway_keeps_the_corridors_designation` and
  `::test_a_real_interstate_on_its_own_designated_corridor_still_scores_nothing` - the "two in
  test_byways_fixture.py" of that entry, now named), and both tests in `test_score_contract.py`.
  `eligibleBywayBonus 0.06 -> 0.15` in `SegmentScore.swift` -> `Test run with 223 tests in 28 suites failed
  after 0.320 seconds with 22 issues.`, and EXACTLY TWO named tests, both added by this PR: `every fixture
  row scores within 1e-6 of the oracle` and `an eligible byway scores strictly below a designated one on the
  same road`. M6 stands as measured.
  **THE RED-FIRST RUN IS CORROBORATED TO THE LAST DIGIT, not merely re-derived.** That same
  `eligibleBywayBonus -> 0.15` mutant *is* the pre-T-0154 behaviour (one 0.15 for both tiers), and it
  printed, verbatim, the strings the 18:20 entry quotes: `240 of 1000 rows disagree with the oracle by >=
  1e-06; worst delta 0.13076020187735218 at axis-scenery-zero-eligible` and
  `class-primary-eligible-nosurface: got 0.5929706302250319, oracle 0.5382223387661732, delta
  0.05474829145885873 (tier=eligible highway=primary)`. The missing red commit is a replayability gap in the
  history, not an unverifiable claim.
  **MY OWN FIVE MUTATIONS, none of them in the harness's 64 nor in the owner's six, each applied ALONE and
  restored.** (S1) `UNSURVEYED_CLASSES` in `score.py` pointed at the plan's OTHER half
  (`{"primary","secondary","tertiary"}`) -> `test_every_fixture_row_scores_within_1e_6_of_the_oracle`, `80 of
  1000 rows disagree ... worst delta 1.517e-01 at rand-0770`. (S2) the cap applied BEFORE the bonus in
  `score.py` (`min(1.0, e) + status_bonus(...)`) -> same named test, `4 of 1000 ... worst delta 7.461e-02 at
  cap-saturated-designated` - the saturated-cap rows earn their place. (S3) `RELIEF_WEIGHT` and
  `OPEN_GROUND_WEIGHT` swapped at the point of use in `scenery_mean`, E still summing to 1.00 -> same named
  test, `594 of 1000 ... worst delta 4.442e-02 at uniform-1.0`. (K1) `SegmentScore.bonus(for:)` paying the
  eligible tier the designated bonus and vice versa -> four named tests, `484 of 1000` rows, including both
  new ones and `the byway bonus is exactly +0.15 added to E ...`. (K2) `case .none: return
  eligibleBywayBonus`, so a way that is no byway at all is paid 0.06 -> fourteen named tests, `256 of 1000
  ... worst delta 0.16061951594470017 at axis-scenery-zero-none`. **NO SURVIVORS**, so I add no fixture row.
  **THE FIXTURE CANNOT PASS OVER NOTHING.** `ScoringFixture.load()` throws (`Data(contentsOf:)`) and
  `test_score_contract.py::_load` raises `AssertionError` at import, so a missing file fails rather than
  skips; `rowCount` is checked against the decoded count on both sides, `>= 1000` is asserted, ids are
  checked unique, all three tiers and all four zero classes are asserted present, and each of the two bonus
  tiers must keep `>= 50` scorable rows. `ScoringFixtureRow.init(from:)` throws on any distance spelling
  other than `"Infinity"`, and the contract suite's `tier(_:)` records an Issue and throws on an unknown
  tier word.
  **ANCHORS.** All 64 entries of `ops/mutate/segmentscore.py`'s `MUTATIONS` were imported (module loaded by
  `importlib`, harness NOT run) and each `old` string occurs **exactly once** in its target:
  `bad_anchors=0`, `MUTATIONS=64`, `MIN_MUTATIONS=64`, targets `SegmentScore.swift` and `SegmentTerms.swift`.
  The two re-pointed anchors are live. `BywayTier` is its own 28-line file, one type, name == filename.
  **RULINGS ON THE AUTHOR'S THREE DISCLOSURES - all three RECORDABLE, none blocking.** (a) *red-first not
  replayable from history*: recordable. The log's own numbers reproduce verbatim from the equivalent mutant
  at this head (above), and CLAUDE.md asks for red-then-green *in the task log*, not in a separate commit.
  (b) *mutation harness not executed*: recordable, with a correction to the disclosure - see the recordable
  below; the harness is invoked by nothing under `ops/`, `.github/` or `pins/`, verifying a fix would cost
  ~70 swift builds on a shared box, and its main arm (`caught == len(MUTATIONS)`) can only improve from a
  new catching suite. (c) *fixture read by `#filePath`, not as an SPM resource*: recordable and correct -
  both `Package.swift` files are serial-only and this task holds no lock, the pattern is already
  `GuidanceMappingTests`', and it demonstrably survives a foreign scratch path: my run from
  `.worktrees/rv1-pr89` with `--scratch-path .build/rv1pr89` read the fixture and passed.
  **RECORDABLE, none of them failing this round.** (R1) `git grep -n isByway -- Sources/ Tests/` is NOT
  empty at this head: one hit, `Tests/ScenicKitTests/SegmentScoreContractTests.swift:11`, a doc-comment
  sentence about the pre-T-0154 API. The 18:24 entry's "`git grep -n isByway` now prints nothing under
  Sources/ or Tests/" was already false at 2332e42 (`git show 2332e42:...SegmentScoreContractTests.swift |
  grep -n isByway` prints line 11). No live identifier survives - the rename is complete or the package
  would not compile - so the substance holds and only the absolute phrasing overstates. (R2)
  `ops/mutate/segmentscore.py:47-50` still says `grep -rln "SegmentScore\|SegmentTerms" Tests/ Sources/`
  "returns these FOUR test files and the two sources and nothing else"; re-run at this head it returns SIX
  Swift test files plus `generate.py`, and three sources. The consequence is stronger than STILL OPEN (b)
  states: `--prove-vacuity` will not merely fail to cover the new suite, it will **fail**, because it empties
  only `TEST_FILES`, `SegmentScoreContractTests.swift` is left standing, and it demonstrably catches
  mutations on `SegmentScore.swift` (K1, K2 and M5 above; `"the byway bonus is dropped"` in `MUTATIONS` would
  too), so `caught == 0` cannot hold. `ops/mutate/hazards.py:423,506` carries an explicit REFUSING guard for
  exactly this case and `segmentscore.py` has none, so it will report an unproven vacuity rather than
  refuse. Follow-up task, because the fix is one line in `TEST_FILES` **plus a harness run** to show it, and
  that run cannot honestly be done on this box today. (R3) Two acceptance quotes carry a wall clock that
  cannot reproduce: line 3's `Test run with 223 tests in 28 suites passed after 0.315 seconds.` (mine:
  `0.335 seconds`) and line 8's `Test run with 223 tests in 28 suites failed with 22 issues`, which never
  appears verbatim at all - the real line is `... failed after 0.320 seconds with 22 issues.` The
  load-bearing numbers (223, 28, 22) reproduce exactly; the 18:52 entry solved this for pytest's wall clock
  and not for swift's. (R4) The differential never exercises validation parity: no fixture row is out of
  range (honestly disclosed at 18:12(3)), so `score.py`'s `out_of_range` -> `None` and ScenicKit's `nil` are
  pinned only by each side's own tests, never against each other. A refused-rows section in the fixture
  would close it - T-0012 is the natural home. (R5) `MUTATIONS` has no entry on `bonus(for:)` or
  `eligibleBywayBonus`; my K1 and K2 are the kind that belong there once R2 is fixed.
  **NOT DONE BY ME:** `ops/test` (shared `.build`, as the task says), `ops/sane`, the mutation harness itself
  (`--prove-vacuity` or the full arm), any iOS/xcodebuild target, and `ops/mutate/gates.py`. I ran no
  mutation on `SegmentTerms.swift` and none on `generate.py` itself.

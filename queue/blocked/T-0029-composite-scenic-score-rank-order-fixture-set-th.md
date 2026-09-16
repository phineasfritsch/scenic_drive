---
id: T-0029
title: Composite scenic score + rank-order fixture set (the anti-mush check)
state: blocked
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T20:17:44Z
lease_expires_at: 2026-09-08T00:17:44Z
worktree: ../wt/T-0029
branch: task/T-0029
exclusive: []
touches: [services/etl/, pins/PINS.yaml]
pins_affected: []
reviewer: agent/reviewer-34
depends_on: [T-0030]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

score = GATE x M^0.35 x E^0.65 with the gates as POSITIVE EVIDENCE only (see CLAUDE.md).

THE CHECK THAT MATTERS: a hand-picked set of ~30 known-good and ~30 known-dull Bay Area segments whose RANK
ORDER the score must preserve. A unit test on the formula proves arithmetic; only the rank-order set proves the
score means anything. Makes P-PROD-01 real (it is currently pending on T-0012).

RED: swap the geometric mean for a linear sum -> the curvy-industrial vs straight-redwood pair inverts and the
rank-order test fails. That is the exact failure the geometric mean exists to prevent.

## Log
- 2026-09-07T20:17:44Z claimed by agent/claude-opus-5; lease until 2026-09-08T00:17:44Z

- 2026-09-08T01:10Z moved claimed -> blocked by agent/claude-opus-5, its owner. The arithmetic is committed
  (6376178 on task/T-0029: etl/score.py, tests/test_score.py, 41 tests). THE RANK-ORDER SET IS NOT BUILT,
  and this task must not be handed to review as though it were.

  The brief is unambiguous about which half matters: "A unit test on the formula proves arithmetic; only the
  rank-order set proves the score means anything." What is committed is the arithmetic. Calling that done
  because the tests are green is the exact failure this repo exists to catch.

  **Why it is blocked, checked rather than assumed.** The set needs ~30 known-good and ~30 known-dull REAL
  Bay Area segments, which needs their terms, which needs the Bay Area extract. It is on disk nowhere:

      services/etl/inputs/ across every worktree holds the 8 3DEP tiles, the 2 WorldCover tiles, both byway
      geojsons and the Vermont pair - and no sfbay extract. The only .pbf in any work/ directory is T-0025's
      Vermont subset.

  The manifest's OSM source for this region is `california-latest.osm.pbf` (~1.2 GB), which nothing has
  fetched, and the sfbay extract is produced from it by `etl.extract` - which is T-0030's work. Hence
  `depends_on: [T-0030]`.

  **A second reason to wait, about honesty rather than availability.** Two of the four term families are in
  review right now and their constants moved this session: T-0027 changed `BUFFER_STEP_M` 50 -> 20, redefined
  `is_wooded`/`is_built_up` around a dominance ratio, and added `OPEN_CLASSES`; T-0028 changed the
  eligible-byway weight 0.10 -> 0.06 and reordered `match()`. A rank-order fixture recorded against those
  today would be re-recorded within the week, and a snapshot that gets re-recorded whenever it disagrees is
  not evidence of anything.

  **What I am NOT doing, deliberately.** Building the set from synthetic archetypes instead of real segments.
  `tests/test_score.py` already holds those - the curvy-industrial and straight-redwood pair among them - and
  they are the arithmetic test wearing a different hat. Substituting them would satisfy the words of the
  brief and none of its point.

  **One correction to the brief that stands regardless**, from the committed work. The brief says "swap the
  geometric mean for a linear sum -> the curvy-industrial vs straight-redwood pair inverts". Measured, it
  does not invert: `impervious=0.85` and `furniture=0.8` punish E enough on their own.

      industrial  M=0.820 E=0.064   geometric 0.156   linear 0.328
      redwood     M=0.263 E=0.663   geometric 0.479   linear 0.523
      ratio redwood/industrial       geometric 3.073  linear 1.591

  What the geometric mean actually buys on that pair is SEPARATION, 3.07x against 1.59x. The test is named
  for what it measures, and a second test constructs a pair that genuinely does invert - a road that maxes
  the driving terms and is merely bland rather than paved over. Whoever builds the rank-order set should
  expect the same: pairs that look decisive in prose often are not, and the decisive ones have to be found by
  measuring.

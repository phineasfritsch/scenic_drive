---
id: T-0163
title: ETL way record and region normaliser - raw per-way terms in, the 0..1 terms score.py consumes out, deterministically
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T19:52:39Z
lease_expires_at: 2026-09-19T03:52:39Z
worktree: .worktrees/T-0163
branch: task/T-0163
exclusive: []
touches: [services/etl/etl/way_record.py, services/etl/etl/normalise.py, services/etl/tests/test_way_record.py, services/etl/tests/test_normalise.py, services/etl/tests/test_way_records_fixture.py, services/etl/tests/fixtures/, Tests/Fixtures/scoring/]
pins_affected: []
reviewer: null
depends_on: [T-0154]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

One of three disjoint pieces T-0146 was split into by the 2026-09-18 13:13 panel (CODE lens, grounded; the
grounding pass ruled against a separate "seam" PR - `score.py:119-122`'s keyword-only names ARE the seam, so
the record type rides in this task). The producers on main return different kinds of number:
`curvature.way_curvature` (curvature.py:172), `terrain.elevation_gain` / `relief` (terrain.py:85, :112) are
unbounded raw units; `landcover.fractions` is already 0..1; T-0161 will add raw `sinuosity` and metres, T-0162
a 0..1 `speed_fit` and a raw `furniture` rate. `score.py` wants every UNIT_TERM in 0..1.

**Owner's ruling on what gets ranked (the plan and T-0146's brief disagree; this settles it - record it in
your Log with both pointers and argue if the code proves it wrong):** plan:89 rank-normalises only photo
density; T-0146's brief says rank-normalise "each". RULED: a term that arrives UNBOUNDED - curvature,
elevation_gain, relief, sinuosity, furniture - becomes its REGION PERCENTILE RANK in [0,1], computed over the
SCORABLE ways of the region only (the four zero classes are excluded from the population: they score 0
whatever their terms, and 15k motorway segments must not set the curve for back roads). A term that arrives
as a fraction - canopy, impervious, water - or as a designed 0..1 function - speed_fit - is MAPPED as is,
never ranked. `points_of_interest` is neither: it is ranked within 50 km with its top decile penalised
(plan:89), needs the network, and is T-0164 - until it lands the record carries it as an explicit
`None -> 0.0 with a flag`, never a silent default.

**Build:**
1. `way_record.py` - the per-way record: fields 1:1 with `score.score`'s keyword names, each declared RAW or
   UNIT, plus `way_id`, `highway`, `surface`, `byway_status`, `tunnel_meters`, `meters_to_nearest_motorway`;
   a validator that REFUSES by field name (a UNIT field outside 0..1, a RAW field negative or non-finite, an
   unknown field). One type per file.
2. `normalise.py` - region percentile rank: deterministic (sort by value then `way_id`; ties take the average
   rank; a population of one, or all-equal values, is a NAMED case with a stated answer, not a division by
   zero); idempotent (normalising an already-normalised region is refused by name, not silently re-ranked -
   the record says which state it is in); zero classes excluded from the population and passed through.
   P-DATA-01 (ETL idempotent) is the plan's pin for this property - do not add a pin here, say so under STILL
   OPEN.
3. A committed raw-term fixture with a generator in the style of `Tests/Fixtures/scoring/generate.py` (seeded,
   deterministic, re-running leaves `git diff` empty), whose expected ranks come from a naive transcription
   inside the generator, NEVER from `normalise.py`. Then the end-to-end check this task exists for: raw
   fixture -> `normalise` -> `score.score` for every row runs with no refusal and every score in [0,1], the
   zero-class rows exactly 0.0.

**The author rule (it took PR #89 through review in one round):** rule every source disagreement in your Log
BEFORE writing code (the ranking ruling above is the first entry); re-run and quote the whole acceptance
block at your FINAL commit; close your own verifier's findings before the review is bought. Every new test
RED by name first (three mutations per module: the tie rule, the population filter, the sort key), then green.
Check `queue/*/T-0112-*` and `queue/*/T-0050-*` for overlap before you start and say what you found.

## Log
- 2026-09-18T20:20:00Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.
- 2026-09-18T19:52:39Z claimed by agent/claude-opus-5; lease until 2026-09-19T03:52:39Z
- 2026-09-18T19:59:41Z agent/claude-opus-5 (owner, author). READ BEFORE ANY CODE: CLAUDE.md; the plan's
  "Score per way" block (plan:75-91); `services/etl/etl/score.py` end to end; `services/etl/etl/byways.py`
  (`SCENIC_ZERO_CLASSES`, `status_bonus`, `apply_to_e`); `services/etl/tests/test_score_contract.py`;
  `Tests/Fixtures/scoring/generate.py`; the producer signatures `curvature.way_curvature` (curvature.py:172),
  `terrain.elevation_gain` (terrain.py:85), `terrain.relief` (terrain.py:112), `landcover.fractions`
  (landcover.py:87); `services/etl/tests/test_landcover_fixture.py` for the fixture-test style;
  `.githooks/pre-commit`'s `touches:` matcher (prefix match, `queue/*` always allowed).

  RULING R1 - WHAT GETS RANKED. Pointers: plan:89 ("Commons photo density rank-normalized in 50 km, top
  decile penalized" - photo density and nothing else) vs T-0146's brief ("rank-normalise each") vs this
  task's Brief (the owner's ruling above). RULED as the Brief states, and the code agrees rather than merely
  permitting it: `curvature.way_curvature` returns a sum of weighted segment lengths (curvature.py:172-186),
  `terrain.elevation_gain` returns metres of climb (terrain.py:85-102) and `terrain.relief` metres of range
  (terrain.py:112-130) - three different unbounded units, and no fixed divisor can map metres of climb to
  0..1 without inventing a ceiling; `landcover.fractions` already returns 0..1 per class (landcover.py:87-103)
  and ranking a fraction would throw away the only absolute scale in the mean. So: RANKED_TERMS = curvature,
  elevation_gain, relief, sinuosity, furniture. MAPPED_TERMS = canopy, impervious, water, speed_fit.
  DEFERRED_TERMS = points_of_interest (T-0164). Their union is asserted equal to `score.UNIT_TERMS` by name,
  so a term added to score.py cannot arrive unclassified.

  RULING R2 - WHICH PERCENTILE ESTIMATOR. plan:89 says "rank-normalized" and names no estimator; the Brief
  adds three requirements (ties take the average rank; a population of one and an all-equal population are
  NAMED cases with a stated answer; never a division by zero). Two candidates: (a) `(rank-1)/(n-1)`, which
  reaches exactly 0.0 and 1.0 and is 0/0 at n=1; (b) the mid-rank form `(below + 0.5*equal)/n`, which IS the
  tie group's average 1-based rank mapped by `(rank - 0.5)/n`. RULED (b): one formula satisfies all three
  requirements with no special case - n=1 gives 0.5, an all-equal population gives 0.5 to every way, and n>=1
  makes the divisor non-zero by construction. Stated consequence, now an asserted end-to-end property: a rank
  is never exactly 0.0 or 1.0, so ranking alone cannot zero a scorable way's score, and "only motorway/trunk
  score 0" (CLAUDE.md, Product invariants) stays true of the normalised corpus.

  RULING R3 - WHAT A ZERO-CLASS WAY CARRIES. The Brief says the four zero classes are "excluded from the
  population and passed through" and is silent on what their ranked terms then hold. The code decides it:
  `score.score` refuses out-of-range terms at score.py:131-132 and only reaches the zero-class branch at
  score.py:139-140, so a motorway row still carrying raw metres returns **None, not 0.0** - the end-to-end
  check this task exists for would fail on exactly the rows it is about. RULED: a third record state,
  `EXCLUDED`, in which the five ranked fields hold the named constant `EXCLUDED_RANK = 0.0` and are not
  readable as measurements, while the mapped terms pass through untouched. The validator enforces that
  equality by field name, so an excluded record cannot quietly carry a rank.

  RULING R4 - IDEMPOTENCE IS A REFUSAL. Brief: normalising an already-normalised region is refused by name.
  `terms_state` on the record is that name (`raw` / `normalised` / `excluded`), and `score_kwargs()` refuses
  in the `raw` state rather than handing raw metres to a scorer that would answer None. P-DATA-01 is the
  plan's pin for ETL idempotence; no pin is added here - see STILL OPEN.

  RULING R5 - FURNITURE IS RANKED, NOT INVERTED HERE. `score.scenery_mean` enters furniture as
  `(1 - furniture)` (score.py:92). T-0162 produces a raw furniture RATE. So the record carries the rank and
  score.py keeps the inversion: two inversions would cancel and no single-module test would see it. Asserted
  end to end instead: of two ways alike but for their furniture rate, the busier roadside scores lower.

  RULING R6 - SINUOSITY GETS NO FLOOR. Sinuosity is >= 1.0 by construction (path length / straight-line
  distance), but the Brief's RAW rule is "negative or non-finite" and a >= 1.0 floor here would be a claim
  about T-0161's not-yet-existing output that this task cannot verify. Not added; the rank is invariant to
  any monotone shift anyway.

  OVERLAP, as the Brief asks. `queue/backlog/T-0112-*` (curvature-per-km saturates and ranks rat-runs):
  touches `services/etl/etl/score.py`, `tests/test_score_rank_order.py`, `tests/fixtures/`. It argues which
  raw number `curvature.py` should hand over - per-km or the raw sum - which is upstream of this task; this
  normaliser ranks whatever non-negative raw value arrives and its tests use both scales. No overlap with
  `way_record.py` or `normalise.py`. `queue/claimed/T-0050-*` (whether the scenic index adopts Curvature's
  six squash post-processors): the same upstream shape, a product decision about the raw value, `touches:
  [services/etl/]`. Neither blocks nor is blocked by this task. Sibling T-0161 shares the
  `services/etl/tests/fixtures/` touches prefix with this task; the filenames are disjoint
  (`way_records_fixture.json` / `generate_way_records.py` here).

  TOUCHES AMENDED in this commit: `services/etl/tests/test_way_records_fixture.py` added. The end-to-end
  check wants the repo's own `test_*_fixture.py` name (`test_landcover_fixture.py`,
  `test_terrain_fixture.py`, `test_byways_fixture.py`) and folding it into `test_normalise.py` would push
  that file at the 300-line cap. `Tests/Fixtures/scoring/` stays in the list and is NOT touched: the shared
  cross-language fixture is a snapshot reference (CLAUDE.md, Verification).

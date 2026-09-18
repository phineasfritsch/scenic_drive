---
id: T-0163
title: ETL way record and region normaliser - raw per-way terms in, the 0..1 terms score.py consumes out, deterministically
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/way_record.py, services/etl/etl/normalise.py, services/etl/tests/test_way_record.py, services/etl/tests/test_normalise.py, services/etl/tests/fixtures/, Tests/Fixtures/scoring/]
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

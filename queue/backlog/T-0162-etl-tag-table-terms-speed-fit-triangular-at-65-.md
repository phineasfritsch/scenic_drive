---
id: T-0162
title: ETL tag-table terms - speed_fit (triangular at 65 km/h) and furniture, from OSM tags alone
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/speedfit.py, services/etl/etl/furniture.py, services/etl/etl/tagfilter.py, services/etl/tests/test_speedfit.py, services/etl/tests/test_furniture.py, services/etl/tests/test_tagfilter.py]
pins_affected: []
reviewer: null
depends_on: [T-0154]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

One of three disjoint pieces T-0146 was split into by the 2026-09-18 13:13 panel (CODE lens, grounded).
`services/etl/etl/score.py` takes keyword-only `speed_fit` and `furniture` in 0..1 (UNIT_TERMS, score.py:72-73)
and nothing produces either. Both come from tags alone - no geometry library, no raster, no container.

**Build:**
1. `speedfit.py` - the plan's `speed_fit`: "triangular at 65 km/h" (plan:89). 1.0 at 65 km/h, falling linearly
   to 0.0 at the two feet. The plan gives the apex and not the feet: RULE the feet in your Log before code
   (owner's starting ruling: 0 at 25 km/h and at 105 km/h - symmetric, so a 45 and an 85 km/h road score the
   same 0.5; argue against it in the Log if the plan's intent reads otherwise). The speed comes from `maxspeed`
   when it parses (km/h bare number, `NN mph`, the common `signals`/`none`/`walk` non-numerics each ruled by
   name) and otherwise from a per-`highway`-class default table LOCAL TO THIS MODULE, typed out and pinned by
   a test against literals. NEVER read or write `services/routing/profiles/` - serial-only files another task
   owns. Output is already 0..1: it is mapped, never region-ranked.
2. `furniture.py` - RAW street-furniture count per kilometre for a way: nodes on or tagged along it that make
   a road feel urban (`highway=street_lamp`, `highway=traffic_signals`, `highway=stop`, `highway=crossing`,
   `traffic_calming=*`, `barrier=bollard` - enumerate the accepted set as a named constant pinned against
   literals; say in the docstring what is deliberately NOT counted and why). Unbounded raw value; the region
   normaliser (T-0163) maps it to 0..1 and score.py inverts it (`1 - furniture`). Do not normalise here.
3. If - and only if - the extract's tag filter drops a tag either module needs, this task is the SOLE owner of
   `tagfilter.py` for the duration: add the tag, extend `test_tagfilter.py`'s literal expectations, and say in
   the Log which per-class count in `regions/*/region.json` that would move (do NOT re-record counts - that
   needs the container and is T-0024's gate; state it as STILL OPEN).

**The author rule (it took PR #89 through review in one round):** rule every place the plan, score.py and the
OSM wiki's tag semantics disagree in your Log BEFORE writing code; re-run and quote the whole acceptance
block at your FINAL commit; close your own verifier's findings before the review is bought. Expected values
typed out from arithmetic shown in a comment, never computed by the function under test. Every new test
demonstrated RED by name (three mutations per module), then green. Whole ETL suite green with zero skips.

## Log
- 2026-09-18T20:20:00Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.

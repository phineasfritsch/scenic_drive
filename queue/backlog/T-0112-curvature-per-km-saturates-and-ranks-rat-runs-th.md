---
id: T-0112
title: curvature-per-km saturates and ranks rat-runs; the raw sum ranks real canyon roads
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/score.py, services/etl/tests/test_score_rank_order.py, services/etl/tests/fixtures/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "pytest -k rank_order -> the curv term's top-100 over the LA extract is not majority residential"
  - "RED: the same assertion against curvature-per-km prints 96 residential in the top 100 and exits 1"
---
## Brief

**First real curvature measurement in this project, on 26,549 real Los Angeles ways.** Source:
`work/la/la-filtered.osm.pbf` (the T-0107 extract) exported to GeoJSON with `osmium export`, filtered to
routable classes, `score.py`'s real safety gates applied (10,226 ways gated), ways under 400 m dropped.

Two candidate ranking keys, and they disagree in the way CLAUDE.md says is fatal.

**Ranked by curvature per km** - the density measure, which looks like the obviously fair one because the raw
sum rewards a road for being long:

     curv/km  class        name
      1817.5  residential  Putney Road
      1815.8  residential  Rodgerton Drive
      1809.2  residential  Saint Andrews Drive
      1804.5  residential  La Cuesta Drive
      1793.8  residential  Tuxedo Terrace

Those are Hollywood Hills switchback stubs. **96 of the top 100 are `residential` or `living_street`.**

**Ranked by raw sum** - what the Curvature project itself publishes:

        raw  class        name
      17155  tertiary     Latigo Canyon Road
      14354  primary      Angeles Crest Highway
      11942  primary      Angeles Crest Highway
       9251  tertiary     Piuma Road
       8407  unclassified Corral Canyon Road
       8278  tertiary     Yerba Buena Road
       7341  secondary    Little Tujunga Canyon Road
       5930  tertiary     Tuna Canyon Road

Latigo Canyon, Angeles Crest, Piuma, Corral Canyon, Yerba Buena, Tuna Canyon, Stunt Road, Saddle Peak,
Mulholland Highway. **That is the canonical Southern California driving-roads list, produced from geometry
alone with no scenery data of any kind**, and it is the closest thing to an external oracle this project has
found since the Curvature Vermont numbers. 44 of the top 100 are residential - still high, but the top 20 is
canyon highways.

**Why per-km fails, mechanically.** `LEVELS` in `curvature.py` caps the per-metre weight at 2.0, so
curvature-per-km is bounded at 2000 by construction. Measured distribution over the 26,549 ways:

    curv/km      ways     share
    0-1        12,819     48.3%
    1-100       3,875     14.6%
    100-400     5,556     20.9%
    400-800     2,737     10.3%
    800-1200    1,076      4.1%
    1200-1600     438      1.6%
    1600-1800      44      0.2%
    1800-2000       4      0.0%

The top 200 ways span 1393.0 to 1817.5 - **21.2% of the scale for 200 roads** - with a median length of
0.60 km. The metric has stopped discriminating at exactly the end of the range the ranking reads from. A
0.4 km road that is entirely one hairpin saturates it; a 15 km canyon road with fifty of them cannot beat it.

**Why this matters beyond picking a key.** CLAUDE.md's first fatal risk is *"one residential rat-run ends the
relationship."* The simplest defensible scorer, run on real data, puts 96 rat-runs in its top 100. This is
not a hypothetical the anti-rat-run penalty guards against later - it is the default behaviour of the term
before anything guards it.

Do:

1. **Decide the normalisation of the `curv` term in `score.py` against this data and record the decision with
   its top-100 class mix.** `curv` feeds `M` at weight 0.45, and `M` carries exponent 0.35, so the term is
   normalised to [0,1] somewhere - and neither candidate is that shape today. Raw sum is unbounded and
   length-dependent; per-km saturates. Whatever is chosen, the argument must cite measured numbers, not
   plausibility.
2. **Add the rank-order fixture T-0029 has been blocked for.** It is now unblockable: real extracts exist.
   The assertion that catches this defect class is not "Latigo scores above 8" - it is a class-mix property:
   *the top 100 of the curv term is not majority `residential`.* That is a single number, it is checkable,
   and it fails loudly on the per-km implementation.
3. **Keep the raw-sum ranking as a named oracle.** Latigo/Angeles Crest/Piuma/Yerba Buena/Stunt/Saddle Peak
   are externally verifiable as LA's canonical driving roads. A future scoring change that drops them out of
   the top 25 near LA is a regression, whatever else improves.

Reproduce with `.artifacts/score-la.py` and `.artifacts/analyze-la.py` against
`services/etl/work/la/la-ways.geojson`.

**RED FIRST.** The red run is the class-mix assertion in step 2 against the per-km key: it must print 96 and
exit non-zero before the normalisation is changed.

## Log

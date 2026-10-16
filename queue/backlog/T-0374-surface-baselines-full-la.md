---
id: T-0374
title: Re-measure surfacecoverage.BASELINES over the FULL LA corpus - the canyon-window baselines put motorway and motorway_link red on full LA
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/surfacecoverage.py, services/etl/tests/, ops/lib/, ops/mutate/, pins/PINS.yaml, queue/]
pins_affected: [P-OPS-09]
reviewer: null
depends_on: [T-0372]
verify: [ops/check-pins]
acceptance: []
---
## Brief

Filed by agent/claude-opus-5 from T-0372 round 2 (2026-10-16). surfacecoverage.BASELINES were measured on T-0205's
canyon window (x 0.75). T-0372 measured the FULL LA corpus (T-0275, /home/phineas/t0242/la-corpus.sqlite in WSL,
560208 ways, 874391 segments, schema 3) through `python3 ops/lib/sane_corpus.py --corpus`: rc=4,
`FAIL corpus-surface motorway: surface coverage 0.4297 is below the baseline 0.593 (3217 known of 7486 ways);
motorway_link: surface coverage 0.1905 is below the baseline 0.318 (1887 known of 9908 ways)`. The canyon window
itself is green ([] verdict). So ops/sane exit 4 goes red the moment a full LA corpus sits at
$SCENIC_REGION_WORK/la-corpus.sqlite - correctly by today's numbers, wrongly by intent.

MEASURE first, read-only: every class's known/total over the full LA corpus's meta.surface_coverage (quote the whole
table), next to the canyon window's. RULE whether BASELINES become per-region (la full vs the CI golden set) or one
table re-derived from the full region, and the 0.75 margin. Then: the new literals, the surfacecoverage tests and
its mutation population re-run, check-sane-corpus (its rows place classes on BASELINES, so they follow), and the full
LA corpus through sane_corpus.py green on corpus-surface. Do NOT touch prod/R2.

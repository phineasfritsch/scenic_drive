---
id: T-0240
title: quietness - measured traffic counts per way (Caltrans AADT on state routes, LA County Public Works counts on county roads), road class as a flagged fallback, into the E term's empty 0.14 slot; licensing ruled by the human first
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/etl/quietness.py, services/etl/tests/test_quietness.py, services/etl/tests/fixtures/, services/etl/inputs/manifest.yaml, services/etl/etl/score.py, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0208]
verify: [ops/test, ops/check-pins]
acceptance:
  - "HUMAN GATE FIRST: the owner rules on licensing in the Log - Caltrans AADT ('Copyright State of California ... made available to the public solely for informational purposes') and LA County Public Works counts (eGIS Terms of Use) carry no explicit open license; neither is cleared for redistribution in the app. No code before the ruling"
  - "MEASURED population (quietness probe, 2026-09-25, .artifacts/data-probe/quietness/, 11,740 canyon-window ways): 751 ways measured (6.4% of ways, 12.7% of length; 5.3% Caltrans, 7.4% County); q = (5 - log10 ADT)/3 clamped to [0,1]; over the owner's 8 good back roads vs 4 busy scenic highways the length-weighted pair AUC is 1.000 (lowest good Encinal 0.403 > highest busy Kanan Dume 0.305; measured good <= 3,733/day, busy >= 12,201/day). Road class alone also scores AUC 1.000 on these 12 roads, so the acceptance is WITHIN-class ranking: a test over recorded counts orders Saddle Peak (476/day) above Old Topanga (3,733/day), both secondary/tertiary"
  - "unmeasured ways take a road-class fallback flagged as an estimate (never the lanes/speed proxy as if measured - Spearman 0.29-0.33 once class is removed); the per-way value lands in score.py's E term in place of the empty points_of_interest slot (weights unchanged, 0.14), RULED in the Log with the before/after frontier for T1 and T4 from ops/plan --menu"
  - "the new numeric module ships its ops/mutate population with a literal floor; the inputs enter through services/etl/inputs/manifest.yaml (URL, sha256, license field)"
---
## Brief

The owner's positioning is 'calm adventure' and the taste is back roads over busy scenic highways (Saddle Peak over
PCH). The scorer today cannot see traffic at all. Of three candidate inputs measured on 2026-09-25, quietness is the
only one that separates the owner's roads in the owner's direction: OSM points of interest (AUC 0.30-0.475) and
Commons photo density (dense on PCH and the Getty Villa, zero on Encinal) point the wrong way - they mark where
tourists go. Weekend variant (the County's DAY_OF_WEEK field) worth a ruling: Mulholland picks up the weekend surge.
Does not transfer by itself: the Bay Area golden set and the incorporated cities need their own count sources.

## Log
- 2026-09-25T23:46:40Z filed by agent/claude-opus-5 (orchestrator) from the three scenic-data probes. FOR THE OWNER: the licensing ruling on the two count sources.

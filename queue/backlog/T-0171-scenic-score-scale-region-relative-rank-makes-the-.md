---
id: T-0171
title: scenic_score scale - region-relative percentile rank makes the plan's honest-failure floor unreachable; decide the reference distribution
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/normalise.py, services/etl/tests/, services/etl/regions/, Sources/ScenicKit/Scoring/]
pins_affected: []
depends_on: [T-0168]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

A PRODUCT decision, not a code fix. PR #93 (T-0163) normalises every unbounded term - curvature, elevation
gain, relief, sinuosity, furniture, photo density - by PERCENTILE RANK within the region's scorable ways
(`normalise_region`, mid-rank estimator, ruling R2 there; plan line 89 says only "rank-normalized" and names
no reference population). Its round-1 reviewer (agent/rv1-pr93, entry appended verbatim to T-0163's Log by the
fixer) put the consequence in one sentence: a region-relative rank means a table-flat region's straightest
best road ranks like a mountain pass, so the plan's honest failure - RouteScore < 0.45 -> "not much pretty
within 25 minutes of this drive" (plan, Problem A step 3) - can never fire on absolute grounds, and the P90
term of the route score is relative to whatever the region happens to contain. The fixer of #93 makes the seam
READY without deciding: `normalise_region` gains an optional explicit `reference` population (rank against a
supplied distribution instead of the region's own; default = today's behaviour), tested both ways.

**This task decides and pins it.** Rule in the Log, with the reviewer's arithmetic quoted, between:
 (a) a FIXED reference distribution per ranked term, recorded from a named extract at a dated commit and
     versioned as data (`services/etl/regions/<region>/reference.json`, sha in the manifest), so a flat region
     scores low in absolute terms and the honest-failure floor means something; or
 (b) absolute breakpoints in the producers' own units (the Curvature project's values, metres of relief per km,
     furniture per km) typed out from the plan and the oracles.
Whichever: the ScenicKit side (`SegmentScore` parity, P-PROD-01) must see the same mapping, and `ops/sane`
check 4's "no motorway/trunk/private/unpaved way with a score above 0" is unaffected (those are gates, not
ranks). The RED that must exist first: a synthetic region in which every way is straight, flat, treeless and
unfurnished must score BELOW the honest-failure threshold end to end - today it scores like any other region.
Then the reviewer's product question is closed with a number the plan can be held to.

Not in this task: the route-level honest-failure logic itself (M3, T-0116's budget search and the route score);
photo density (T-0164); the tagged-PBF write (T-0168).

## Log
- 2026-09-18T21:23:07Z filed by agent/claude-fable-5-1 from PR #93's round-1 review (agent/rv1-pr93, recordable R-1) and the
  fixer brief that made the seam ready (`reference` argument on `normalise_region`). Not started.
- 2026-09-18T21:54:27Z depends_on -> [T-0168] by agent/claude-fable-5-1 (15:13 panel, STRATEGY F4, grounded): plan:283's "8/10
  top-scored ways are roads you'd drive" is a within-region top-K judgement that percentile rank does not
  disturb, and the 0.45 floor this task protects is route-level (plan:117; M3, T-0116). Ruling the reference
  distribution over a hand-written fixture would mean guessing California's curvature spread; it is ruled
  against T-0168's real scored extract, and before T-0031 imports the 0..10 encoded value.

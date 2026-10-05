---
id: T-0262
title: the Worker serves POST /isochrone - the Surprise reach as nested time-bucket polygons from GraphHopper /isochrone, one coordinate at 2 dp, quota first, cached daily
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T15:08:50Z
lease_expires_at: 2026-10-06T03:08:50Z
worktree: .worktrees/T-0262
branch: task/T-0262
exclusive: []
touches: [services/api/]
pins_affected: [P-PRIV-05, P-COST-01, P-COST-04]
reviewer: null
depends_on: [T-0248, T-0256]
verify: [ops/test, ops/check-pins]
acceptance:
  - "POST /isochrone {start:{lat,lon}, minutes} (whitelisted keys at every level, start at most 2 dp, minutes in a ruled range) answers {buckets:[{minutes, polygon}], ...} for ruled one-way buckets (e.g. 15/30/45/60 up to minutes/2), built from ONE GraphHopper /isochrone request (profile car_scenic or car_fast - ruled) carrying the secret header; the whole response is tested by EXACT equality over a recorded or ruled-synthetic router answer"
  - "KILL=1 -> 503 before the body is read; quota reserved before the upstream call (its own kind, ruled: the plan's Surprise free tier is 3/day); the request count is exactly 1 per call and 0 on a cache hit; the cache key is (start at 2 dp, minutes bucket, UTC day, graph/closures version) and a hit spends no quota (ruled) - each a test by name through ROUTES['/isochrone']"
  - "a client can turn the buckets into the round-trip minutes Surprise.pick (T-0253) takes as its reach input: the ruling says how (bucket upper bound x 2, or the matrix) and a TS test pins that conversion for three points; a TS mutation population entry set with a literal floor"
---
## Brief

M5 Surprise: plan 'Reach polygon from /isochrone (cached per H3-8 x 15-min bucket, daily)'. T-0253 shipped the
on-device selector, whose reach input is per-candidate round-trip minutes; nothing serves the reach yet. Copy the
shapes of T-0248 (/plan), T-0252 (/loop) and T-0256 (deps, QuotaCounter kinds, the secret header) - all merged.
H3 is not in the Worker today: a 2-dp start (~1 km) is the ruled cache cell unless the author measures a reason to
add an H3 dependency. No deploy, no Cloudflare resources.

## Log
- 2026-10-05T15:07:03Z filed by agent/claude-opus-5 (orchestrator) after PR #147 (T-0256) merged.
- 2026-10-05T15:08:50Z claimed by agent/claude-opus-5; lease until 2026-10-06T03:08:50Z

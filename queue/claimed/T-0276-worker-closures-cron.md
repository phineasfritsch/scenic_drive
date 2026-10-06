---
id: T-0276
title: the Worker's closures cron - Caltrans Lane Closure System (LCS) full closures for the LA district into KV as at most 50 polygons, a closures-version every route sends as areas and folds into its cache key; stale feed fails safe
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T07:59:18Z
lease_expires_at: 2026-10-06T19:59:18Z
worktree: .worktrees/T-0276
branch: task/T-0276
exclusive: []
touches: [services/api/, Tests/Fixtures/t0276/]
pins_affected: [P-SAFE-08, P-SAFE-01]
reviewer: null
depends_on: [T-0256, T-0262, T-0268]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST: fetch the public Caltrans LCS feed for District 7 (cwwp2.dot.ca.gov lcs JSON - quote URL, licence/terms page and fetch time in the Log; record one response under Tests/Fixtures/t0276/ verbatim) and count full closures vs lane closures, their geometry kinds and active windows BEFORE writing any predicate"
  - "a scheduled() handler (cron every 15 min in wrangler.jsonc) parses ONLY full closures active now, buffers each to a ruled polygon (<= 50 total, nearest-first or ruled cap order), and writes {version, fetched_at, geojson} to KV; parse is a table test over the recorded fixture by full equality, every malformed/missing field refused per row (range tables at every bound); no secret, no 511 key (511 needs the owner's key - a later task)"
  - "/plan, /loop, /isochrone, /trip pass the current closures as buildCustomModel areas (rejectCustomModel still applies) and include closures-version in every cache key; a KV read failure or a feed older than a ruled max age (P-SAFE-08: 30 min) never routes THROUGH a stale closure silently - rule fail-safe (serve with the last good set + a 'closures stale' hazard) and test it through ROUTES; KILL unaffected; a TS mutation population with a literal floor"
---
## Brief

Plan 'Closures: Worker cron every 15 min: 511 SF Bay Traffic Events (free key) + Caltrans LCS D4 -> KV closures/*.geojson
(<50 KB, <= 50 polygons); sent as areas in every request; client shows HazardFlag.closure; plan cache key includes
closures-version' and pin P-SAFE-08. The owner is in LA, so District 7 first (memory: user-lives-in-la). The custom
model already accepts closures (customModel.ts closureGeometries); nothing produces them. No deploy, no Cloudflare
resources.

## Log
- 2026-10-06T07:52:07Z filed by agent/claude-opus-5 (orchestrator) from the plan's lifecycle table (closures).
- 2026-10-06T07:59:18Z claimed by agent/claude-opus-5; lease until 2026-10-06T19:59:18Z

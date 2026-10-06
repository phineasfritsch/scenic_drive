---
id: T-0282
title: closures nearest-first per request - KV keeps every active full closure (measured), and each driven request sends the <=50 polygons nearest its own corridor instead of a fixed global 50
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/, Tests/Fixtures/t0276/, pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-SAFE-08, P-SAFE-01]
reviewer: null
depends_on: [T-0276, T-0281]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST on the recorded D7 fixture: active full closures (163 at record time), polygons after buffering, KV value bytes for all of them vs Cloudflare's KV value limit, and the GraphHopper custom-model areas limit actually configured in services/routing (quote both); RULE the stored cap and the per-request selection (distance from each closure to the request's origin/destination segment, or a ruled corridor box) in the Log before code"
  - "the cron stores every active full closure up to the measured ceiling; each driven request (/plan, /loop, /trip legs) selects its nearest <= 50 by the ruled metric, deterministic tie-break; a closure ON the straight corridor is never dropped while a farther one is kept - a table test through ROUTES by full equality of the areas sent; the closures-version still keys every cache; the 'closures dropped' count is reported in the hazard when > 0"
  - "P-SAFE-08's WHAT IT CANNOT SEE line about the global cap is superseded by an APPENDED dated sentence; new tests bound by name under P-SAFE-08; a TS mutation population entry set with a literal floor and the table-rows-as-functions-of-input discipline (rows over an empty set, one closure, and > 50)"
---
## Brief

T-0276 stillOpen 3 / T-0281 WHAT IT CANNOT SEE: the global 50-polygon cap dropped 121 of 163 active full closures on
the recorded LA feed, so a route can be sent through a dropped closure with no hazard. Selecting per request keeps
the ones that matter for that drive.

## Log
- 2026-10-06T15:25:23Z filed by agent/claude-opus-5 (orchestrator) after PR #171 (T-0281) review PASS.

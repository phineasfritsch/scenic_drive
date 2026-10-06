---
id: T-0288
title: the Worker serves GET /config - typed remote config (feature flags, quota display numbers, min app build, kill-switch mirror, supported regions) from KV with compiled-in defaults; any bad or missing KV value falls back to defaults, never to an unsafe value
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/]
pins_affected: [P-COST-01]
reviewer: null
depends_on: [T-0256]
verify: [ops/test, ops/check-pins]
acceptance:
  - "GET /config answers a closed JSON object (whitelisted keys only; RULE the key set from the plan: min_app_build, planning_paused mirror of KILL, supported_regions [la], feature flags for loop/trip/surprise, quota numbers read FROM quota.ts never retyped) built from compiled defaults overlaid by a KV 'config/v1' record; every field validated by a whitelist table at every bound; any invalid field drops to its default individually and the answer says which (config_warnings); KV unbound/throws -> pure defaults; the safety-relevant fields (planning_paused) can only be made MORE restrictive by KV, never less (a KV 'false' cannot unpause an env KILL=1)"
  - "cacheable (ruled max-age), no request read beyond the route (requestReadSites APPROVED extended by equality), KILL never blocks /config itself; tests through ROUTES by full equality with the cross-product discipline (KV absent / defaults / every field invalid / every field at its bounds); a TS mutation population with a literal floor"
---
## Brief

Plan Worker list: '/config' and lifecycle 'remote config'. The app needs one place to learn min build, which features
are on, the supported region and whether planning is paused (PlanError.planningPaused). No deploy; KV binding declared
only.

## Log
- 2026-10-06T20:22:31Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 remote config).

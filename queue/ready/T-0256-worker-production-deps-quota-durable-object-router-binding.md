---
id: T-0256
title: Worker production deps - Durable Object quota counters, the ROUTER_URL binding with the secret header, a place resolver, so /plan and /loop stop answering 503 planning_unavailable when the bindings exist
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/]
pins_affected: [P-COST-01, P-COST-02, P-COST-03]
reviewer: null
depends_on: [T-0248, T-0252]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a Durable Object class (one type per file) implements upstream.ts's Counters - reserve-before-call per device per UTC day by tier (anon 3 / free 10 / paid 200 from quota.ts, never a second copy of the numbers) and the monthly MAX_MONTHLY_UPSTREAM_CALLS ceiling - plus a per-kind daily allowance so a free loop is 1/day (plan table) without spending a plan; tested through the shipping handlers over an in-memory DurableObjectState fake by EXACT equality of the counter state after each call"
  - "planDepsFromEnv and the /loop deps factory return real deps exactly when DO binding, ROUTER_URL and the ROUTER_SECRET secret are all present, and still null (503 planning_unavailable, zero upstream) when ANY one is missing - a test per missing binding by name; every upstream fetch carries the secret header (P-COST-03), asserted on the recorded request"
  - "a place resolver for /plan's destination id over the D1 binding (or a ruled bundled table), unknown id 404 with zero upstream calls unchanged"
  - "wrangler.jsonc gains the DO binding + migration and ROUTER_URL as a var with a non-routable placeholder; no secret in the tree; the KILL switch reads KV if bound and the existing env var otherwise (ruled); vitest count quoted RED first then green; a TS mutation population entry for the DO counter arithmetic with a literal floor"
---
## Brief

T-0248 and T-0252 shipped /plan and /loop with injected deps; production answers 503 planning_unavailable because
`planDepsFromEnv` returns null (T-0248 stillOpen 1; T-0252 R10). This task makes the Worker deployable the moment the
owner binds a router and runs `wrangler deploy` - it does NOT deploy, create Cloudflare resources or touch secrets.
Also closes T-0252's stillOpen 'loop quota has no kind'. Copy the shapes of services/api/src/upstream.ts and quota.ts.

## Log
- 2026-10-05T12:14:20Z filed by agent/claude-opus-5 (orchestrator) after PR #143 (T-0252) merged.

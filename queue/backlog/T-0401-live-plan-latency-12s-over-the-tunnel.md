---
id: T-0401
title: A live /plan takes 12.1 s (6 router evaluations across the tunnel) against the plan's p95 1.5 s - measure where the time goes and cut it
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, ops/lib/, queue/]
pins_affected: [P-COST-04, P-SAFE-04]
reviewer: null
depends_on: []
verify: [ops/test]
acceptance: []
---
## Brief

Measured 2026-10-17 (T-0395), one live request through the deployed Worker (c6f2da75) to the pilot router (the
owner's Windows box, WSL docker, Cloudflare Tunnel scenic-router.phineasfritsch.com): origin 34.07,-118.44 ->
Topanga place, budget 25 -> HTTP 200 in 12.1 s total; evaluations 6, lambda 7.75. The plan's target is p95 < 1.5 s
against the CI router. The phone pilot will feel 12 s as broken.

This is a MEASUREMENT task first: time each upstream call (Worker -> tunnel -> Caddy -> GraphHopper) and the
Worker's own work, for at least 5 live plans to different seeded places (privacy rule: one 2-dp origin per request).
Quote the per-call times. Then rule which lever pays: parallel bracketing evaluations within the <= 2 in-flight cap
(P-COST-04), a smaller lambda search when the first bracket already fits, router-side JVM warmup / ch.disable cost,
or tunnel RTT. File the fix as its own acceptance once the population is measured. The ceiling (ETA <= fastest +
budget) must hold through any change.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0395's live /plan probe.

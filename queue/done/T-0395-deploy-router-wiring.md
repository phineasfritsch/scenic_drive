---
id: T-0395
title: Deploy the router wiring (T-0391's ROUTER_URL and GRAPH_VERSION) and prove one live /plan plus ops/sane --prod
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T12:22:46Z
lease_expires_at: 2026-10-18T12:22:46Z
worktree: .worktrees/T-0395
branch: task/T-0395
exclusive: [prod]
touches: [ops/api-url, queue/]
pins_affected: []
reviewer: agent/rv1-t0395
depends_on: [T-0391]
verify: [ops/sane]
acceptance: []
---
## Brief

T-0391 (PR #291) merged the wrangler.jsonc vars ROUTER_URL=https://scenic-router.phineasfritsch.com and
GRAPH_VERSION=d802c102...acb9. Production still runs 2daea62c with the placeholder. Run `bash ops/deploy` from
main under prod.lock; quote DEPLOYED, /__version, /__health; send ONE /plan request that obeys the privacy rule
(one coordinate per action, 2 dp) through the shipped route and quote its status and shape (no secrets); run
`ops/sane --prod` and quote every exit code; record what is still degraded and why. The router runs on the
owner's machine through a Cloudflare Tunnel (owner-authorised pilot, 2026-10-17).

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0391's review note (the vars take effect only at the next deploy).
- 2026-10-17T12:22:46Z claimed by agent/claude-opus-5; lease until 2026-10-18T12:22:46Z
- 2026-10-17T16:07:43Z agent/claude-opus-5: DEPLOYED. First deploy 5e4150a0 (live == HEAD, ROUTER_URL + GRAPH_VERSION bound). /loop through the Worker reached the tunnelled router and answered real coordinates from Westwood. /plan then answered 404 unknown_place until D1 places was seeded: T-0393 merged (c6f2da75); 'bash ops/seed-places --out .artifacts/seed-places/out' printed 'schema_version=4 region=la corpus_version=20261006T000000Z rows=1334 chunks=3 sha256=0e6435da...6e86'; the three printed 'npx wrangler d1 execute scenic --remote --file ...' lines each answered success:true; 'SELECT count(*) FROM places' answered 1334.
- 2026-10-17T16:07:43Z agent/claude-opus-5: LIVE /plan (one origin coordinate at 2 dp, destination a place id - privacy rule kept): origin 34.07,-118.44 -> place 710486223536647933 (Topanga, from corpus-fallback.sqlite), budget 25 -> HTTP 200 in 12.1 s; eta_s 1844.4, fastest_eta_s 1529.6, ceiling_s 3029.6 (eta <= ceiling holds), lambda 7.75, evaluations 6, used_budget false, eta_is_estimate true, hazards [], 9 waypoints, apple_maps_url maps.apple.com/directions with 9 waypoints. Latency 12.1 s is far over the plan's p95 1.5 s (6 evaluations across the tunnel); filed as its own task.
- 2026-10-17T16:07:43Z agent/claude-opus-5: ops/sane --prod after the T-0393 merge exited 3: 'version FAIL services/api changed since live 5e4150a0 -> deploy pending: services/api/test/fixtures/seed-places/places-000{1,2,3}.sql' - test fixtures only, no Worker code; filed as its own task (the version check should not count services/api/test/). Redeployed: 'DEPLOYED sha=c6f2da75788f019a97eb3acfd65a885b7d8c97f0 live=c6f2da75788f019a97eb3acfd65a885b7d8c97f0 built_at=2026-10-17T16:02:26Z'. Re-run: backend ok (db up), 'version ok live c6f2da75 == Worker code at HEAD c6f2da75', quota ok (15 of 225000, kill switch off), legal/manifest/tiles/corpus/goldens skip (unpublished, M6/T-0008), bounds ok; exit 10 ONLY from 'worktrees FAIL 1 of 95' = local T-0104 (no origin branch), not production.
- 2026-10-17T16:14:36Z agent/rv1-t0395: review PASS (round 1). /__version git_sha c6f2da75788f019a97eb3acfd65a885b7d8c97f0 (an ancestor of origin/main efbb58e9); /__health ok true, db up, kill_switch false. bash ops/seed-places --dry-run on origin/main printed rows=1334 chunks=3 sha256=0e6435da...6e86, which matches the Log. /plan: eta_s 1844.4 <= ceiling_s 3029.6 = fastest_eta_s 1529.6 + budget 1500 s. Follow-ups T-0400 and T-0401 are in queue/backlog/ on origin/main. The diff against origin/main touches only this task file. QUEUE OK (391 tasks). The task branch is behind origin/main by efbb58e9, which only files T-0400/T-0401 in the queue (drift OK). Released queue/LOCKS/prod.lock (held by T-0395).

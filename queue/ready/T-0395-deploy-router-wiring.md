---
id: T-0395
title: Deploy the router wiring (T-0391's ROUTER_URL and GRAPH_VERSION) and prove one live /plan plus ops/sane --prod
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [prod]
touches: [ops/api-url, queue/]
pins_affected: []
reviewer: null
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

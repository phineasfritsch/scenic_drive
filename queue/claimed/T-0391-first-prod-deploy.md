---
id: T-0391
title: First production deploy of scenic-api from main (pilot backend) - ops/deploy, live /__version == HEAD, /__health quoted
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T10:49:37Z
lease_expires_at: 2026-10-18T10:49:37Z
worktree: .worktrees/T-0391
branch: task/T-0391
exclusive: [prod]
touches: [ops/api-url, queue/, services/api/wrangler.jsonc]
pins_affected: []
reviewer: null
depends_on: [T-0390]
verify: [ops/sane]
acceptance: []
---
## Brief

The owner authorised a production deploy on 2026-10-17. After T-0390 merges, run `bash ops/deploy` from the
main checkout at origin/main. That needs queue/LOCKS/prod.lock, which this task holds. Then:
- Quote the DEPLOYED line, /__version and /__health.
- Run one /plan request that obeys the privacy rule (one coordinate, 2 dp). Expect the routingOffline answer
  until ROUTER_URL points at the VPS.
- Run `ops/sane --prod`, quoting its exit codes. Record what is degraded and why (router not yet up).

A reviewer who is not the owner re-reads the live endpoints and confirms that /__version equals the deployed sha.

## Log
- 2026-10-17 filed by agent/claude-opus-5 after the owner authorised the deploy.
- 2026-10-17T10:49:37Z claimed by agent/claude-opus-5; lease until 2026-10-18T10:49:37Z
- 2026-10-17T11:35:24Z agent/claude-opus-5: DEPLOYED (owner-authorised, prod.lock held): `bash ops/deploy` -> 'DEPLOYED sha=2daea62cdc8247f29516dec88b47379b40bb51f4 live=2daea62cdc8247f29516dec88b47379b40bb51f4 built_at=2026-10-17T10:52:53Z url=https://scenic-api.phineas-fritsch.workers.dev'. /__version {git_sha 2daea62c, schema_version 4}; /__health 200 {ok:true, db:up, kill_switch:false, upstream_calls:0}; /config 200 (supported_regions [la]).
- 2026-10-17T11:35:24Z agent/claude-opus-5: ROUTER (owner chose a local-machine tunnel, hostname scenic-router.phineasfritsch.com): LA graph imported with scenic-routing:t0392 (properties sha256 d802c10291f219e4fbeda1a5501a2c7863df15733231a69e69a94ef17e20acb9); compose project scenic-routing-pilot up in WSL docker with ROUTER_SECRET from an env file outside the repo; Cloudflare Tunnel scenic-router (2c83a32a-6e50-441d-80f2-c97ce7132706, own config file, the owner's jarvis tunnel untouched; a first DNS route mistakenly attached the CNAME to jarvis and was re-pointed with --overwrite-dns). Probes: https://scenic-router.phineasfritsch.com/info without the header 401, with the placeholder 401, with the secret 200 graph_hash d802c102...acb9. Touches widened to services/api/wrangler.jsonc: vars ROUTER_URL=https://scenic-router.phineasfritsch.com and GRAPH_VERSION=<that hash> (neither is a secret). Full Worker suite on this change: 100 files, 2690/2690 passed; the router saw no test traffic (docker logs 0 requests).

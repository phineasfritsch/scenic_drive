---
id: T-0392
title: The router is not servable over HTTP - a GraphHopper web image for the LA graph (with the scenic-score and T-0381 gate plugins) behind a Caddy front door that refuses requests without x-scenic-router-secret
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T07:57:30Z
lease_expires_at: 2026-10-18T07:57:30Z
worktree: .worktrees/T-0392
branch: task/T-0392
exclusive: [routing-profiles]
touches: [services/routing/, ops/deploy-routing, ops/lib/, ops/sane]
pins_affected: [P-COST-03, P-PROD-04]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The pilot audit found that services/routing builds only a command-line jar (graphhopper-core; modes import/probe/route/route-details). config.yml has no server: section, and nothing serves /route, /isochrone or /info over HTTP. Nothing checks the Worker's x-scenic-router-secret either: the plan's P-COST-03 says 'VPS refuses requests without the Worker secret'. Until this exists the Worker's /plan answers 503 routingOffline.

Build, following the pattern services/search already uses:
- a GraphHopper web server image pinned by digest that loads the same plugins (scenic-score parser, T-0381 GateFactParser) and serves the LA graph built from the same config.yml and profiles;
- a docker compose service;
- a Caddy front door that returns 401/403 without the secret header, and also 401 for the literal placeholder. The secret comes from the environment and is never committed;
- /info exposing the graph hash (P-PROD-04).

The Worker's routerClient must work against it unchanged: measure the exact paths and headers it sends and match them. Prove locally in WSL docker:
- the LA graph imports;
- a /route through Caddy with the header returns a route;
- the same request without the header is refused;
- /info carries the hash.
Quote each container stage's count lines into the Log as the stage lands.

ops/deploy-routing must deploy this compose to a host given by environment variables. Do not run it against any real host: the owner provides the VPS. Write the owner's exact VPS steps (docker install, firewall to Cloudflare ranges plus owner IP, compose up, secret env) in services/routing/README.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the pilot runbook audit (owner authorised the pilot backend 2026-10-17).
- 2026-10-17T07:57:30Z claimed by agent/claude-opus-5; lease until 2026-10-18T07:57:30Z

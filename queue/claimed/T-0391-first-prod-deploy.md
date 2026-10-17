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
touches: [ops/api-url, queue/]
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

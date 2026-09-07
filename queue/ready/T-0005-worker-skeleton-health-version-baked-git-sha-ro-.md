---
id: T-0005
title: Worker skeleton: /__health, /__version (baked git SHA), /__ro; ops/deploy; ops/prod-read
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/, ops/deploy, ops/prod-read]
pins_affected: [P-COST-02]
reviewer: null
depends_on: [T-0001]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "cd services/api && npm test -> vitest JSON report; ops/test now shows the vitest count in linux="
  - "ops/deploy refuses when HEAD is not on origin (RED), then prints DEPLOYED sha=<40hex> live=<same> ... exit 0"
  - "ops/prod-read REPLACE INTO x VALUES(1) -> refused, exit 1 (RED); ops/prod-read SELECT 1 -> 1"
  - "curl $API/__version -> {git_sha: <HEAD>, built_at: ...}"
---
## Brief

Cloudflare Worker (TypeScript, wrangler, vitest + @cloudflare/vitest-pool-workers). No business routes yet.
/__ro accepts only ^(EXPLAIN (QUERY PLAN )?)?(SELECT|WITH)\b single statements against D1. GIT_SHA baked at deploy.
Needs the Cloudflare account + a D1 database + a GitHub origin (deploy refuses otherwise - that is the red).

## Log

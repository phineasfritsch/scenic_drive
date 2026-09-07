---
id: T-0005
title: Worker skeleton: /__health, /__version (baked git SHA), /__ro; ops/deploy; ops/prod-read
state: claimed
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: 2026-09-07T03:38:33Z
lease_expires_at: 2026-09-07T07:38:33Z
worktree: ../wt/T-0005
branch: task/T-0005
exclusive: [prod]
touches: [services/api/, ops/deploy, ops/prod-read, ops/lib/ro_grammar.py, ops/lib/ro_cases.json, ops/test, ops/api-url]
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
- 2026-09-07T03:38:33Z claimed by agent/claude-opus-5; lease until 2026-09-07T07:38:33Z
- 2026-09-07T04:50:00Z scope note: touches widened - ops/lib/ro_grammar.py + ro_cases.json are the Python mirror of the Worker grammar (shared case list); ops/test gained the vitest tier CR fix (Python on Windows emits CRLF into the count line); ops/api-url is written by ops/deploy.
- 2026-09-07T03:50:38Z took exclusive [prod] for the first deploy; queue/LOCKS/prod.lock created

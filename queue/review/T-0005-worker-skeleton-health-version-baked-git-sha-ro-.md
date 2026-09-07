---
id: T-0005
title: Worker skeleton: /__health, /__version (baked git SHA), /__ro; ops/deploy; ops/prod-read
state: review
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: 2026-09-07T03:38:33Z
lease_expires_at: 2026-09-07T07:38:33Z
worktree: ../wt/T-0005
branch: task/T-0005
exclusive: [prod]
touches: [services/api/, ops/deploy, ops/prod-read, ops/lib/ro_grammar.py, ops/lib/ro_cases.json, ops/test, ops/api-url, pins/PINS.yaml]
pins_affected: [P-COST-02]
reviewer: agent/reviewer-1
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
- 2026-09-07T03:52:00Z GREEN: npm test 34/34 in the Workers pool; ops/test -> TESTS linux=37/3 OK; python ops/lib/ro_grammar.py --self-test -> RO-GRAMMAR OK 26 cases
- 2026-09-07T03:52:00Z RED: ops/test with a broken vitest.config.ts -> FAIL: services/api exists but vitest produced no report, exit 1
- 2026-09-07T03:52:00Z RED: ops/deploy with HEAD not on origin -> DEPLOY REFUSED, exit 1; with no prod.lock -> DEPLOY REFUSED, exit 1
- 2026-09-07T03:52:00Z DEPLOYED sha=f75eddb175b46058ba7417f0c2bce5c1a813d7e8 live=f75eddb175b46058ba7417f0c2bce5c1a813d7e8 url=https://scenic-api.phineas-fritsch.workers.dev (D1 scenic 5f475f94-9fd3-4902-9f6e-022c6db30544 created; RO_TOKEN secret set; token lives in services/api/.env.ro, gitignored)
- 2026-09-07T03:52:00Z GREEN: ops/prod-read --health shows live sha == HEAD; ops/prod-read SELECT 1 AS one -> 1
- 2026-09-07T03:52:00Z RED: ops/prod-read REPLACE INTO ... -> refused locally, exit 1; wrong token -> HTTP 401, exit 1; WITH...INSERT sent straight to /__ro via curl -> refused: write keyword INSERT
- 2026-09-07T03:52:00Z fix: prod-read sends an explicit User-Agent (Cloudflare 1010 blocks python-urllib default)
- 2026-09-07T03:52:00Z P-COST-02 pending repointed from T-0005 to the new quota task T-0014 (this task never owned that constant); pins/PINS.yaml added to touches
- 2026-09-07T03:52:00Z prod.lock released; moved to review/, reviewer agent/reviewer-1

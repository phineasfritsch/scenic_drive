---
id: T-0393
title: Nothing fills D1 places - every corpus place id the app sends is 404 unknown_place; ship an ops/seed-places that loads the corpus places table into D1 from the same commit
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/, services/api/test/, services/api/migrations/, services/etl/etl/, services/etl/tests/]
pins_affected: [P-PROD-05]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The pilot audit found that the Worker resolves place ids against D1 places (migration 0001), and nothing writes that table: there is no ops/publish-corpus and no seeding. Every Surprise, plan-to-place or trip request with a corpus place id answers 404 unknown_place in production.

MEASURE first:
- which Worker routes read places;
- the D1 places schema against the corpus places table (the app's bundled corpus-fallback.sqlite and the LA corpus built by the region build);
- the row count.

Then RULE the source of truth (the corpus from the same commit as the app; schema_version must match) and write ops/seed-places. It should export the corpus places into idempotent, chunked SQL for `wrangler d1 execute --remote`, with a --dry-run mode that prints the row count and a sha256 of the canonical rows.

Test the exporter through its shipped entry point: a fixture corpus is exported, the SQL is applied to a local D1 (vitest/miniflare), and the rows are read back and compared whole. Re-running must leave the same rows. Never run it against the remote database in this task. The orchestrator runs it once the PR merges, under the owner's authorisation.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the pilot runbook audit (owner authorised the pilot backend 2026-10-17).

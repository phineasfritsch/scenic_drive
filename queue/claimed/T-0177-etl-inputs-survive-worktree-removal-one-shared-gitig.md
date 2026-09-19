---
id: T-0177
title: ETL inputs survive worktree removal - one shared gitignored inputs directory outside .worktrees/, and the fetcher and the extract read it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T01:02:12Z
lease_expires_at: 2026-09-19T09:02:12Z
worktree: .worktrees/T-0177
branch: task/T-0177
exclusive: []
touches: [services/etl/etl/fetch.py, services/etl/etl/manifest.py, services/etl/tests/, ops/etl-fetch-inputs, ops/etl-extract, .gitignore, queue/README.md]
pins_affected: []
reviewer: null
depends_on: [T-0169]
verify: [ops/test, ops/check-pins]
acceptance:
  - "`python -m etl.fetch` and `ops/etl-fetch-inputs` resolve the inputs directory to ONE path shared by every worktree (the main checkout's services/etl/inputs/, or an env var SCENIC_ETL_INPUTS documented in queue/README.md), never <worktree>/services/etl/inputs/; RED by name: a test that runs the resolver from a fake worktree path and asserts the shared path, red today"
  - "`--verify-only` over the shared directory is the acceptance for every task that consumes an input; the verified line quoted"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From the 17:13 panel (STRATEGY, grounded). T-0169 fetched and verified the 1,328,688,632-byte California extract
into `.worktrees/T-0169/services/etl/inputs/` (gitignored); the worktree was removed with `--force` the hour
PR #99 merged and the deliverable went with it. Only an unverifiable 2026-09-08 build survives as hardlinks in
two old worktrees. T-0168 starts with a second 7m43s fetch. Rule: inputs live in ONE gitignored directory
outside `.worktrees/` (`fetch.py`'s `DEST = ROOT / "inputs"` is per-worktree today), the fetcher and
`ops/etl-extract` read it, and `queue/README.md` says so. Not a symlink farm (Windows).

## Log
- 2026-09-19T00:40:47Z filed by agent/claude-fable-5-1 from the 17:13 panel's grounded synthesis. Not started.
- 2026-09-19T01:02:12Z claimed by agent/claude-opus-5; lease until 2026-09-19T09:02:12Z

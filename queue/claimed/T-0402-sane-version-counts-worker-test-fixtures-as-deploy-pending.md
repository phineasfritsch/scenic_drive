---
id: T-0402
title: ops/sane --prod exit 3 counts a services/api/test fixture change as a pending deploy - compare only the files the deployed Worker is built from
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T17:18:06Z
lease_expires_at: 2026-10-18T17:18:06Z
worktree: .worktrees/T-0402
branch: task/T-0402
exclusive: []
touches: [ops/sane, ops/lib/, queue/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Measured 2026-10-17 (T-0395): after T-0393 merged (c6f2da75) with only new files under
services/api/test/fixtures/seed-places/, `ops/sane --prod` printed
`version FAIL services/api changed since live 5e4150a0 -> deploy pending: services/api/test/fixtures/seed-places/places-0001.sql ...`
and exited 3. Nothing the deployed Worker is built from had changed. ops/sane:77 runs
`git diff --quiet "$live" "$head" -- services/api ops/deploy`, so every test file, fixture and README counts.

Fix by WHITELIST, not by excluding test/: the version row compares only the paths the bundle is built from
(what wrangler bundles - services/api/src/, wrangler.jsonc, package.json, package-lock.json, tsconfig - plus
ops/deploy). Read the list from wrangler's own config/entry, or pin it, so that a new source directory cannot be
missed silently. Demonstrate on a scratch repo or with a fixture git history: a fixture-only change -> ok; a
src/ change -> exit 3; a wrangler.jsonc var change -> exit 3; an unlisted new top-level directory under
services/api that wrangler bundles -> exit 3 (fail closed). Each shown red on today's ops/sane, then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0395's ops/sane --prod run.
- 2026-10-17T17:18:06Z claimed by agent/claude-opus-5; lease until 2026-10-18T17:18:06Z

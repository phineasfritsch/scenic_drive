---
id: T-0344
title: ops/sane --prod gains its reserved exit codes 6 (quota / kill switch tripped or near its trip) and 8 (the R2 corpus/tiles manifests disagree with this checkout's config), read-only, against the deployed Worker's own read-only endpoints
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/sane, ops/lib/, ops/mutate/, services/api/src/, services/api/test/, pins/PINS.yaml]
pins_affected: [P-OPS-05, P-COST-01, P-COST-02, P-PROD-05]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

The plan's harness table: `ops/sane [--prod]` exit 6 = quota/kill switch, 8 = R2 manifest != config. ops/sane reserves
both ("5/6/8 reserved ... added with T-0008/T-0014"); exit 5 (golden routes live against the router) needs the
deployed router and stays out of scope here. MEASURE FIRST: what the deployed Worker exposes read-only today
(/__health, /__version, /config, /__ro - which of them can answer "is KILL set / how close is the monthly upstream
counter to MAX_MONTHLY_UPSTREAM_CALLS" and "which corpus/tiles manifest version is live" without a new write path),
what this checkout's config pins (corpus schema_version, tiles manifest, MAX_MONTHLY_UPSTREAM_CALLS), and how
ops/sane's EXIT_ORDER / check-sane-exit-order (P-OPS-05) must move. Then write the acceptance: each new check seen
red then green against a LOCAL fake Worker (never prod from CI; never a deploy), EXIT_ORDER updated with P-OPS-05
seen red then green, never mutates, distinct exit codes, a near-trip threshold ruled (e.g. 90% as the plan's kill
switch). If the Worker lacks a read-only field the check needs, add it read-only (no location data, P-PRIV-05) with
a whole-answer test.

## Log
- 2026-10-09T13:50:14Z filed by agent/claude-opus-5 (orchestrator) from the plan's harness table (M1 ops/sane 6/8).

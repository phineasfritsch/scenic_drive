---
id: T-0302
title: Worker /ledger - a signed-in device records which Surprise places it was shown (place id + H3-5 cell + UTC day) and reads back its last 90 days, so the 90-day no-repeat survives reinstall; nothing finer than H3-5 is ever stored
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T15:53:34Z
lease_expires_at: 2026-10-08T05:53:34Z
worktree: .worktrees/T-0302
branch: task/T-0302
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/migrations/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-PRIV-04, P-PRIV-05, P-COST-01]
reviewer: null
depends_on: [T-0287, T-0278]
verify: [ops/check-pins]
acceptance:
  - "RULE FIRST in a dated Log entry: identity (the session JWT sub only - no session, no ledger: 401), the row shape (user, place_id, h3_5 cell, UTC day - migration 0008, no timestamp finer than a day, no coordinate), the 90-day window and retention (rows older than 90 days deleted on write), quota/kill-switch exemption (D1 only, no upstream - ruled like /waitlist T-0293 R8), and that DELETE /account removes every ledger row for the user (P-PRIV-04)"
  - "POST /ledger {place_id, cell} validates by whole-body whitelist (place id shape from the corpus, cell = a valid H3 resolution-5 id) and writes one row per (user, place, day) idempotently; GET /ledger returns exactly the caller's rows within 90 days by full equality; another user's rows never appear - table through worker.fetch with rows as functions of the user variant and a meta-test no row ignores it"
  - "Range table over the window: a row at exactly 90 days is returned, at 90 days + 1 is not and is deleted on the next write; every bound by the day boundary at 23:59:59.999Z / 00:00:00.000Z"
  - "P-PRIV-05 DDL test extended to the new table (seen red with a forbidden column); P-PRIV-04 deletion test extended (seen red with the ledger delete removed); every ROUTES-enumerating table extended for /ledger (memory parallel-worker-prs-conflict); new PINS.yaml values double-quoted (memory pins-yaml-strict)"
  - "A mutation population entry per validation branch, the window bound and the user scoping, with a literal floor; three MISSED before and CAUGHT by name after"
---
## Brief

Plan, Surprise Me: "Unlimited, 90-day no-repeat"; Worker list: "ledger (place ids + H3-5)". Today the no-repeat history
lives only on the device (Sources/ScenicKit/Surprise/SurpriseHistory.swift), so a reinstall forgets it. Privacy: the
server never holds a coordinate or anything finer than an H3-5 cell (plan, Telemetry and Worker rows).

## Log
- 2026-10-07T15:50:09Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 ledger).
- 2026-10-07T15:53:34Z claimed by agent/claude-opus-5; lease until 2026-10-08T05:53:34Z

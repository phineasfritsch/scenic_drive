---
id: T-0296
title: POST /waitlist counts one device once per cell per day - a rate limit so anyone cannot inflate a cell's count
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/waitlist.ts, services/api/test/, services/api/migrations/]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0293]
verify: [ops/check-pins]
acceptance:
  - "RULE FIRST: the identity a waitlist write is bound to (the attested session / install id the quota already uses), and how a per-device-per-cell-per-day dedupe is stored without keeping the device id next to the cell (e.g. a keyed hash that expires daily) - P-PRIV-05 DDL test extended"
  - "Through worker.fetch: the same device posting the same cell twice in one UTC day increments once; a second device increments again; the next day increments again - full-equality table"
  - "Population entries for the dedupe key and the day boundary, MISSED before and CAUGHT by name after"
---
## Brief

T-0293 author stillOpen 4 (PR #182): /waitlist has no rate limit, so anyone can inflate a cell's count. The waitlist
must stay free of personal data (memory user-lives-in-la; plan Launch scope).

## Log
- 2026-10-07T07:17:54Z filed by agent/claude-opus-5 (orchestrator) from T-0293's stillOpen 4.

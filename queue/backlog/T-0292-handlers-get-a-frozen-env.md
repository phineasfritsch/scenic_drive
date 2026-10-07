---
id: T-0292
title: Handlers get a frozen env and the kill-switch tables run on a shared-env worker after an authenticated sweep - request-time shared-state patches cannot unpause anything
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/index.ts, services/api/test/]
pins_affected: [P-COST-01]
reviewer: null
depends_on: [T-0288]
verify: [ops/check-pins]
acceptance:
  - "default.fetch hands every handler a frozen env (Object.freeze of a per-request copy, or the binding object frozen once); a test through worker.fetch shows a handler's attempt to delete or assign env.KILL throws or has no effect on the next request, by name"
  - "the P-COST-01 kill table and the /config table run on ONE worker sharing ONE env object after a sweep that includes authenticated requests with bound fakes (D1, KV, Analytics Engine, the router), under every KILL source - full equality"
  - "population entries: a handler that deletes env.KILL on its first call, and one gated on an authenticated path - MISSED before, CAUGHT by name after"
---
## Brief

rv5-t0288 recordable (PR #177 sign-off): the sweep builds a new env per call, but workerd hands one env object to every
request in an isolate, so a handler that mutates env is never exercised; and the sweep's well-formed requests are not
authenticated, so a patch gated on an authenticated or bound-env path never fires (owner residual R10). Memory
runtime-read-recorder.

## Log
- 2026-10-07T02:08:18Z filed by agent/claude-opus-5 (orchestrator) from rv5-t0288's recordable on PR #177.

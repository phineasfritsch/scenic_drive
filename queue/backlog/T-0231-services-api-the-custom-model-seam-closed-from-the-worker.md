---
id: T-0231
title: services/api - the custom-model seam closed from the Worker side: a vitest case re-emits Tests/Fixtures/custom-model/lambda-*.json from buildCustomModel and diffs byte for byte (today only the Swift side is bound, so a customModel.ts edit ships a Worker/CLI divergence green)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/test/, Tests/Fixtures/custom-model/]
pins_affected: []
reviewer: null
depends_on: [T-0182]
verify: [ops/test, ops/check-pins]
acceptance:
  - "services/api/test/customModel.test.ts gains a case that reads every Tests/Fixtures/custom-model/lambda-*.json and asserts JSON.stringify(buildCustomModel(lambda, null), null, 2) + a trailing newline equals the committed bytes; RED first by editing customModel.ts (a mutated multiplier), then green; PROVENANCE.txt's 'a change on either side fails it by name' corrected to what each test actually does; the re-record procedure ruled (the Worker is canonical; both sides re-emitted in one commit reviewed by a different agent)"
  - "the vitest count line under ops/test's TS tier (no new toolchain - services/api/test already runs there); queue-check bare"
---
## Brief

From the 14:13 panel (CODE, grounded): LambdaCustomModelParityTests compares the Swift output to committed bytes only,
and nothing under services/api/test reads the fixtures. If rv1-pr124 makes the fixer close this inside PR #124, close
this task as done-by-#124 with a Log line.

## Log
- 2026-09-19T21:54:54Z filed by agent/claude-opus-5[1m] (14:13 panel, grounded on pins/floor_*.txt, T-0203 Log :34, queue.py:541-548, RouteScore.swift:92-94). Not started; conditional on rv1-pr124 recording rather than blocking.

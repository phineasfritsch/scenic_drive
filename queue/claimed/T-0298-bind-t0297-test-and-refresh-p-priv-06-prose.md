---
id: T-0298
title: P-COST-01 binds T-0297's shared-binding kill test by name, and P-PRIV-06's T-0296 prose matches the 18-step sequence
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T13:46:52Z
lease_expires_at: 2026-10-07T21:46:52Z
worktree: .worktrees/T-0298
branch: task/T-0298
exclusive: []
touches: [ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-06]
reviewer: null
depends_on: [T-0296, T-0297]
verify: [ops/check-pins]
acceptance:
  - "ops/lib/named-tests.json P-COST-01 gains the T-0297 test in services/api/test/sharedEnvWorker.test.ts ('the kill read is not reachable through a shared binding (T-0297, P-COST-01) > a handler that assigns env.KILL_SWITCH.get = ...' - copy the exact full name from the file); run-named-tests P-COST-01 passes 37/37; seen RED by name with T-0297's mutant attest-real-binding-kill-get-patched applied (configMutants.mjs) then green"
  - "pins/PINS.yaml P-COST-01 prose appends a dated sentence for the new binding and the new count (append-only: never rewrite earlier dated sentences - memory never-edit-dated-record-output); P-PRIV-06's T-0296 clause gains an appended correction sentence: the sequence is 18 steps over {empty, holding} x {session-only, legacy-headers}, and a bare legacy header with the secret set counts under IDENTITY_HEADERS=1"
---
## Brief

rv1-t0297 recordable (a) and T-0297 owner R6 (PR #186): the new test is not bound by name because named-tests.json and
PINS.yaml were outside T-0297's touches. rv2-t0296 recordable (PR #185): P-PRIV-06's T-0296 clause still says
"a thirteen-step sequence". Wording and binding only; no src or test change.

## Log
- 2026-10-07T13:45:30Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0297 and rv2-t0296 recordables.
- 2026-10-07T13:46:52Z claimed by agent/claude-opus-5; lease until 2026-10-07T21:46:52Z

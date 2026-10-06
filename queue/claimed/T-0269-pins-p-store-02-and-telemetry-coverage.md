---
id: T-0269
title: register P-STORE-02 (refund/expiry/revoke turn the entitlement off) over T-0267's /asn tests, and bind the Telemetry row-coverage test under P-PRIV-05
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T00:29:02Z
lease_expires_at: 2026-10-06T12:29:02Z
worktree: .worktrees/T-0269
branch: task/T-0269
exclusive: []
touches: [pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-STORE-02, P-PRIV-05]
reviewer: null
depends_on: [T-0261, T-0265, T-0267]
verify: [ops/test, ops/check-pins]
acceptance:
  - "pins/PINS.yaml gains P-STORE-02 (statement in the plan's words: /asn sets the entitlement inactive on EXPIRED/REFUND/REVOKE; runs_on linux; anchor api) asserted by run-named-tests.py over the named services/api/test/asnState.test.ts tests for EXPIRED, REFUND, REVOKE, GRACE_PERIOD_EXPIRED, the out-of-order no-regress case and the read-after-REFUND case, plus the asnVerify defect table (a forged notification changes nothing); each binding RED by a one-line mutant of src/ (REFUND mapped active; the signedDate guard >= ; readEntitlement ignoring status) quoted in the Log, then green"
  - "P-PRIV-05 binds TelemetryTests.TelemetryEventEncodingTests/fourteenEventsEachWithARow() (rv2-t0265's recordable: its every-kind-has-a-row expectation is the coverage half of the whitelist clause), shown RED by the rv2 variant (a Double payload plus its row deleted) through run-named-tests P-PRIV-05; prose changes APPENDED with dates, never rewritten"
---
## Brief

T-0267 stillOpen (a): P-STORE-02 does not exist in PINS.yaml; T-0265 rv2 recordable: the Telemetry row-coverage test
is unbound. Both are pins-only bindings over shipped tests (the T-0261/T-0264 pattern).

## Log
- 2026-10-06T00:26:49Z filed by agent/claude-opus-5 (orchestrator) after PR #158 (T-0267) merged.
- 2026-10-06T00:29:02Z claimed by agent/claude-opus-5; lease until 2026-10-06T12:29:02Z

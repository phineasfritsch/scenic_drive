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
- 2026-10-06T00:38:33Z RULING before code (agent/claude-opus-5, owner). Every disagreement between plan, Brief, acceptance and code, ruled here; touches stay pins/PINS.yaml and ops/lib/named-tests.json (plus this task file).
  - Plan vs acceptance, statement: the plan's row (plan line 267) reads `/asn` sets entitlement inactive on EXPIRED/REFUND/REVOKE | Worker test | linux. The PINS statement copies those words; GRACE_PERIOD_EXPIRED (the fourth entry of the shipped DEACTIVATES in src/asnNotification.ts) is bound as a test the acceptance names but is not added to the statement.
  - Row schema, copied from the existing anchor: api row P-COST-01: id, statement, why_no_test_catches_it, anchor: api, runs_on: [linux], assertion "\"${PYTHON:-$(command -v python3 || command -v python)}\" ops/lib/run-named-tests.py P-STORE-02", owner: agent/claude-opus-5, added: 2026-10-06. Appended after P-PROD-02 (the file's last row).
  - P-STORE-02 test list (vitest only, no swift key; names copied from the vitest JSON report of services/api on 7196d40, every one passed): asnState.test.ts SEVEN - "deactivating types set the row inactive > EXPIRED -> inactive", "... > REFUND -> inactive", "... > REVOKE -> inactive", "... > GRACE_PERIOD_EXPIRED -> inactive"; "replay and out-of-order delivery never regress state (R6) > an older SUBSCRIBED after a newer EXPIRED leaves the row inactive" and "... (R6) > a notification with the stored signedDate (a replay) changes nothing"; "GET /entitlement through the shipped ROUTES (R8) > after REFUND the token is inactive". asnVerify.test.ts FIFTY-FOUR - the 51 DEFECTS rows of "every signedPayload defect is 400 with zero state change (shipped handleAsn)", that describe's two sibling tests (a body that is not JSON; a body without signedPayload), and "the shipped ROUTES['/asn'] pins Apple's root > a chain valid in every respect but its self-made root is 400 through ROUTES with zero state change" (the one forged-notification test driving the shipped ROUTES entry). SIXTY-ONE in all. Shipping symbol: the asnState writes go through the shipped handleAsn (test/asnHarness.ts), the R8 read through ROUTES['/entitlement'].
  - Disagreement, acceptance vs code: the acceptance pairs "the signedDate guard >=" with "the out-of-order no-regress case", but that test sends signedDate NOW-1 after NOW, which `>=` refuses exactly as `>` does - it cannot go red under that mutant. The test the mutant reaches is the R6 replay test (equal signedDate), so both R6 tests are bound; the out-of-order test is bound for its own regress clause, not claimed red by `>=`.
  - Disagreement, acceptance vs acceptance: none of the three named mutants (REFUND mapped active; the guard `>=`; readEntitlement ignoring status) touches a defect-table row, so "each binding RED" needs a fourth. Ruled: the one-line mutant src/appleJws.ts `if (header.alg !== "ES256") reject("alg is not ES256");` -> `if (false) reject("alg is not ES256");`, expected to redden the alg rows by name.
  - Mutant sites, exactly: REFUND mapped active = src/asnNotification.ts `ACTIVATES.includes(type) || grace ?` -> `ACTIVATES.includes(type) || grace || type === "REFUND" ?`; the guard = src/entitlementStore.ts `WHERE excluded.signed_date > entitlements.signed_date` -> `>=`; readEntitlement ignoring status = src/entitlementStore.ts `r.status === "active" && (r.active_until === null || nowMs < r.active_until)` -> `(r.active_until === null || nowMs < r.active_until)`.
  - P-PRIV-05: its swift tests list gains "TelemetryTests.TelemetryEventEncodingTests/fourteenEventsEachWithARow()"; the filter already selects TelemetryEventEncodingTests and is unchanged; TWENTY-TWO -> TWENTY-THREE. RED by rv2-t0265's variant C: Sources/Telemetry/TelemetryEvent.swift `case corpusActivated(version: Int)` -> `version: Double` plus deleting the `(.corpusActivated(version: 7), ...)` row from TelemetryEventEncodingTests.rows (the variant that printed passed=22/22 exit 0 under rv2); expected passed=22/23 exit 1 with fourteenEventsEachWithARow() FAILED by name. The P-PRIV-05 prose gets one dated sentence APPENDED; nothing in it is rewritten.
  - Mutants are applied in the worktree and reverted with git checkout of the one src file; no src or Tests file is committed.

---
id: T-0375
title: P-PRIV-05 binds everyRequestStampsTheProvidersCurrentID() by name, so deleting the per-request install-id test is caught, not only weakened inside the suite filter
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T09:15:21Z
lease_expires_at: 2026-10-17T09:15:21Z
worktree: .worktrees/T-0375
branch: task/T-0375
exclusive: []
touches: [ops/lib/named-tests.json, pins/PINS.yaml, queue/]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0367]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0367 (PR #254) moved the per-request install-id read into Sources/Telemetry and added
TelemetryClientTests.everyRequestStampsTheProvidersCurrentID() (rows: same id, id changed after a post, id changed
while a post is in flight). It runs inside P-PRIV-05's named swift filter, but its NAME is not in
ops/lib/named-tests.json, so deleting it leaves `run-named-tests.py P-PRIV-05` green (T-0367 R4: pins/ was outside
touches). Bind it by name, re-approve whatever PINS.yaml digest or count P-PRIV-05 carries, and show the binding
red by deleting the test (run-named-tests reports it MISSING) then green.

## Log
- 2026-10-16T09:40:00Z filed by agent/claude-opus-5 (orchestrator) from T-0367 R4 / rv2-t0367 (ids checked on main
  and task/T-0318, task/T-0368: highest T-0374).
- 2026-10-16T09:15:21Z claimed by agent/claude-opus-5; lease until 2026-10-17T09:15:21Z
- 2026-10-16T09:16:43Z MEASURED on task/T-0375 at 7fb516e2 (main + queue commits):
  M1 ops/lib/named-tests.json `P-PRIV-05` has keys [vitest, swift]; vitest binds 37 names; swift `filter` already
  runs `TelemetryTests\\.(...|TelemetryClientTests)`, and `tests` binds 37 distinct names, five of them
  TelemetryClientTests (everyEventPostsExactlyItsRequest(), waitingBoundTable(waiting:), everyOutcomeDropsTheBatch(),
  capacityIsTheWorkersCap(), recordedOnlyAfterTheFirstPostReturns()). `everyRequestStampsTheProvidersCurrentID` occurs
  in no line of named-tests.json or PINS.yaml; it is declared at Tests/TelemetryTests/TelemetryClientTests.swift:110
  as `@Test func everyRequestStampsTheProvidersCurrentID() async throws`, so its xunit identifier is
  `TelemetryTests.TelemetryClientTests/everyRequestStampsTheProvidersCurrentID()`.
  M2 P-PRIV-05's `assertion` is check-telemetry-emit-sites.py && check-learned-speeds-sites.py &&
  run-named-tests.py P-PRIV-05 - no check-named-table.py, so the pin carries NO digest and no machine-checked count.
  Its only recorded count is prose in `why_no_test_catches_it`, last sentence T-0365: "the row binds 37 Swift tests".
- 2026-10-16T09:16:43Z RULINGS (author rule, before code):
  R1 Brief "re-approve whatever PINS.yaml digest or count P-PRIV-05 carries" vs M2: there is no digest to re-approve.
  The count lives only in why_no_test_catches_it, so this task appends one dated T-0375 sentence there (the row binds
  38 Swift tests; seen RED/green as below) and edits no earlier sentence.
  R2 Adding check-named-table.py to P-PRIV-05 (a digest over the entry) is NOT done here: the Brief does not ask for
  it, and T-0318 (in flight) may edit P-PRIV-05's vitest rows, which would make two branches re-approve one digest.
  It is recorded as still open: a row dropped from P-PRIV-05's table, with the test, stays green.
  R3 On this Windows box UserStorePrivacyTests is GRDB-gated and does not build, so run-named-tests reports
  `PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail()` MISSING and exits 1 everywhere here (pin
  text, T-0290). Green on this box therefore means: every name passed except that one, which is MISSING; CI's Linux
  core job is the whole green. Red means the bound test is reported MISSING BY NAME in addition.

## Acceptance
1. `ops/lib/named-tests.json` P-PRIV-05 `swift.tests` contains
   `TelemetryTests.TelemetryClientTests/everyRequestStampsTheProvidersCurrentID()` exactly once; 38 distinct swift
   names; the filter and the vitest half are unchanged (`git diff origin/main -- ops/lib/named-tests.json` is that
   one added line plus its preceding line's comma).
2. pins/PINS.yaml P-PRIV-05 `why_no_test_catches_it` ends with a dated T-0375 sentence recording the binding and
   "38 Swift tests"; no other field and no earlier sentence changes; `python ops/lib/check-pins-yaml.py` exit 0.
3. Seen RED by name: with `everyRequestStampsTheProvidersCurrentID()` deleted from TelemetryClientTests.swift (not
   committed), `SCENIC_SWIFT_SCRATCH=.build/t0375 python ops/lib/run-named-tests.py P-PRIV-05` reports that name
   MISSING (beside the R3 environment MISSING) and exits 1; under the pre-binding table the same deletion does NOT
   name it (the gap). The file is then restored and its sha256 equals the committed blob's.
4. GREEN: the same command on the restored tree reports the bound name passed; the only non-pass is R3's
   UserStorePrivacyTests MISSING.
5. Gates: `python ops/lib/check-pins-yaml.py`, `bash ops/queue-check`, `python ops/lib/check-mutate-population.py`
   exit 0 on the merged head.

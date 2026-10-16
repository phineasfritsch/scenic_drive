---
id: T-0371
title: surprise_not_this has no wire reason for the card's fourth button, Wrong time - it sends nothing today
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T12:56:50Z
lease_expires_at: 2026-10-17T12:56:50Z
worktree: .worktrees/T-0371
branch: task/T-0371
exclusive: []
touches: [Sources/Telemetry/, Tests/TelemetryTests/, Tests/Fixtures/t0279/, services/api/, apps/ios/Packages/ScenicApp/Sources/PlanAdapter/, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: agent/rv1-t-0371
depends_on: [T-0361]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0361 (M6/R5): SurpriseFeedback.Reason has four cases and the card four buttons; Telemetry's SurpriseNotThisReason
has three (too_far, been_there, not_my_thing). PlanAdapter's LiveMoments sends nothing for `.wrongTime`. Rule whether
the closed list gains `wrong_time` (Telemetry enum + the Worker's accepted labels + encoding table rows) or the button
stays unreported, and record it.

## Log
- 2026-10-16T02:32:24Z filed by agent/claude-opus-5 (T-0361 owner) from T-0361 R5.
- 2026-10-16T12:56:50Z claimed by agent/claude-opus-5; lease until 2026-10-17T12:56:50Z
- 2026-10-16T13:01:00Z MEASURED on task/T-0371 = main da28b745 (git grep over the tree, queue/done excluded):
  - `ScenicKit.SurpriseFeedback.Reason` (Sources/ScenicKit/Surprise/SurpriseFeedback.swift:5-9) has 4 cases:
    tooFar, notMyThing, beenThere, wrongTime. The card renders all four (FeatureSurpriseMe/SurpriseNotThis.swift:21
    `button(.wrongTime)`, :52 `"Wrong time"`).
  - `Telemetry.SurpriseNotThisReason` (Sources/Telemetry/SurpriseNotThisReason.swift) has 3: too_far, been_there,
    not_my_thing. `LiveMoments.wire(_:)` returns `SurpriseNotThisReason?` and `case .wrongTime: return nil`;
    `report` does `guard let wire = Self.wire(reason) else { return }` - Wrong time sends nothing.
  - Worker `TELEMETRY_WIRE.surprise_not_this.labels` (services/api/src/telemetryPoint.ts:40) = the same 3;
    telemetryWhitelist.test.ts LABELS (:48) = the same 3, REFUSED keeps `surprise_not_this` "other" (:121) and S2
    derives every proper prefix of every label as a refused row.
  - Tests/Fixtures/t0279/datapoints.jsonl: 36 lines, 3 `surprise_not_this` lines (12 been_there, 27 too_far, 28
    not_my_thing). TelemetryWireFixtureTests pins 36 (`lines.count == 36`); telemetryFixture.test.ts pins 36 twice
    (`FIXTURE_LINES.length` and `dailyTelemetry(36)`) and holds the fixture's labels EQUAL to TELEMETRY_WIRE's.
  - ops/lib/funnel.py STEP_LABELS names no surprise_not_this labels (it reads plan_requested, preview_shown,
    drive_started, post_drive_answer only): the funnel is unaffected either way.
  - P-PRIV-05's named-tests.json entry: 76 names (38 vitest, 38 Swift), digest 4c879f4d...a45; it names tests,
    not label rows, so a new label adds no name by itself.
  - check-telemetry-emit-sites.txt:26 whitelists the LiveMoments site line `            LiveTelemetry.surpriseNotThis(wire)`.
  - Digest rows: Sources/Telemetry/SurpriseNotThisReason.swift in check-safety-disclaimer-linked-digests.txt:352;
    PlanAdapter/LiveMoments.swift in check-safety-disclaimer-pinned:342.
  - mutate-population-allowlist.json:127 allowlists SurpriseNotThisReason.swift as "a closed three-case String enum".
- 2026-10-16T13:01:00Z RULINGS (before code):
  - R1 The closed list GAINS `wrong_time` (`case wrongTime = "wrong_time"`). "Wrong time" is a fixed button, not
    typed text, so it is a closed-enum label like the other three: no free-form string, no coordinate, no instant -
    P-PRIV-05's one-coordinate/2-dp rule and the H3-5 cell rule are untouched (surprise_not_this carries no cell).
    Leaving the button unreported makes the decline funnel undercount by a whole answer class; nothing measured
    argues for that. The owner's pending privacy rule concerns coordinates, not this label.
  - R2 Every layer is compared WHOLE: (a) Swift: a new TelemetryEventEncodingTests test
    `everySurpriseReasonEncodesExactly()` holds `SurpriseNotThisReason.allCases.map { .surpriseNotThis($0).dataPoint }`
    EQUAL to the four labels written out literally, in order, through `point(...)` - a dropped, renamed or extra
    case is red; the encoding table `rows` is not grown (one row per event kind stays its shape). (b) The shared
    fixture gains exactly one line, hand-written (NOT re-recorded with T0279_RECORD=1 - the CLAUDE.md snapshot rule
    is not engaged), and TelemetryWireFixtureTests' byte equality to the shipping encoder is its oracle; 36 -> 37 in
    the Swift and Worker counts. (c) Worker: TELEMETRY_WIRE gains the label; the existing whole-equality test
    "the fixture's wire names and labels are exactly the whitelist's" is the Worker-accepts-exactly-the-Swift-points
    check; LABELS gains `wrong_time` (an accepted row plus its S2 prefix refusals derive from it). Refusal of an
    unknown label is kept ("other") and one row is added: the card's own case spelling `wrongTime` is refused.
  - R3 The iOS layer: `LiveMoments.wire(_:)` becomes TOTAL - returns `SurpriseNotThisReason` (non-optional) from a
    switch with no `default`, `case .wrongTime: return .wrongTime`; `report` keeps the one emit line
    `LiveTelemetry.surpriseNotThis(wire)` byte-identical (emit-sites table unchanged). ScenicApp has no test target
    and PlanAdapter does not build on Linux, so this mapping is held by compile totality (a fifth Reason case or an
    optional return does not compile against `surpriseNotThis(_:)`) and by its sha256 row re-approved in
    check-safety-disclaimer-pinned. Not a numeric module: no mutation population; the allowlist reason for
    SurpriseNotThisReason.swift is reworded three-case -> four-case.
  - R4 The new Swift test is added to P-PRIV-05's named entry (the closed list is the P-PRIV-05 "no free-form
    string" property): count 76 -> 77, digest re-approved in the same diff in PINS.yaml, one appended dated
    sentence in why_no_test_catches_it, no earlier text edited.
  - R5 No Package.swift change is needed (TelemetryTests already depends on Telemetry); serial files untouched.
- 2026-10-16T13:22:20Z RED, by name, tests + fixture line in, src unchanged (fcfff23f + worktree):
  - `swift test --jobs 4 --scratch-path .build/t-0371 --filter TelemetryTests` -> `Test run with 22 tests in 7 suites
    failed after 0.191 seconds with 3 issues`: × "every surprise_not_this reason encodes to its whole data point, the
    four labels and no other" (TelemetryEventEncodingTests.swift:81), × "the fixture names all fifteen wire names and
    holds no row twice" (`(lines.count → 36) == 37`), × "the shared fixture is the Swift encoder's exact JSON for every
    row, by bytes" (`(stored → 3342 bytes) == (bytes ...`).
  - `npx vitest run test/telemetryWhitelist.test.ts test/telemetryFixture.test.ts` -> `Test Files 2 failed (2)`, 4
    failed: × every fixture row is accepted alone ... (`events[0] label is not one of surprise_not_this's`), × the
    whole fixture, in requests of MAX_TELEMETRY_EVENTS_PER_REQUEST ... (`events[8] label is not one of
    surprise_not_this's`), × the fixture's wire names and labels are exactly the whitelist's (`+ "wrong_time"`),
    × every ruled bound and closed-enum edge is accepted and written exactly (row `"surprise_not_this label wrong_time"`).
- 2026-10-16T13:22:20Z GREEN after the src change (enum case, TELEMETRY_WIRE label, LiveMoments total):
  `Test run with 22 tests in 7 suites passed after 0.846 seconds`; vitest `Test Files 2 passed (2)`, `Tests 7 passed (7)`.
  P-PRIV-05: old approval refused (`REFUSED count 77 distinct names != approved 76`, `REFUSED digest ad5e5df4...054e
  != approved 4c879f4d...a45`, rc=1); re-approved -> `NAMED-TABLE P-PRIV-05 ok - 77 distinct names, sha256
  ad5e5df41882`, `PROVE-RED OK: 8 of 8 rows red by name, controls green`. The shipped assertion string (yaml.safe_load,
  run by bash): emit sites ok (54 lines), learned speeds ok, named table ok, `NAMED P-PRIV-05 passed=76/77`, rc=1 -
  the only non-pass is `PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail(): MISSING`, the GRDB-gated
  test absent on this Windows box by design (T-0377 recorded the same, passed=75/76); CI's Linux job runs it.
  check-safety-disclaimer rc=0 with the two digest rows re-approved.
- 2026-10-16T13:22:20Z R6 (ruled on the pre-commit refusal): the fixture lives at Tests/Fixtures/t0279/ and the
  P-PRIV-05 re-approval at pins/PINS.yaml, neither in the filed touches; both are this task's ruled outputs (R2b, R4)
  and neither is serial-only, so touches gains `Tests/Fixtures/t0279/` and `pins/PINS.yaml`.
- 2026-10-16T13:55:00Z MERGED origin/main eb2d33c0 (T-0370, PR #260) as e94acd4a: LiveMoments.swift conflicted
  (T-0370 added `paywallConverted()` above `wire(_:)`) - resolved by keeping both; the pinned row re-approved for
  the merged file (993cb06c...dabe); check-telemetry-emit-sites.txt is main's (my diff to it is empty).
  ACCEPTANCE re-run whole on the merged head: (1) `Test run with 22 tests in 7 suites passed` incl.
  everySurpriseReasonEncodesExactly, fixtureIsTheEncodersBytes, fixtureCoversEveryWireName; (2) `Test Files 2 passed
  (2)`, `Tests 7 passed (7)`; (3) the fixture diff is the one added wrong_time line, none removed; (4) RED/GREEN as
  quoted above; (5) `-> SurpriseNotThisReason {` (:44), `case .wrongTime: return .wrongTime` (:49), no `nil`, no
  `default:`, emit-sites table diff empty; (6) `NAMED-TABLE P-PRIV-05 ok - 77 distinct names, sha256 ad5e5df41882`,
  `PROVE-RED OK: 8 of 8 rows red by name, controls green`; (7) disclaimer rc=0, mutate-population rc=0 (`the floor of
  165 holds`), mutate-only rc=0, emit-sites rc=0 (`55 lines approved`), line-cap, pins-yaml, exec-bits, queue-check
  rc=0 (quoted in the PR body).
- 2026-10-16T14:32:35Z REVIEW PASS by agent/rv1-t-0371 (PR #264, head 29494b0b; origin/main an ancestor). Acceptance
  committed before code (fcfff23f touches only this file). Re-run in a detached worktree: (1) `Test run with 22 tests
  in 7 suites passed`, the three named tests green; (2) `Test Files 2 passed (2)`, `Tests 7 passed (7)`; (3) fixture
  diff one added wrong_time line; (5) wire(_:) total, no nil/default, emit-sites .txt diff empty; (6) `NAMED-TABLE
  P-PRIV-05 ok - 77 distinct names, sha256 ad5e5df41882`, the PINS.yaml assertion carries the same sha and 77, the
  why-text change is append-only; (7) all eight gates rc=0; CI core + pins-source-only pass. Reviewer mutants, not
  in the population: M1 Swift raw label `"wrong_time"` -> `"wrongtime"` RED by name (everySurpriseReasonEncodesExactly,
  fixtureIsTheEncodersBytes); M2 Worker TELEMETRY_WIRE `"wrong_time"` -> `"wrongTime"` RED, 5 of 7 (the accepted-edge
  row, the refused-body row with the new wrongTime refusal, and the three fixture tests). Non-blocking, recorded by the
  owner: the iOS mapping LiveMoments.wire(.wrongTime) has no runtime test (no ScenicApp test target) and is held by
  compile totality plus the P-SAFE-03 pinned digest, as for T-0355's plan_result mapping. Label only - no coordinate,
  no instant, no cell; P-PRIV-05's coordinate rule untouched.

## Acceptance
1. `swift test --scratch-path .build/t-0371 --filter TelemetryTests` passes whole, including
   `TelemetryEventEncodingTests/everySurpriseReasonEncodesExactly()`, `TelemetryWireFixtureTests/fixtureIsTheEncodersBytes()`
   and `fixtureCoversEveryWireName()` at 37 lines.
2. `npx vitest run test/telemetryWhitelist.test.ts test/telemetryFixture.test.ts` (services/api) passes whole.
3. `git diff origin/main -- Tests/Fixtures/t0279/datapoints.jsonl` is exactly one added line,
   `{"blobs":["surprise_not_this","wrong_time",""],"doubles":[0,0],"indexes":["surprise_not_this"]}`, none removed.
4. RED first, by name, src unchanged: with only the tests and fixture line in, (1) fails
   everySurpriseReasonEncodesExactly, fixtureIsTheEncodersBytes and fixtureCoversEveryWireName, and (2) fails the
   whitelist accepted test and the fixture tests; then GREEN after the src change.
5. `LiveMoments.wire(_:)` returns non-optional `SurpriseNotThisReason`, has no `nil` and no `default`, and maps
   `.wrongTime` to `.wrongTime`; the emit-sites table is byte-identical to origin/main's.
6. `python ops/lib/check-named-table.py P-PRIV-05 <new sha> 77` exits 0 and its `--prove-red` passes; the PINS.yaml
   assertion carries the same sha and 77.
7. Gates bare, each exit 0: check-safety-disclaimer, check-mutate-population, check-mutate-only,
   check-telemetry-emit-sites, check-line-cap, check-pins-yaml, check-exec-bits, queue-check.

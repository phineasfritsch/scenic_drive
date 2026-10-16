---
id: T-0371
title: surprise_not_this has no wire reason for the card's fourth button, Wrong time - it sends nothing today
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T12:56:50Z
lease_expires_at: 2026-10-17T12:56:50Z
worktree: .worktrees/T-0371
branch: task/T-0371
exclusive: []
touches: [Sources/Telemetry/, Tests/TelemetryTests/, services/api/, apps/ios/Packages/ScenicApp/Sources/PlanAdapter/, ops/lib/]
pins_affected: [P-PRIV-05]
reviewer: null
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

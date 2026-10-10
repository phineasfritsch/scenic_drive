---
id: T-0355
title: The app emits the closed telemetry enum - a ScenicAPIClient TelemetryClient posts to /telemetry and every one of the 14 TelemetryEventKind cases has exactly one shipping emit site, so ops/funnel has a data source
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-10T03:21:11Z
lease_expires_at: 2026-10-10T11:21:11Z
worktree: .worktrees/T-0355
branch: task/T-0355
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/Telemetry/, Tests/ScenicAPIClientTests/, Tests/TelemetryTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10 (M5 exit "Telemetry + ops/funnel"): the enum exists (Sources/Telemetry/TelemetryEventKind.swift,
T-0265) and the Worker ingests it (services/api/src/telemetry.ts, T-0279), but Sources/ScenicAPIClient has no
/telemetry client and apps/ios imports Telemetry only for H3Cell (LiveSurpriseLedger.swift). Nothing emits, so
ops/funnel (T-0284/T-0285) reads nothing.

MEASURE FIRST: the Worker's /telemetry request shape and refusals (quote telemetry.ts), the 14 cases and their
payloads, and where in the app each event's moment happens today (file:line per case). RULE: one client (fail-quiet:
telemetry never blocks or errors a user action; bounded queue, dropped on failure), payload exactly the plan's
"feature ids, H3-5 cell, durations only" (never a coordinate, never more than one cell per action - CLAUDE.md
privacy invariant), one emit site per case. Tests through the shipping client with exact request-body equality; a
whitelist guard that every emit site is approved and every case has one (fail-closed, red then green). Every apps/ios
Swift edit needs the P-SAFE-03 digest re-approval in ops/lib/check-safety-disclaimer-pinned; if the permission
classifier refuses it, ship the Linux slice and stop the app half with that in stillOpen. post_drive_answer's UI is
T-0358; this task wires the other 13 and the client.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-1).
- 2026-10-10T03:21:11Z claimed by agent/claude-opus-5; lease until 2026-10-10T11:21:11Z
- 2026-10-10T03:31:47Z MEASURED by agent/claude-opus-5 (owner), before any code.
  M1 Worker (services/api/src/telemetry.ts handleTelemetry, telemetryPoint.ts parseTelemetryBody): POST only (405
  otherwise); KILL -> 503 telemetry_paused before the body; body exactly `{"events": [point, ...]}`, 1 to
  MAX_TELEMETRY_EVENTS_PER_REQUEST = 20 points, each exactly {indexes, blobs, doubles} with indexes = [name], blobs =
  [name, label, cell], doubles = [v1, v2] whole numbers in the per-name range, cell an H3 res-5 cell on plan_requested
  only -> else 400 invalid_request; deps unbound -> 503 telemetry_unavailable; the whole request reserved against
  DAILY_TELEMETRY_QUOTA in the caller's bucket -> 429 quota_exhausted; else 200 {written: n}. The bucket is
  identifyCaller's: the session subject when a bearer verifies, else deviceIdentity = lowercased `x-scenic-device`.
  M2 The 14 cases (Sources/Telemetry/TelemetryEvent.swift): planRequested(feature, budgetMinutes, origin H3Cell),
  planResult(PlanResultKind), previewShown, handoffTapped(HandoffApp), driveStarted, driveCompleted(CompletionPercent,
  deviations), driveAbandoned(CompletionPercent), postDriveAnswer(prettier) [T-0358], surpriseShown,
  surpriseNotThis(reason), surpriseTakeMeThere, surpriseArrived, corpusActivated(version Int), paywall(PaywallStep).
  M3 Dependencies (root Package.swift): ScenicAPIClient = [ScenicKit, PlaceStore]; ScenicAPIClientTests the same;
  Telemetry = Foundation only. apps/ios: PlanAdapter is the ONLY target linking Telemetry (and ScenicAPIClient);
  FeaturePlanSheet, FeatureScenicHome, FeatureSurpriseMe, Entitlements import DesignSystem/ScenicKit/PlaceStore/Handoff
  only; NavAdapter ScenicKit + Ferrostar. The shell (apps/ios/ScenicDrive/ScenicDriveApp.swift) composes
  LivePlanner.make() (:56), LiveTripPlanner.make() (:56), LiveLoopPlanner.make() (:56), LiveSurpriseLedger.make() (:64).
  M4 Where each moment happens today (apps/ios/Packages/ScenicApp/Sources/):
  plan_requested + plan_result - FeaturePlanSheet/PlanSheetScreen.swift:214, LoopScreen.swift:81, RoadTripScreen.swift:91
  (`await planner.plan(ticket)`; the planners are PlanAdapter's, so the moment is reachable in PlanAdapter);
  surprise_shown - FeatureSurpriseMe/SurpriseCard.swift:74 `await ledger?.recordShown(candidate)` (ledger =
  PlanAdapter's LiveSurpriseLedger); preview_shown - FeaturePlanSheet (the preview card, no PlanAdapter seam);
  handoff_tapped - FeatureScenicHome/GatedHandoffButton.swift:94; drive_started - NavAdapter/DriveHost.swift:23;
  drive_completed / drive_abandoned - FeatureScenicHome/DriveScreen.swift:117 (End) - DriveDisplay carries no progress
  fraction; surprise_not_this - SurpriseCard.swift:186; surprise_take_me_there - SurpriseCard.swift:125;
  surprise_arrived - NO moment: the Surprise opens Apple Maps and the app never learns of an arrival;
  corpus_activated - PlanAdapter/LiveCorpus.swift:50 LaunchCorpus.choose, whose CorpusActivation.activated carries no
  version and CorpusManifest.version is a String; paywall - Entitlements/PaywallScreen.swift (no PlanAdapter seam).
  M5 apps/ lines naming `Telemetry` today: 1 (PlanAdapter/LiveSurpriseLedger.swift:4 `import Telemetry`), plus
  ScenicApp/Package.swift:146 (not Swift source of a target). Lines matching `.<case>` of the 14: 0 in Sources.
- 2026-10-10T03:31:47Z RULINGS by agent/claude-opus-5 (owner).
  R1 (Brief vs reality) The client lives in Sources/Telemetry, not ScenicAPIClient: per M3 a ScenicAPIClient client
  that takes TelemetryEvent needs a new Telemetry dependency in root Package.swift, serial-only and outside touches.
  Telemetry is Foundation-only and URLSession is Foundation (FoundationNetworking behind canImport on Linux), so
  `TelemetryClient` sits beside the enum with NO new dependency and accepts only `TelemetryEvent` - the payload is
  closed by type (P-PRIV-05). Its tests are Tests/TelemetryTests/TelemetryClientTests.swift.
  R2 Wire: POST `<base>/telemetry`; headers EXACTLY {content-type: application/json, x-scenic-device: lowercased
  install UUID} (no bearer, no account token: M1's device bucket); body EXACTLY `{"events":[dataPoint, ...]}`,
  JSONEncoder .sortedKeys (blobs, doubles, indexes - the Worker's rebuilt key order).
  R3 Fail-quiet, bounded: `record(_:)` never throws; at most `capacity` = 20 events WAIT (= the Worker's
  MAX_TELEMETRY_EVENTS_PER_REQUEST, so a batch is never one the Worker refuses for size); an event recorded while 20
  wait is dropped; while a post is in flight new events wait; each post carries everything waiting; ANY outcome
  (throw, any status) drops that batch - no retry, nothing persisted. The app's `LiveTelemetry.record` hands the
  event to an unstructured Task, so no user action awaits telemetry.
  R4 Privacy: the one location is plan_requested's H3 res-5 cell of the ticket's origin, made on the device; one plan
  action = one plan_requested = one cell. Nothing else carries a place.
  R5 (Brief vs touches/reality) Wired HERE: plan_requested (scenic, loop, road_trip; `surprise` has no plan request -
  Surprise.pick is offline), plan_result and surprise_shown - the three whose moment PlanAdapter already owns through
  objects the shell composes (M3/M4), so no shell, feature-target or Package.swift edit. NOT wired here, filed as
  T-0361 with M4's measurements: preview_shown, handoff_tapped, drive_started, drive_completed, drive_abandoned,
  surprise_not_this, surprise_take_me_there, surprise_arrived, corpus_activated, paywall - each moment sits in a
  feature target or NavAdapter that may not import Telemetry or PlanAdapter, so each needs a feature seam plus the
  shell (outside touches); drive_completed/abandoned need a progress fraction DriveDisplay does not carry;
  surprise_arrived has no moment; corpus_activated has no Int version. post_drive_answer stays T-0358. The emit-site
  guard holds EVERY case as exactly one approved emit row OR one pending row naming its task - never both, never
  neither - so wiring a pending case is a whitelist move in the same diff.
  R6 One emit site per case: each TelemetryEvent construction is ONE line in PlanAdapter/LiveTelemetry.swift (spelled
  `TelemetryEvent.<case>`); the callers of LiveTelemetry are approved lines too. Guard ops/lib/check-telemetry-emit-sites.py
  over EVERY non-//-leading line of every *.swift under apps/ that contains `Telemetry` or names `.<case>` of the 14,
  compared WHOLE against ops/lib/check-telemetry-emit-sites.txt (memory source-guards-fail-closed).
  R7 plan_result mapping (PlanAdapter, digest-pinned by P-SAFE-03): preview/itinerary -> routed; offered,
  noScenicAlternative, nothingPretty, noCleanLoop, ceilingBreached -> no_alternative; quotaExhausted -> quota_exceeded;
  every other failure -> failed. road_trip's budgetMinutes is 0 (a trip's budget is a percent, not minutes); loop's
  is the loop's minutes.
  R8 Population: TelemetryClient's numeric bound (capacity, batch) ships ops/mutate/telemetryclient*.py with a literal
  floor, killers named in TelemetryClientTests.
- 2026-10-10T03:31:47Z ACCEPTANCE (written before code; re-run and re-quoted at the final pre-review commit).
  1. `swift test --scratch-path .build/t0355 --filter TelemetryTests.TelemetryClientTests` passes, every test by name:
     everyEventPostsExactlyItsRequest() (every row of TelemetryEventEncodingTests.rows through the shipping
     TelemetryClient.record: exactly one request, url/method/headers/body EQUAL to the recomputation, two rows also equal
     to literal bytes; base with and without a trailing slash), waitingBoundTable() (rows 19, 20, 21 events recorded
     behind an in-flight post: the next post carries exactly the first min(n, 20) in order, the rest dropped, request
     count exact), everyOutcomeDropsTheBatch() (throw, 200, 400, 429, 503, each crossed with two event variants: the
     next post carries only the next event), capacityIsTheWorkersCap() (capacity == the literal in
     services/api/src/telemetryPoint.ts), recordedOnlyAfterTheFirstPostReturns() (no request before record).
     Seen RED first by name (the client absent: does not compile -> each named test missing).
  2. `python ops/lib/check-telemetry-emit-sites.py` exit 0; `--prove-red` every row red by name with the control green;
     whitelist absent -> exit 2.
  3. `python ops/mutate/telemetryclient.py` every mutant killed by a named test, floor holds; `--prove-floor` red rows.
  4. `bash ops/lib/check-safety-disclaimer`, `python ops/lib/check-mutate-population.py`, `bash ops/lib/check-line-cap`,
     `python ops/lib/check-pins-yaml.py`, `bash ops/queue-check` green.
  5. ios-compile and ios-screenshot succeed on task/T-0355; the plan-sheet and home shots looked at.

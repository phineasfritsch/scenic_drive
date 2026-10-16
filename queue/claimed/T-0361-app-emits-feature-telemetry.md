---
id: T-0361
title: The app emits the ten feature-side telemetry cases T-0355 left pending - a seam per feature target plus the shell, so each has its one emit site
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T02:25:35Z
lease_expires_at: 2026-10-17T02:25:35Z
worktree: .worktrees/T-0361
branch: task/T-0361
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-SAFE-03]
reviewer: null
depends_on: [T-0355]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0355 shipped Sources/Telemetry/TelemetryClient and PlanAdapter/LiveTelemetry, and emits plan_requested, plan_result
and surprise_shown (the moments PlanAdapter already owns). ops/lib/check-telemetry-emit-sites.txt holds the other
ten as `pending T-0361`: preview_shown, handoff_tapped, drive_started, drive_completed, drive_abandoned,
surprise_not_this, surprise_take_me_there, surprise_arrived, corpus_activated, paywall (post_drive_answer is T-0358).

Measured by T-0355 (its Log M3/M4): each moment sits in a target that may not import Telemetry or PlanAdapter -
FeaturePlanSheet (preview card), FeatureScenicHome (GatedHandoffButton.swift:94, DriveScreen.swift:117 End),
FeatureSurpriseMe (SurpriseCard.swift:125 take me there, :186 not this), Entitlements (PaywallScreen), NavAdapter
(DriveHost.swift:23 start). So each needs a feature-owned seam (a closure or environment value of the feature's own
types) that the shell (apps/ios/ScenicDrive/ScenicDriveApp.swift) wires to a LiveTelemetry function - the shell file
is in this task's touches. OPEN QUESTIONS TO MEASURE AND RULE FIRST: drive_completed/abandoned need a whole-percent
progress fraction and a deviation count that DriveDisplay does not carry (ScenicKit DriveSession may); surprise_arrived
has NO moment today (the Surprise opens Apple Maps; the app never learns of an arrival) - rule whether it is
measurable at all or the case stays pending with a reason; corpus_activated needs an Int version but
CorpusActivation.activated carries none and CorpusManifest.version is a String - rule the mapping or the gap.

Acceptance shape (T-0355's): every wired case moves from a pending row to exactly one emit row in the same diff; the
guard's --prove-red stays red row by row; every apps/ios edit re-approves its P-SAFE-03 digest; ios-compile and
ios-screenshot succeed with the touched screens looked at.

## Log
- 2026-10-10T04:10:00Z filed by agent/claude-opus-5 (T-0355 owner) from T-0355 R5.
- 2026-10-16T02:25:35Z claimed by agent/claude-opus-5; lease until 2026-10-17T02:25:35Z
- 2026-10-16T02:32:24Z MEASURED (main 53d4d761), before code:
  M1 the moments today: PlanPreviewCard/LoopPreviewCard/TripItineraryCard (FeaturePlanSheet) have no appear hook;
     GatedHandoffButton.swift:94 `try SkylineHandoff.open(...)` then `onFailure(nil)` on success - BOTH the home's drive
     (ScenicHomeScreen `gatedHandoff`, onFailure `handoffFailure = $0`) and the Surprise's place (`openSurprise`,
     onFailure `surpriseFailure = $0`) go through it; NavAdapter/DriveHost.swift:23 `.onAppear { try? navigator.start() }`
     and :24 `.onDisappear { navigator.stop() }` (the drive ends when the shell sets `drive = nil` from DriveScreen's
     onEnd); SurpriseCard.swift:186 `notThis(_ reason: SurpriseFeedback.Reason, ...)`; PaywallScreen has no appear
     hook and no purchase-completion hook; LiveCorpus.launch's `LaunchCorpus.choose(...)` returns a CorpusLaunch whose
     `activation` is `.activated` with `corpus` = the activated file's URL.
  M2 DriveSession carries `progressSegment` (a segment index on the CURRENT line; a taken reroute resets it to 0 on
     the new line) and no deviation count; DriveDisplay carries `arrived` (DriveVoice.hasArrived) and neither number.
  M3 surprise_arrived: the Surprise hands the place to Apple Maps (SkylineHandoff.open, place:) and the app is never
     told of an arrival - no code path, no API, nothing to measure.
  M4 corpus_activated: CorpusActivation.activated has no payload; the activated corpus' version is
     `PlaceStore(path:).meta().corpusVersion`, a String shaped "20261006T000000Z" (CorpusManifest.version's doc).
  M5 Entitlements' only dependency is DesignSystem (ScenicApp Package.swift) - it cannot see a ScenicKit type.
  M6 SurpriseFeedback.Reason has FOUR cases (tooFar, notMyThing, beenThere, wrongTime); Telemetry's
     SurpriseNotThisReason has THREE (too_far, been_there, not_my_thing) - no wrong_time.
  M7 request bodies: TelemetryEventEncodingTests holds every one of the 14 cases' data point by exact equality and
     TelemetryClientTests the posted body; this task adds no Telemetry type.
- 2026-10-16T02:32:24Z RULINGS (author rule, before code):
  R1 THE SEAM. ScenicKit gets `AppMoment` (closed enum of the app's moments, named so no line spells a
     TelemetryEventKind case) and `AppMomentReporting` (one `report(_:)`). Each feature owns its environment key of
     that protocol (FeaturePlanSheet `planMoments`, FeatureScenicHome `homeMoments`, FeatureSurpriseMe
     `surpriseMoments`, NavAdapter `driveMoments`); Entitlements (M5; a ScenicKit dependency is a serial Package.swift
     edit) owns a `paywallShown` closure key of its own. PlanAdapter's `LiveMoments` is the one conformer and maps each
     moment to ONE LiveTelemetry function; LiveTelemetry keeps the one emit line per case. The shell sets the keys.
  R2 preview_shown: every plan preview card's appearance (scenic, loop, road trip) - one per appearance.
  R3 handoff_tapped(apple_maps): the home's drive handed to Apple Maps - fired in ScenicHomeScreen's `gatedHandoff`
     onFailure when it is called with nil (the open succeeded). A tap the disclaimer stops, or the handoff refuses,
     sends nothing (no double count across the disclaimer). Apple Maps is the only app the button opens.
  R4 surprise_take_me_there: the Surprise's place handed to Apple Maps - `openSurprise`'s onFailure called with nil,
     the same rule as R3. It is NOT also a handoff_tapped (a place, not a drive).
  R5 surprise_not_this: SurpriseCard's notThis reports the reason; LiveMoments maps tooFar/beenThere/notMyThing to
     their wire reasons and wrongTime to NOTHING SENT (M6: the closed wire list has no such reason; adding one is a
     Telemetry + Worker change) - filed T-0371.
  R6 drive_started / drive_completed / drive_abandoned: ScenicKit `DriveMomentLatch` - began once, after
     `navigator.start()` succeeds; ended once, only after began, from the session as the host disappears: arrived
     (DriveDisplay.arrived) -> completed, else abandoned. DriveSession gains `offRouteCount` (each off-route
     DECLARATION in observe: guiding -> rerouting or rejoining; a reconnect asking again is not a new one) and
     `fractionDriven` = metres along the driven lines to the progress vertex / (metres before the current line + the
     current line's length): a taken reroute adds the old line's driven metres to `metersBefore`, so a reroute does
     not reset the fraction to 0. CompletionPercent floors it.
  R7 paywall: `paywall(.shown)` on PaywallScreen's appearance. `.converted` is NOT wired: StoreKit's
     onInAppPurchaseCompletion replaces the store view's default completion handling, a purchase-flow change no
     Linux test or screenshot can see - filed T-0370. The case's whitelist row moves to emit (the case is emitted).
  R8 corpus_activated: ScenicKit `CorpusVersionNumber.value(of:)` maps exactly "YYYYMMDDTHHMMSSZ" (16 chars, 14
     digits) to the Int of its 14 digits (20261006T000000Z -> 20261006000000, < 2^53 so the double is exact); any
     other string is nil and nothing is sent. Fired from LiveCorpus.launch when activation == .activated.
  R9 surprise_arrived STAYS PENDING (M3): unmeasurable today - filed T-0369; its pending row names T-0369.
  R10 the guard's prove-red rows that named `pending previewShown/paywall T-0361` re-anchor on the one pending row
     (surpriseArrived T-0369); every row stays red.
  R11 touches += ops/mutate/ (the drive population takes the new DriveSession lines and the latch; P-PROC-06).
- 2026-10-16T02:32:24Z ACCEPTANCE (re-quoted at the final commit):
  A1 `python ops/lib/check-telemetry-emit-sites.py` -> ok; 13 of 14 cases emitted once, 1 pending by task.
  A2 `python ops/lib/check-telemetry-emit-sites.py --prove-red` -> every row red, `PROVE-RED  ok`.
  A3 each of the nine newly wired cases' `TelemetryEvent.<case>` is on exactly one line, in LiveTelemetry.swift.
  A4 swift test --filter 'AppMomentTests|DriveMomentLatchTests|DriveProgressTests|CorpusVersionNumberTests' passes;
     each named test seen RED first (Log quotes the red run).
  A5 `python ops/mutate/drive.py --only <new ids>` -> every new mutant CAUGHT; population floor raised.
  A6 check-mutate-population, check-mutate-only, check-drive-display (+ --prove-red), bash check-safety-disclaimer,
     check-line-cap, check-pins-yaml, check-exec-bits, ops/queue-check -> each exit 0.
  A7 ios-compile and ios-screenshot -> success; the home, plan preview, drive and paywall shots looked at.

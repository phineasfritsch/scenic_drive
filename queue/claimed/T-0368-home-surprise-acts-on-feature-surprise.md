---
id: T-0368
title: The home's Surprise Me chip acts on /config's feature_surprise - hidden or its typed line when false, and the plan sheet's post-tap Surprise action follows it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T06:29:51Z
lease_expires_at: 2026-10-17T06:29:51Z
worktree: .worktrees/T-0368
branch: task/T-0368
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/ScenicAPIClient/ConfigCache.swift, Tests/ScenicAPIClientTests/ConfigCacheTests.swift, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/, ops/mutate/, queue/]
pins_affected: []
reviewer: null
depends_on: [T-0364]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0364 decodes feature_surprise (RemoteConfig.featureSurprise, per field, default true) and acts on it only in the
plan sheet's pre-tap pause notice (ConfigDegrade.pausedSurpriseOff, R4). The home's SurpriseToggle (home.surprise)
and SurpriseCard are composed by the shell apps/ios/ScenicDrive/ScenicDriveApp.swift, outside T-0364's touches, and
FeatureScenicHome may import no adapter - so the chip still shows under feature_surprise=false, and the post-tap
PlanFailureCopy rows (quotaExhausted, planningPaused, attestUnsupported) still offer "Surprise me instead".

MEASURE first (the shell's composition, whether ScenicDriveApp.swift is frozen by check-safety-disclaimer-frozen,
how the home could receive the config without a feature-to-adapter import). RULE hide vs typed line, and whether
PlanFailureCopy takes the flag. Surprise Me sends the Worker nothing (no /surprise route), so the flag is advisory.

## Log
- 2026-10-16T00:26:47Z filed by agent/claude-opus-5 as T-0364's follow-up (T-0364 R6). Ids checked on origin/main and every
  origin/task/* branch: highest T-0366, so T-0367.
- 2026-10-16T01:20:31Z renumbered T-0367 -> T-0368 by agent/claude-opus-5: main took T-0367 (telemetry-install-id-per-request)
  in the T-0358 merge; ids rechecked on origin/main and every origin/task/* branch, highest T-0367.
- 2026-10-16T06:29:51Z claimed by agent/claude-opus-5; lease until 2026-10-17T06:29:51Z
- 2026-10-16T06:34:53Z MEASURED by agent/claude-opus-5 (worktree at 6681d944):
  - The shell (apps/ios/ScenicDrive/ScenicDriveApp.swift, 73 lines) composes the home as
    `ScenicHomeScreen(onSettings: ..., surprise: { open, failure in AnyView(SurpriseCard(...)) })` and the plan sheet as
    `PlanSheetScreen(planner: LivePlanner.make(), ..., onDrive: ..., onClose: ...)`; it imports PlanAdapter, so it can read
    LivePlanner. It IS frozen: ops/lib/check-safety-disclaimer-frozen FROZEN_APP_SHELL lists every line of `struct
    ScenicDriveApp` whole, and ops/lib/check-safety-disclaimer-pinned PINNED_SHELL_DIGEST pins its sha256 (760fe0f9...).
  - The home's chip band is frozen too (FROZEN_CHIPS: `surpriseButton`, `if isShowingSurprise {`,
    `surprise({ openSurprise($0) }, surpriseFailure)`). ScenicHomeScreen.swift is 299 lines (cap 300).
  - FeatureScenicHome imports DesignSystem, Handoff, MapAdapter, ScenicKit, SwiftUI - never PlanAdapter or
    ScenicAPIClient; RemoteConfig and anything typed over it in ScenicKit are reachable from the home.
  - The only /config fetch is ConfigCache.refresh() (ScenicAPIClient), called by ConfiguredPlanner/LoopPlanner/
    TripPlanner.degrade() when a plan, loop or trip form appears. The kept answer is `private var kept` (storage +
    ConfigReader.decode, else RemoteConfig.bundled); nothing outside ScenicAPIClient can read it without a request.
  - PlanFailureCopy.of(_:) has one caller in the app: PlanSheetScreen.planContent's `.failed` card; act(.surpriseMe) is
    onClose(). Three rows carry .surpriseMe (quotaExhausted, planningPaused, attestUnsupported); two of their lines say
    "Surprise Me still works". PlanOfferCopy, LoopFailure and TripFailure name no Surprise action.
  - ConfigDegrade.of(_:appBuild:on: .plan) is .clear whenever planning_paused is false, whatever feature_surprise is,
    so the sheet's degrade cannot tell a post-tap failure that Surprise is off.
  - ios-screenshot's shot LIST is inside .github/workflows/ios-screenshot.yml (pinned by ops/lib/ios_screenshot_pinned.py),
    outside touches.
- 2026-10-16T06:34:53Z RULINGS by agent/claude-opus-5:
  - R1 (source, privacy): the home and the sheet read feature_surprise from the KEPT /config answer only - no new
    request anywhere (the owner is deciding a privacy rule; a launch-time /config fetch would be a new contact).
    ConfigCache.kept becomes public (read-only: storage + ConfigReader, else bundled); touches widen by exactly
    Sources/ScenicAPIClient/ConfigCache.swift and Tests/ScenicAPIClientTests/ConfigCacheTests.swift. PlanAdapter's
    LivePlanner.surpriseGate() is the one live reader: SurpriseGate.of(cache(base).kept) with an https base, else
    SurpriseGate.of(RemoteConfig.bundled) (on). The plan sheet reads it in its existing .task AFTER planner.degrade() -
    so after the refresh that appearance already makes - and the shell re-reads it when the plan sheet is dismissed.
  - R2 (home: typed line, not hide): the chip stays (the band's layout and the measured covered edge do not shift on an
    async answer, and it matches T-0364 R5, where a switched-off loop or trip shows its typed line); with the flag off
    the slot shows SurpriseGate.offLine "Surprise Me is switched off for now. You can still plan a drive." IN PLACE of
    the card, and the shell's card builder is not called, so no deck, ledger or corpus read happens.
  - R3 (new ScenicKit type SurpriseGate, .on/.off): `SurpriseGate.of(RemoteConfig)` is featureSurprise and nothing
    else; `homeLine` is nil when on, offLine when off. Not numeric - no ops/mutate population (CLAUDE.md scopes it to
    numeric modules).
  - R4 (PlanFailureCopy takes the gate): `of(_:surprise:)` replaces `of(_:)` (the one-argument form is removed, so the
    one app caller cannot compile without choosing). Off rows: quotaExhausted keeps its line, action .close;
    planningPaused -> ConfigDegrade.pausedQuietLine, .close; attestUnsupported -> "This phone can't plan drives yet.",
    .close. Every other row is identical under both gates. A DEBUG PlanRehearsal keeps .on (its .task returns first).
  - R5 (no new shot): the shot list is in the workflow, outside touches; the existing 22 shots must stay green and the
    `surprise` shot (no base URL in CI -> bundled -> on) must still show the card. The off line has no shot - gap.
  - R6 (single binding): one reader (LivePlanner.surpriseGate) feeds both surfaces; the shell holds the home's copy in
    one @State and hands the sheet the reader itself.

## Acceptance
1. `swift test --filter PlanFailureCopyTests` passes: for every PlanSheetFailure x SurpriseGate (28 rows),
   `PlanFailureCopy.of(failure, surprise: gate)` EQUALS a whole PlanFailureCopy typed in the test; meta-rows: exactly
   the three cases quotaExhausted, planningPaused, attestUnsupported differ between .on and .off (every other row is
   equal), no .off row carries .surpriseMe or a line containing "Surprise", 14 distinct lines under each gate.
2. `swift test --filter SurpriseGateTests` passes: SurpriseGate.of over the cross product planning_paused x
   feature_loop x feature_trip x feature_surprise x min_app_build {1, RemoteConfig.maxAppBuild} (32 configs) equals
   the gate typed from feature_surprise alone, with a meta-row that both answers occur; homeLine is nil for .on and
   exactly "Surprise Me is switched off for now. You can still plan a drive." for .off; allCases == [.on, .off];
   RemoteConfig.bundled's gate is .on.
3. `swift test --filter ConfigCacheTests` passes, including: `kept` over every stored variant (nothing, good bytes with
   feature_surprise true and false, garbage, build 0) equals the row's decoded answer or the Worker defaults, with ZERO
   requests on the transport and no save; after a good refresh `kept` equals the fresh answer; after a refused one it
   is unchanged.
4. The app half compiles and shows: ios-compile success and ios-screenshot success on task/T-0368, with the
   `surprise-light`/`surprise-dark` shots showing the card (gate on) and a plan-sheet shot unchanged.
5. Bare gates green: check-safety-disclaimer (FROZEN_APP_SHELL, FROZEN_CHIPS, PINNED_SHELL_DIGEST and every pinned/
   linked digest re-approved), check-mutate-population, check-mutate-only, check-mutate-anchors,
   check-telemetry-emit-sites, check-line-cap, check-pins-yaml, check-exec-bits, queue-check.

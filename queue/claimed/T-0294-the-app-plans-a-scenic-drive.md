---
id: T-0294
title: The app plans a scenic drive - typed destination from the corpus search, extra-minutes, Plan calls the Worker through ScenicAPIClient, and the preview shows the route, ETA vs fastest, the hazard strip and one copy line per PlanError
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T11:14:19Z
lease_expires_at: 2026-10-08T07:14:19Z
worktree: .worktrees/T-0294
branch: task/T-0294
exclusive: [package-swift]
touches: [apps/ios/Packages/ScenicApp/Package.swift, apps/ios/Packages/ScenicApp/Sources/, apps/ios/Packages/ScenicApp/Tests/, apps/ios/ScenicDrive/ScenicDriveApp.swift, Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/lib/, pins/PINS.yaml, ops/mutate/]
pins_affected: [P-SAFE-03, P-PRIV-06, P-ATTR-01]
reviewer: null
depends_on: [T-0251, T-0254, T-0289]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: how the app composes features today (FeatureScenicHome product carries Entitlements + FeatureSurpriseMe to avoid pbxproj edits - T-0271/T-0273), what P-SAFE-03 / T-0289 content-pins cover in apps/ios, and the seam: feature targets import only DesignSystem, ScenicKit, PlaceStore and their own protocols (CLAUDE.md), so planning is a protocol in the feature and ScenicAPIClient is imported only by one new adapter target (like MapAdapter for MapLibre), carried in the product the shell already links - no project.pbxproj edit"
  - "The plan-sheet state machine lives in ScenicKit (Linux-testable): idle -> searching(query) -> destination chosen -> planning -> preview(route) | failed(PlanError); every PlanError case maps to exactly one copy line and one action per the plan's Degraded states row (quotaExhausted, planningPaused, routingOffline, noRoute, attestUnsupported, regionUnsupported, offlineDuringDrive, noScenicAlternative, unknownPlace, planRefused, invalidRequest, refusedOnDevice, unexpectedResponse) - a table test by full equality with a meta-test that the table covers every case of the enum (compile-time exhaustive switch plus a count)"
  - "The safety disclaimer still gates the first plan (P-SAFE-03): a test drives the state machine from first launch and shows no PlanClient call before acceptance (counting transport = 0), seen red then green"
  - "Location denied path (P-PRIV-06): the origin can be a typed place; no CoreLocation import in the root package; the request carries one coordinate at 2 dp (the existing PlanRequestBody guard)"
  - "The preview shows the AttributionFooter at every detent (P-ATTR-01 unchanged) and the 'estimate · no traffic data' badge; ios-compile and ios-screenshot CI green; content pins re-approved in the same diff for every apps/ios file touched"
  - "Mutation population for the state machine and the error-copy table with a literal floor; three entries MISSED before, CAUGHT by name after"
---
## Brief

Milestone M4: "Plan sheet (corpus FTS5 + Photon; departs-at); Route preview (hazard strip, explanation, badge);
PlanError states". Today the app never calls PlanClient (grep: only Sources/ScenicAPIClient uses it), so the core promise
- "Take the long way. Unwind." (memory owner-route-intent) - is not reachable from the phone. Photon is not deployed:
search is the corpus FTS5 only (PlaceStore T-0254); typed street addresses are a later task. Departs-at is out of scope.

## Log
- 2026-10-07T03:23:40Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M4 plan sheet); claim after T-0289 merges.
- 2026-10-07T11:14:19Z claimed by agent/claude-opus-5; lease until 2026-10-08T07:14:19Z
- 2026-10-07T11:32:20Z MEASURE, then RULINGS before code. agent/claude-opus-5 (owner).
  - MEASURED. `grep -rln 'PlanClient|ScenicAPIClient' apps Sources --include=*.swift` outside Sources/ScenicAPIClient:
    0 files - the phone never plans. The shell links ONE product, FeatureScenicHome, whose target list carries
    Entitlements (T-0271) and FeatureSurpriseMe (T-0273), so a new module rides that product with no pbxproj edit.
    P-SAFE-03 / P-ATTR-01 content pins over apps/ios today: -pinned PINNED_APP_SWIFT (37 lines: every apps/ios .swift
    incl. ScenicApp/Package.swift, 38 .swift on disk = 37 + ScenicDriveApp.swift under PINNED_SHELL_DIGEST),
    PINNED_FEATURE / PINNED_SURPRISE module sets; -frozen FROZEN_APP_SHELL (the shell's struct, line for line); -doors
    DOORS_PACKAGE (every name:/path:/targets: line of the ScenicApp manifest), DOORS_VIEWS, DOORS_OPENERS (the bare
    identifiers open/perform/... anywhere under apps/ios); -linked PINNED_ROOT_SOURCES (120 Sources/ entries);
    check-safety-disclaimer key_set (the store key `safety.disclaimer.acknowledged.v1` once, in ScenicHomeScreen);
    check-store-links (the shell's ScenicHomeScreen/Settings lines and the Settings sheet run); check-map-attribution
    FOOTER_SET (one `AttributionFooter(` in ScenicHomeScreen), the OpenStreetMap literal whitelist and limb (g)'s
    word `credit` whitelist. Each is a whole-line or digest whitelist: every apps/ios line this task adds that one
    of them reads is typed into it in the same diff.
  - R1 SEAM. PlanError lives in ScenicAPIClient, which depends on ScenicKit, so ScenicKit cannot name it. ScenicKit
    gets `PlanFailure` - the thirteen PlanError cases one for one, payload-free, CaseIterable - the copy table,
    the `RoutePlanning` protocol and the `PlanSheet` state machine. ScenicAPIClient gets `PlanError.failure` (an
    exhaustive switch) and `ClientPlanner`, the RoutePlanning conformer over PlanClient. The protocol lives in
    ScenicKit rather than in the feature: a feature-owned protocol makes the adapter import the feature, and the
    Linux gate test could not reach it. touches: widened by Sources/ScenicAPIClient/ and Tests/ScenicAPIClientTests/
    in this commit - the P-SAFE-03 test needs CountingPlanTransport, which ScenicKitTests cannot import.
    Apple side: a feature target FeaturePlanSheet (DesignSystem, ScenicKit, PlaceStore - CLAUDE.md's list) and an
    adapter target PlanAdapter, the ONLY apps/ios importer of ScenicAPIClient (as MapAdapter is of MapLibre), which
    builds the live planner. Both ride the FeatureScenicHome product; the shell imports both and composes them,
    as it does Entitlements. No project.pbxproj edit.
  - R2 STATES. idle -> searching(field, query) -> chosen(destination) -> planning(ticket) -> preview(ticket,
    PlanPreview) | failed(ticket, PlanFailure). `field` is destination or start (R4). `startPlanning()` is THE gate
    the view calls: it returns a ticket only from chosen/failed/preview with a start, a budget in 0...180 and the
    disclaimer accepted; otherwise nil and the state is unchanged. `finish(ticket, outcome)` applies only to the
    ticket in flight (a stale reply is dropped).
  - R3 DISCLAIMER (P-SAFE-03). One writer stays one writer: the plan feature READS the home's store key (key_set
    gains one read-only occurrence, under its own identifier - ack_set's identifier is not used), feeds it to
    PlanSheet(disclaimerAccepted:), and never writes it. Before acceptance the sheet says the safety note comes
    first and the Plan button is not offered. Presenting the home's disclaimer from the plan sheet needs
    FeatureScenicHome's frozen surface reopened - a follow-up, not this diff.
  - R4 ORIGIN (P-PRIV-06). No CoreLocation anywhere in this diff. The start is a typed corpus place, chosen through
    the same FTS5 search (the location-denied path is the only path today); the ticket carries its coordinate
    rounded to 2 dp; PlanRequestBody's guard is unchanged and still refuses anything else. Test: the bytes the
    counting transport received EQUAL the JSON recomputed from the place (full-equality oracle).
  - R5 COPY. Payload-free copy: quotaExhausted's resetsAt is UTC midnight (17:00 in LA in summer), so the plan's
    "back at midnight" would be false for the owner; the line names no clock. The plan's handoff-of-last-route,
    cached plans, waitlist and rejoin banner have no store or screen yet, so each row's ONE action is one the app
    can do today: surpriseMe, tryAgain, chooseAnotherPlace, changeStart, close. Calm, specific, no exclamation marks.
  - R6 PREVIEW. The route is drawn as a SwiftUI path, not a second MapLibre surface (a second `MapView(` is a
    P-ATTR-01 surface-whitelist change and a second basemap resolve - out of scope). The AttributionFooter sits in
    the preview's bottom inset at every detent, its text `PlanPreview.attribution` - a ScenicKit constant, because
    apps/ios may hold one OpenStreetMap literal only, and no apps/ios line names the word limb (g) tracks. FOOTER_SET
    gains the preview file; the basemap-resolve count moves to SURFACE_SET (same value today, one per map surface).
    ETA vs fastest from the response; the "estimate · no traffic data" badge shows whenever eta_is_estimate is true -
    always, today: the server always says so and the device has no learned-sample store yet. Hazard strip: one row
    per hazard run. Apple Maps from the preview (a new door) and departs-at (Brief) are out of scope.
  - R7 LIVE PLANNER. No deployed Worker URL is in the tree (wrangler.jsonc has no route) and no keychain
    InstallIDProvider exists (plan M6). PlanAdapter reads the base URL from UserDefaults `plan.base.url` (a launch
    argument sets it); with none, its planner answers routingOffline with zero requests. The install id is generated
    once and kept in UserDefaults until M6 moves it to the keychain.
  - R8 RED FIRST by name: the state-machine and copy-table tests are committed against stubs that compile and are
    wrong, run red, then the code. Population ops/mutate/plansheet.py (+_mutations, _run) with a literal floor;
    three entries shown MISSED against the stub-era suite subset, CAUGHT by name after.
  - R9 VERDICT. The local full P-SAFE-03 guard takes ~72 min here (T-0295): CI core + pins-source-only decide it;
    ios-compile and ios-screenshot decide the Apple half. Only touched digests are re-approved, each in this diff.
- 2026-10-07T13:08:55Z RED FIRST, by name. agent/claude-opus-5 (owner).
  - R10 NAME CLASH (ruled on contact): ScenicKit already has `PlanFailure` (Sources/ScenicKit/Plan/PlanFailure.swift,
    the CLI/engine's refusal enum). R1's payload-free mirror is named `PlanSheetFailure`; every ruling above that
    says PlanFailure for the sheet's enum means PlanSheetFailure. PlanFailureCopy / PlanFailureAction keep their names.
  - Committed at 29a604c7 against stubs that compile and are wrong (gate ignores the disclaimer, origin unrounded, a
    pick always fills the destination, budget unclamped, a stale reply lands, every copy row empty). Run:
    `swift test --scratch-path .build/t0294 --filter "PlanSheetTests|PlanFailureCopyTests|PlanSheetGateTests"` ->
    "Test run with 17 tests in 3 suites failed ... with 54 issues", exit 1. Red by name (issue counts):
    P-SAFE-03 from first launch no plan request before acceptance (2); P-PRIV-06 typed start leaves as ONE coordinate
    at 2 dp (2); first launch: no ticket until the disclaimer is accepted (2); the ticket is the typed start at 2 dp
    ... whole (2); choosing fills the field being searched (2); no ticket from idle, searching or planning (2); a
    reply lands only on the ticket in flight (1); the extra time is clamped to 0...180 at every bound (12); every
    PlanSheetFailure has its one copy line and one action (13); copy lines are calm (13); the table covers all
    thirteen PlanError cases (1); a 200 reaches the sheet as the preview (1); Worker failures and a dead network
    reach the sheet as failed (1). Green from the start, as they test code the stubs did not touch: the PlanError
    mapping (13 cases), the ETA line, the button words, the failure-table count.
  - Two harness facts met on the way, fixed in the tests: Swift Testing's #require/#expect cannot take a mutating
    call (`startPlanning()` hoisted into a let), and an untyped tuple-literal `arguments:` table of PlanError cases
    pinned one swift-frontend for 15+ minutes on this box (now typed `[(PlanError, PlanSheetFailure)]`).
  - ios-compile and ios-screenshot are workflow_dispatch only: dispatched on task/T-0294 (runs 37626118143,
    37626129739).
- 2026-10-07T14:17:04Z GREEN, population, merged head. agent/claude-opus-5 (owner).
  - GREEN at df205586: the same filter -> "Test run with 17 tests in 3 suites passed", exit 0; on the merged head
    06f2980d (origin/main a7005872 merged, no Swift change from main) again 17/17, exit 0.
  - POPULATION ops/mutate/plansheet.py: 27 entries (MIN_MUTATIONS 27), 1 EQUIVALENT (E1, witness in the file).
    --prove-floor: "FLOOR PROOF OK: 7 of 7 arms refused and the control did not". Entries 1, 5, 13 with the three
    test files emptied (--prove-vacuity --only 1,5,13): MISSED 3 of 3, "VACUITY PROOF OK"; with them (--only
    1,5,13): "caught 1 the gate ignores the disclaimer by: first launch: no ticket until the disclaimer is accepted,
    then one | P-SAFE-03 ...", "caught 5 the origin unrounded by: P-SAFE-03 ...", "caught 13 a stale reply lands by:
    a reply lands only on the ticket in flight; a stale one is dropped" - "MUTATE OK caught=3/3". The full 27-entry
    run is NOT done here (each mutant is a ScenicKit rebuild on a box shared with other sessions); owner-approved
    faster verification, recorded as open.
  - GATES on the merged head: check-mutate-population exit 0 after PlanError.swift left SUBJECT_MODULES (it is
    already allowlisted; entry 27 still mutates it); CI round 1 (PR #187) refused P-PROC-06 for that and P-ATTR-01
    "a presentation over the map outside its approved site" (the shell's new overlay and plan sheet) - the two shell
    lines are typed into check-map-attribution-sheet's whitelist in this commit. ios-compile 37626118143 and
    ios-screenshot 37626129739 green on the branch.
- 2026-10-07T14:48:23Z PRE-REVIEW SURVIVORS M1 and M3b closed by CLASS. agent/claude-opus-5 (owner).
  - FOUND (pre-review mutant pass on 06f2980d, filter as above: baseline 17/17, each survivor 17/17 exit 0):
    M1 "the retry path skips the disclaimer" - `guard disclaimerAccepted` moved into the .chosen/.preview arm, so a
    ticket from .failed was issued with acceptance withdrawn (P-SAFE-03 open on one path); M3b "the extra-time
    control moves while a plan is in flight" - setBudget's `.planning` early return dropped. No test withdrew
    acceptance after a first plan, none called setBudget between startPlanning() and finish().
  - RULED (no Sources/ change: PlanSheet.swift already holds both properties, so no digest is re-approved). The
    classes, not the two spellings: (1) the gate refuses on EVERY launch state, not only the first launch; (3) every
    input is frozen while a ticket is in flight. New tests:
    PlanSheetTests "the gate holds on every path: acceptance withdrawn, no ticket from chosen, failed or preview"
    (arguments chosen/failed/preview; each row reached with acceptance on, its state recomputed per row by
    expectedState(path); withdrawn -> nil and state unchanged; re-accepted -> serial 1 or 2, so a refusal spends no
    serial); PlanSheetTests "inputs are frozen while a plan is in flight: the budget, a search, a pick" (setBudget at
    Int.min, -1, 0, 44, 46, 90, 180, Int.max in flight -> 45 and .planning(ticket); search/choose/endSearch in flight
    -> no change; landed preview's ticket and sheet both 45; after landing setBudget(90) moves and the next ticket
    carries 90); PlanSheetGateTests "P-SAFE-03: after a failure or a preview, no request once acceptance is
    withdrawn, through the planner" (counting transport: 429 path stays at 1 and .failed unchanged; 200 path stays
    at 1 and .preview unchanged; re-accept -> 2).
  - POPULATION rows 28 (M1 verbatim), 29 (its sibling: a re-plan from a preview skips the disclaimer), 30 (M3b
    verbatim); MIN_MUTATIONS 27 -> 30. Committed at c755c323 BEFORE the killers:
    `python ops/mutate/plansheet.py --only 28,29,30` -> "MISSED 28 ... MISSED 29 ... MISSED 30 ... no test objected",
    "MUTATE FAILED caught=0/3", exit 1. Killers committed at c5de11d3, same command -> "caught 28 the retry path
    skips the disclaimer by: the gate holds on every path ... | P-SAFE-03: after a failure or a preview ...",
    "caught 29 ... by: (the same two)", "caught 30 the budget moves while a plan is in flight by: inputs are frozen
    while a plan is in flight ...", "MUTATE OK caught=3/3", exit 0. --prove-floor: "FLOOR PROOF OK: 7 of 7 arms
    refused and the control did not". check-mutate-population.py: "the floor of 74 holds", exit 0.
  - TESTS: `swift test --scratch-path .build/fm-t0294 --filter "PlanSheetTests|PlanFailureCopyTests|PlanSheetGateTests"`
    -> "Test run with 20 tests in 3 suites passed", exit 0. wc -l: PlanSheetTests.swift 190, PlanSheetGateTests.swift
    169 (cap 300).
- 2026-10-07T15:10:00Z CI on the merged head 0785a182 (PR #187): core and pins-source-only RED, both on P-ATTR-01
  only - "a presentation over the map outside its approved site: .sheet( at ...ScenicHomeScreen.swift(1)
  ScenicDrive/ScenicDriveApp.swift(2), tracked ...ScenicHomeScreen.swift(1) ScenicDrive/ScenicDriveApp.swift(1);
  presentationDetents at Packages/ScenicApp/Sources/FeaturePlanSheet/PlanSheetScreen.swift(1), tracked nowhere".
  NOT caused by this round (the survivor commits touch only tests, ops/mutate and this Log). CAUSE: round 1's
  "shell presentations whitelisted" (2a18cee7) never whitelisted anything - it added two more scalar assignments of
  SHELL_PRESENTATION, the last one the Settings line again, so the check is byte-for-byte as strict as before. OPEN,
  for a ruling rather than a whitelist: the plan sheet's `.presentationDetents([.medium, .large])` puts a system
  sheet over the bottom half of the home map, where its credit pill is - exactly what the check exists to refuse
  (P-ATTR-01, "visible on every map surface at every sheet detent"). A candidate (drop the .medium detent so the
  sheet opens full height like Settings, approve the shell's `.sheet(isPresented: $isPlanning) {` by whole line,
  re-approve PlanSheetScreen.swift's -pinned digest) was drafted and NOT committed: changing a P-ATTR-01 guard
  needs the owner's or reviewer's ruling, not the author's.

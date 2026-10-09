---
id: T-0336
title: ios-screenshot shows every screen the owner will design against and the App Store will list - the route preview (with badge, explanation, hazard strip), the honest-failure card, Surprise, the loop preview, the road-trip itinerary, onboarding with the disclaimer, the Saved tab and Legal/Attribution - each a DEBUG `-screen` rehearsal over fixed sample data, light and dark
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T05:07:10Z
lease_expires_at: 2026-10-09T15:07:10Z
worktree: .worktrees/T-0336
branch: task/T-0336
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, .github/workflows/ios-screenshot.yml, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-ATTR-01, P-SAFE-03, P-SAFE-07]
reviewer: agent/rv1-t0336
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the shots ios-screenshot takes today (home x2 detents, settings, paywall, surprise, drive), how a `-screen <name>` DEBUG rehearsal is wired (T-0324 DriveRehearsal: the shell carries no `#` directive), which guard rows each new rehearsal raises (check-map-attribution, check-safety-disclaimer frozen/pinned, ios_screenshot_pinned.py, ios-compile-guardrails), and the sample data each screen shows - real LA place names from the corpus/curated seeds, never invented business names; the estimate badge visible on the preview"
  - "New shots, light and dark: preview, nothingPretty, surprise (if not already the card), loop, trip, onboarding, saved, legal - every map surface in them shows its attribution (P-ATTR-01 green, raised by name where a new surface appears), the preview shows the safety line (P-SAFE-03) and the estimate badge (P-SAFE-07); every rehearsal is DEBUG-only (a release build carries none - a guard row seen red then green)"
  - "ios-compile + ios-screenshot pass; the owner can open one artifact with every screen; the shots are looked at and quoted in the Log (what each shows, anything clipped or illegible filed as a follow-up, not fixed here)"
---
## Brief

Owner asked (2026-10-08) whether the UI needs design work and offered Claude Design; the answer was yes, before human
gate #1 and the M8 listing - but CI only shoots home, settings, paywall, surprise and drive, so most screens cannot be
seen without a Mac. This task makes every screen visible in one ios-screenshot artifact, so the owner can design
against the real current state. It changes no screen's design. Snapshot references are not recorded here (CLAUDE.md:
human-initiated only).

## Log
- 2026-10-09T05:06:37Z filed by agent/claude-opus-5 (orchestrator) for the owner's design pass and the M8 listing.
- 2026-10-09T05:07:10Z claimed by agent/claude-opus-5; lease until 2026-10-09T15:07:10Z
- 2026-10-09T05:15:12Z agent/claude-opus-5 (owner) MEASURE then RULE FIRST, before any code.
  MEASURED on e966755d. The shots today: ios-screenshot.yml's capture loop (pinned whole by
  ops/lib/ios_screenshot_pinned.py CAPTURE_RUN) `for SHOT in collapsed medium fastest settings paywall surprise drive`,
  light and dark, 14 PNGs. Downloaded run 37884547218 (task/T-0329, success, 2026-10-09T04:34Z) and LOOKED:
  home-light-collapsed, settings-light and surprise-light are the SAME picture - onboarding's vehicle step ("What are
  you driving?", five rows, Continue) over a green strip. On a fresh simulator ScenicHomeScreen's `.task` raises
  SafetyDisclaimer (acknowledgement absent, `vehicle.profile.v1` absent) and it wins over Settings and over the
  Surprise card; only drive-* (a root swap, no home) shows its own screen. So today ONE of seven screens is visible.
  How a rehearsal is wired (T-0324): `-screen <name>` lands in UserDefaults' argument domain and is read only
  inside `#if DEBUG` by a feature type (LaunchScreen: settings/paywall; SurpriseSlot: surprise; DriveRehearsal:
  drive); the shell carries no `#` directive (check-safety-disclaimer-frozen). Every `"screen"` key site: LaunchScreen
  lines 16/21, SurpriseSlot 13/19, DriveRehearsal 31/42 - each read inside DEBUG. No guard checks that today: moving a
  read out of `#if DEBUG` is refused by nothing but the digest pins (a re-approval, not a refusal).
  Map surfaces: MapView at ScenicHomeScreen and DriveScreen only; PlanPreviewCard draws PlanRouteShape (a SwiftUI
  Shape, no tiles) and carries AttributionFooter. LoopPreviewCard / TripItineraryCard / Saved / Legal mount no map.
  LiveCorpus.offersDownload needs a `corpus.manifest` URL default - absent on CI, so no download sheet on any shot.
  Sample data, MEASURED from apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite `places` (1334 rows): Topanga (town,
  id 710486223536647933, 34.0897,-118.6030), Zuma Beach (161142772170980305, 34.0189,-118.8274), Top of Topanga
  Overlook, Mulholland Scenic Overlook, Griffith Observatory, Leo Carrillo State Beach (8813832245607821419),
  Point Dume; the preview line follows Routes/saddle-peak.geojson's own quartile points (Saddle Peak, the owner's
  drive) then the coast to Zuma. Hazard kinds from Tests/ScenicAPIClientTests/PlanClientResponseTests (`road_access:
  destination`). services/etl/regions/la/curated.yaml does not exist on main; the corpus is the source.
  R1 ONBOARDING DONE BY ARGUMENT, NOT BY CODE: every shot except onboarding/disclaimer launches with
  `-safety.disclaimer.acknowledged.v1 YES -vehicle.profile.v1 standard` - the argument domain, volatile, never
  written; no app code writes either key (the one writer stays SafetyDisclaimer's accept). This is what makes home,
  settings, paywall and surprise show their own screens for the first time. RISK, stated: whether @AppStorage(Bool)
  reads the argument domain's `YES`; the first run's shots decide, and if not the fallback is ruled in the Log then.
  R2 NEW SHOTS (light+dark): onboarding (vehicle step, no arguments), disclaimer (`-screen disclaimer`: FeatureScenicHome
  `OnboardingRehearsal.atLaunch` hands SafetyDisclaimer an Onboarding advanced by `.next`, its own public event),
  preview, nothingPretty, loop, trip, saved (`-screen <name>`: FeaturePlanSheet `PlanRehearsal`; the shell's one
  line `@State private var isPlanning = PlanRehearsal.opensSheet` - frozen row re-typed; PlanSheetScreen seeds its
  sheet/trip/loop/tab state from the rehearsal; SavedDrivesList loads the rehearsal rows instead of the shelf), legal
  (`LaunchScreen.legal` - Settings opens and pushes LegalAttributionScreen; no shell edit). Surprise keeps its
  existing `-screen surprise` (R1 makes it the card).
  R3 THE GATE IS NOT BYPASSED IN CODE THAT SHIPS: a rehearsal state is built through each machine's public API -
  `PlanSheet(disclaimerAccepted: true)`, search/choose, `startPlanning()` (the gate's own ticket), `finish` with a
  fixture outcome; no planner is called, nothing reaches the network. The fixtures live in
  `PlanRehearsalFixtures`, a file wholly inside `#if DEBUG`; `PlanRehearsal.atLaunch` is nil in release. The
  preview's fixture has `etaIsEstimate: true` (P-SAFE-07's badge) and PlanPreviewCard draws `PlanPreview.conditions`
  (P-SAFE-03's line) and its AttributionFooter (P-ATTR-01) unchanged.
  R4 GUARD ROWS RAISED BY NAME: (a) NEW ops/lib/check-screen-rehearsals.py, added to P-SAFE-03's assertion: a
  whole-line whitelist of every apps/ios Swift line naming `"screen"`, `launchArgumentKey` or `PlanRehearsalFixtures`
  or `OnboardingRehearsal`, each approved line marked DEBUG-only where it reads the argument, and the fixtures file
  required wholly inside `#if DEBUG`; seen red (--prove-red) then green. (b) check-safety-disclaimer -frozen
  FROZEN_APP_SHELL (the isPlanning line), -pinned and -linked-digests rows for every touched file. (c)
  ios_screenshot_pinned.py CAPTURE_RUN re-typed, with a prove-red row for the new shots. (d) check-map-attribution:
  no new map surface, so no surface row; its content pins re-approve via the digests. (e)
  check-ios-compile-guardrails.py reads the workflow through (c).
  R5 NO DESIGN CHANGE: no view's layout, copy or token changes; what is clipped or illegible is filed, not fixed.
  Snapshot references are not recorded (CLAUDE.md).
- 2026-10-09T05:53:29Z agent/claude-opus-5 (owner) RED then GREEN by name, iOS CI, every shot LOOKED AT.
  Correction to the 05:15 entry: the corpus offer's default is `LiveCorpus.manifestURLKey` (not "corpus.manifest"); the
  measured fact (absent on CI, so offersDownload is false) stands. R6 (ruled during build): the capture step's cap is
  timeout-minutes 30, held; MEASURED on run 37884547218 the first launch took 5.7 min and each later shot ~18 s, so
  16 more shots fit (this run: capture 10m16s, 05:40:57-05:51:13).
  Guards, each seen red before its row was raised: check-ios-compile-guardrails.py with the workflow edited and the pin
  not: `IOS-COMPILE-GUARDRAILS: workflow.jobs.simulator-screenshot.steps[4].run: differs from the pinned value`, then
  OK; `--prove-red` `PROVE-RED OK: 72 mutations red` (69 + T-0336's three: onboarding done for no shot, the plan-sheet
  shots dropped, the onboarding and legal shots dropped). check-safety-disclaimer: `the app shell ScenicDriveApp line 3
  of 41 ...: approved \`@State private var isPlanning = false\`, found \`@State private var isPlanning =
  PlanRehearsal.opensSheet\`` then `FeatureScenicHome's file set is not the approved one: added
  OnboardingRehearsal.swift.` until FROZEN_APP_SHELL and -pinned's rows (SafetyDisclaimer, OnboardingRehearsal,
  LaunchScreen, SettingsScreen, PlanSheetScreen, SavedDrivesList, PlanRehearsal, PlanRehearsalFixtures, the shell) were
  re-typed; then green. check-store-links.py: the frozen Entitlements hashes for LaunchScreen/SettingsScreen, then
  `LegalAttributionScreen(: an unapproved line ... \`LegalAttributionScreen()\`` and `LaunchScreen.atLaunch: an
  unapproved line ... \`@State private var isShowingLegal = LaunchScreen.atLaunch == .legal\``; approved in
  store_links_pinned.py; green, `--prove-red` `33/33 rows as required`. NEW check-screen-rehearsals.py (P-SAFE-03's
  assertion): green `11 approved -screen sites, every read inside #if DEBUG, PlanRehearsalFixtures.swift wholly
  DEBUG-only`; `--prove-red` `PROVE-RED OK: 11/11 refused by name` (each read moved out of DEBUG or into #else, the
  fixtures compiled in release or closed early, the shell reading -screen, a new feature file reading it, the
  fixtures used from the shell). check-map-attribution green with no surface row raised (no new map mount).
  iOS CI on dfde674f: ios-compile 37889171643 success; ios-screenshot 37889174904 success, 30 PNGs. R1 HELD: the
  argument-domain acknowledgement is read by @AppStorage - home, settings, paywall and surprise show their own screens
  for the first time. LOOKED AT every PNG (light | dark):
  home collapsed/medium/fastest: the demo-tile map with the Saddle Peak lines, MapLibre logo, the credit pill
  `© MapLibre · Natural Earth · © OpenStreetMap contributors` above the sheet at both detents and both looks; the sheet
  "Saddle Peak · Topanga to Malibu", three chips (Fastest 6.1 km, +13 min 21.5 km, +18 min 26.2 km), the conditions
  line, Open in Apple Maps; medium adds the road list and the copy. settings: Subscription (Not subscribed, Scenic Drive
  Pro, Restore, Manage), Vehicle Standard car, Offline places toggle, About cut at the bottom edge (a scroll, fine).
  paywall: "Subscription Unavailable - unavailable in the current storefront" (the simulator has no StoreKit config),
  Terms/Privacy links. surprise: the card over the map (light Tongva Peak, dark Surfrider Beach - the deck picks
  differently per launch), the estimate badge on the round-trip line, Not this one? four reasons; the map credit pill
  stays visible below the card. drive: unchanged from T-0324 (minimal surface, composed credit, End drive).
  onboarding: "What are you driving?", Standard car checked, four disabled rows, Continue. disclaimer: "Before you
  drive", the body, the bold conditions line, Back, I understand. preview: "Zuma Beach", the route outline, `55 min ·
  20 min longer than the fastest way`, the badge `estimate · no traffic data` (P-SAFE-07), `road_access: destination`,
  bold `Conditions change. Verify locally.` (P-SAFE-03), Save this drive, Start the drive, Choose another place, the
  footer `Route data © OpenStreetMap contributors`. nothingPretty: "Not much pretty within reach of this drive. More time
  might find some." and Choose another place. loop: "A loop from Topanga and back", About 58 min, 32 mi, asked for 60,
  the badge, doubles back 4% inside 15%, Open the loop in Apple Maps, conditions, Change the loop. trip: "2 days to Leo
  Carrillo State Beach", 2 h 30 min, 40 min more, the badge, Day 1 1 h 30 min · 43 mi with the night's-stop note, Day 2
  1 h 0 min · 31 mi, conditions, Change the trip. saved: Mulholland Scenic Overlook (Needs a re-plan · 60 min extra),
  Top of Topanga Overlook (45), Zuma Beach (30), each with Drive it again / Rename / Delete. legal: Legal & Attribution,
  the ODbL notice word for word, openstreetmap.org/copyright.
  FOLLOW-UP CANDIDATES (seen, not fixed - R5): (1) home: the `Plan a drive` button overlays the first menu chip - the
  chip's own text ("Saddle Peak", "Westwood loop") shows through behind it, at every home shot, both looks; (2) preview:
  the hazard strip prints raw API keys (`road_access: destination`), and the route outline is drawn in unscaled
  lon/lat with no basemap, so it reads as a chart, not a road; (3) onboarding: the disabled vehicle rows' explanation
  lines are low-contrast grey on the dark sheet; (4) paywall: no product renders on CI (no StoreKit configuration in the
  simulator), so the listing's paywall shot needs one; (5) the plan sheet's bottom toolbar pair (`Plan a road trip` /
  `Just drive a loop`) changes meaning per tab - a design question for the owner's pass.
- 2026-10-09T06:40:42Z agent/rv1-t0336 (reviewer, not the owner) REVIEW PASS on 6d8b64e2 (PR #221), detached worktree
  .worktrees/rv1-t0336. BARE on the head, every one exit 0: check-safety-disclaimer, check-map-attribution,
  check-store-links.py, check-drive-display.py, check-ios-compile-guardrails.py (both workflows equal the pinned ones),
  check-pbxproj-graph.py (28 assertions, 0 failed), check-screen-rehearsals.py ("11 approved -screen sites, every read
  inside #if DEBUG, PlanRehearsalFixtures.swift wholly DEBUG-only"), check-screen-rehearsals.py --prove-red ("PROVE-RED
  OK: 11/11 refused by name"), ios_screenshot_pinned.py, check-line-cap (518 Swift files, none over 300),
  check-pins-yaml.py (pins=49 fields=395), queue-check (QUEUE OK, 327 tasks). gh pr checks 221: core pass,
  pins-source-only pass. gh run list --branch task/T-0336 on the head 6d8b64e2: ios-compile 37891403662 success,
  ios-screenshot 37891406542 success (also dfde674f: 37889171643 success, 37889174904 success). merge-base
  --is-ancestor origin/main (4537e7d4) origin/task/T-0336: yes, no drift. Diff touches neither project.pbxproj nor
  either Package.swift; the new files import only Foundation and ScenicKit; the shell's one change is
  isPlanning = PlanRehearsal.opensSheet (nil-backed, false outside DEBUG).
  SHOTS LOOKED AT (run 37891406542, 30 PNGs, every one): plan-preview light/dark - Zuma Beach, 55 min / 20 min longer,
  the estimate badge, the hazard row, "Conditions change. Verify locally." bold, Save / Start the drive / Choose another
  place, and the "Route data (c) OpenStreetMap contributors" footer under the drawn outline; nothingPretty - the honest
  card and Choose another place; loop and trip - badge and the conditions line in both; saved - three corpus rows;
  legal - the ODbL notice; onboarding - the vehicle step; disclaimer - Before you drive, the bold conditions line, Back,
  I understand; surprise - the real card (Tongva Peak / Surfrider Beach) with the badge, the map credit pill visible
  below it; home collapsed / medium / fastest light and dark - the credit pill above the sheet at both detents;
  settings and paywall - their own screens now (Standard car, Subscription Unavailable). Nothing required is clipped.
  The owner's five follow-up candidates are confirmed as seen (the Plan a drive button over the first chip; raw
  road_access key; the rest as written); none hides a required element.
  REVIEWER MUTANTS (each applied alone, restored, tree clean after): RV-M1 PlanRehearsal's read under
  "#if DEBUG || true" - refused BY NAME by check-screen-rehearsals.py ("reads the -screen argument outside #if DEBUG"),
  also by the digest pins. RV-M3 a new FeaturePlanSheet/PlanMapPreview.swift mounting MapView(styleURL:..., route:)
  with no AttributionFooter - refused BY NAME by check-map-attribution's (f) map-surface whitelist. RV-M2
  OnboardingRehearsal.atLaunch calling onboarding.send(.next) outside the #if DEBUG arm (release skips the vehicle step;
  the disclaimer still gates) - refused only by the sha256 digest pins (OnboardingRehearsal.swift content changed), the
  rehearsal guard stays green: its whitelist covers -screen reads, not unconditional machine events in a rehearsal
  type. Recorded, not blocking: no safety gate is bypassed and the digest is a refusal by file name.
- 2026-10-09T07:00:50Z agent/claude-opus-5 (owner) MERGE-MAIN ROUND after the sign-off at 6d8b64e2: main took PR #219
  (T-0334: PlanOffer, PlanSheetState.offered, PlanOfferCard wired into PlanSheetScreen). git pull; git fetch origin;
  merge origin/main (4617eddd) = 122a78a4; main then took queue-only 9541b726, 564e6626 (T-0330), merged clean after this commit. ONE conflict: ops/lib/check-safety-disclaimer-pinned, the
  PlanSheetScreen.swift row (ours b7343dde..., main's 02fa02bf...). The Swift auto-merged with BOTH sides: T-0334's
  `case .offered(_, let offer): PlanOfferCard(...)` wiring AND T-0336's `PlanRehearsal.atLaunch` init hook; the row
  recomputed from the merged tree (sed 's/\r$//' | sha256sum) = fab8d6f10d57a02c25631448abc39d445b0f573158371898de58f855c7a8762d.
  Only those two paths differ from both parents (pre-commit: "checking touches: against the 2 path(s)"); digests.txt
  and the other lists merged clean (no row changed on both sides). Merge message carries the attribution line.
  RULED (rv1-t0334 recordable 1, T-0334 stillOpen: the offer card has no shot): a `plan-offered` rehearsal.
  R-A sample: the Brief's westwood-malibu-like numbers - budget 25, try 65, all back roads about 60 min / 32 extra -
  as PlanRehearsalFixtures.offer = PlanOffer(budgetMinutes: 25, moreTimeMinutes: 65, backRoadsEtaSeconds: 3_600,
  backRoadsBudgetMinutes: 32), reached through the machine's API: PlanSheet(disclaimerAccepted: true,
  budgetMinutes: 25), search/choose, the gate's startPlanning(), finish(ticket, with: .offered(offer)). The places
  stay Topanga -> Zuma Beach (corpus ids already verified for the preview) rather than a Westwood row nobody has looked
  up in the corpus; the copy shows only the offer's numbers, so the route pair does not appear on the card.
  R-B launch value `-screen offered`, shot names plan-offered-light/-dark (the loop's NAME=plan-$SHOT-$LOOK).
  R-C cap: run 37891406542 (30 shots) took 18m07s (06:01:38 -> 06:19:45) against timeout-minutes: 30; two more shots
  at SETTLE=15 add well under a minute - 32 shots fit, the shot is NOT skipped.
  Rows raised BY NAME, each seen red then green: check-ios-compile-guardrails.py with the workflow edited and the pinned
  module not yet -> "workflow.jobs.simulator-screenshot.steps[4].run: differs from the pinned value", FAIL; after
  ios_screenshot_pinned.py CAPTURE_RUN/SHOTS_LIST took `offered` -> "ios-screenshot.yml equals the pinned workflow", OK.
  New --prove-red row "T-0336: the plan-offered shot dropped (T-0334's offer card unseen)" -> [red rc=1]; PROVE-RED OK:
  73 mutations red, 6 legitimate spellings green. check-screen-rehearsals.py new row "T-0334's offer sample named
  outside DEBUG (a release plan-offered state)" -> [refused] "`static let offered = PlanRehearsalFixtures.offer` at
  .../PlanRehearsal.swift is not an approved -screen site"; PROVE-RED OK: 12/12 refused by name (was 11/11).
  Digests re-approved in -pinned: PlanRehearsal.swift b5c84b13... (doc line names `offered`), PlanRehearsalFixtures.swift
  88756130... (127 lines). BARE on the change, every one exit 0: check-safety-disclaimer, check-map-attribution,
  check-store-links.py, check-screen-rehearsals.py ("11 approved -screen sites, every read inside #if DEBUG,
  PlanRehearsalFixtures.swift wholly DEBUG-only"), check-ios-compile-guardrails.py (both workflows equal the pinned),
  check-line-cap ("524 Swift files tracked ... none over 300 lines"), check-pins-yaml.py ("pins=49 fields=395").
- 2026-10-09T07:23:06Z agent/claude-opus-5 (owner) CI on the pushed head 4a89e3ec: ios-compile 37896751258 success (07:02:19 ->
  07:05:56), ios-screenshot 37896754771 success (job 07:02:31 -> 07:21:29, 18m58s for 32 shots, under the 30-minute
  cap), linux-core 37896754126 success. Downloaded to .artifacts/t0336-r2-shots: 32 PNGs, plan-offered-light/-dark among them.
  SHOTS LOOKED AT: plan-offered light and dark show "Plan a drive", the line "Not much pretty within 25 extra minutes of
  this drive.", two filled buttons "Try 65 extra minutes" and "All back roads: about 60 min, 32 extra minutes" (the
  second wraps to two lines, nothing clipped), and "Choose another place". In dark mode the buttons are light orange
  with dark text, which reads. The card has no map surface, so it needs no credit (P-ATTR-01), and it is not a route
  screen. plan-preview light and dark are unchanged by the merge: Zuma Beach, the outline, "55 min · 20 min longer
  than the fastest way", the "estimate · no traffic data" badge, road_access: destination, the bold "Conditions
  change. Verify locally.", Save this drive / Start the drive / Choose another place, and the "Route data ©
  OpenStreetMap contributors" footer.
- 2026-10-09T07:37:11Z agent/claude-opus-5 (owner) gh pr checks 221 on 2f215d37: core pass 6m56s, pins-source-only pass 2m8s. Main then took
  PR #220 (T-0335: services/api, ops/lib/named-tests.json) and the T-0337 queue moves; merged clean as 21551365 (no
  conflict, no Swift, workflow or digest path touched). Bare gates re-run on the merged head below; the iOS runs
  above stand, because no apps/ios, Sources/ or workflow file changed.

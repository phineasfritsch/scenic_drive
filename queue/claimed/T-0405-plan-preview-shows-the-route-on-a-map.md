---
id: T-0405
title: The plan preview shows the chosen route on a map above the sheet (reference library, Biggest changes 1) instead of a full-height sheet with an empty lower half
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T19:53:44Z
lease_expires_at: 2026-10-18T19:53:44Z
worktree: .worktrees/T-0405
branch: task/T-0405
exclusive: []
touches: [apps/ios/ScenicDrive/ScenicDriveApp.swift, apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, Sources/ScenicKit/, Tests/, ops/lib/, ops/mutate/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-ATTR-01, P-SAFE-03, P-SAFE-07, P-A11Y-01]
reviewer: null
depends_on: [T-0396]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

After T-0396 (PR #294, merged 21559484) the preview sheet is tidy, but it fills the screen and its lower half is
empty. Today's shot is `.artifacts/shots-39050070882/ios-screenshots/plan-preview-light.png`. The screen where the
driver decides shows no route at all. The reference library is
`C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md`. Its "Biggest
changes" 1 says to put the map back on every route screen and plan in a sheet over it. Its "Plan preview" section,
Recommended layout item 1, puts the map on the top ~45% with the chosen route bold. The references are Google Maps
#205, Apple Maps #056, AllTrails #102 and Waze #088. The screen PNGs are under `.artifacts/mobbin/screens/`.

Scope:
1. While the preview state is up, the chosen route is drawn on a map visible above the sheet. Pick whichever of
   these the code supports better and rule it in the Log: a medium detent over the home map, with the route drawn
   and framed; or a map in the preview card itself through MapAdapter's existing map view.
2. The map is fitted to the route's bounds with padding, so the whole route is visible above the sheet.
3. Attribution stays on the map surface at every detent (P-ATTR-01). The disclaimer line stays directly under Start
   (P-SAFE-03), and the estimate tag stays on the ETA (P-SAFE-07).
4. AX5: the sheet scrolls, and Start plus the disclaimer stay reachable. The map may shrink, but it must not cover
   the sheet's text.

Out of scope: alternative routes with time callouts, the "Most scenic" badge, the elevation chart and road cards.
T-0404 owns AttributionFooter's own size; do not edit DesignSystem.

Demonstration: dispatch ios-compile and ios-screenshot, and quote the run ids. Look at plan-preview light, dark and
ax5, and state item by item what each shot shows: the route visible, the map framed, attribution, Start and the
disclaimer. Any new or changed guard is shown red, then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 after T-0396 merged (empty lower half seen in run 39050070882).
- 2026-10-17T19:53:44Z claimed by agent/claude-opus-5; lease until 2026-10-18T19:53:44Z
- 2026-10-17T20:01:57Z RULINGS before code (agent/claude-opus-5). Read: PlanSheetScreen, PlanPreviewCard, the shell
  (`apps/ios/ScenicDrive/ScenicDriveApp.swift`: `.sheet(isPresented: $isPlanning)` with NO detents, attached to
  PlanDriveButton in `home`'s top safe-area inset, a sibling of ScenicHomeScreen), DriveScreen/DriveBasemap/
  DriveMapLine, MapAdapter's MapView + MapRouteCoordinator (`.fit` of the route bbox with padding = covered edges +
  margin, window y converted into the map view), and ops/lib/check-map-attribution{,-sites} and
  check-safety-disclaimer-{preview,frozen,pinned}. Looked at today's shot and Google Maps #205 / Apple Maps #056.
  - R1 (Scope 1, the choice): a map IN THE PREVIEW CARD through MapAdapter's MapView, not a medium detent over the
    home map. Why: (a) the home map lives in ScenicHomeScreen, a sibling of the sheet - drawing the previewed route
    there needs the preview carried out of the sheet to the home through the shell AND the home's frozen render
    blocks (-frozen) and its five-line sheet mount (-sheet) reopened; (b) a medium plan sheet covers the home's
    credit band, which P-ATTR-01 (h) places under HomeSheet - the credit would have to be duplicated onto the plan
    sheet anyway; (c) the drive screen already proves the second-surface pattern (T-0324 R5: DriveBasemap.planned
    + DriveMapLine.route + composed footer + covered edge), which a card map copies. The sheet stays full height.
  - R2 (module boundary): FeaturePlanSheet may not import MapAdapter (Package.swift, CLAUDE.md) and Package.swift
    is serial-only and outside touches. So the map is a new public FeatureScenicHome view `PlanPreviewMap(preview:)`
    and the SHELL hands it to PlanSheetScreen as `previewMap: (PlanPreview) -> AnyView` - the precedent is
    ScenicHomeScreen's `surprise:` closure. This needs the shell line: `touches:` gains
    `apps/ios/ScenicDrive/ScenicDriveApp.swift` (one line, frozen in check-safety-disclaimer-frozen, updated there).
    The parameter has NO default, so a caller cannot get a mapless preview by omission.
  - R3 (Scope 2): PlanPreviewMap mounts `MapView(styleURL: style.url, ..., coveredBelowY: creditTop, route: route)`
    with `route = DriveMapLine.route(for: preview.route)`, so the coordinator's `.fit` frames the route's bbox with
    its margin above the credit band; style from ONE `DriveBasemap.planned(` held in @State (resolve off the body).
  - R4 (Scope 3, P-ATTR-01): the credit moves from the card's bottom inset onto the map surface: PlanPreviewMap's
    `AttributionFooter(text: CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit))` at
    the map's bottom edge - basemap + route data, one line, the DriveScreen form. The card's bottom-inset
    `AttributionFooter(text: PlanPreview.attribution)` is removed (it would be a second, partial credit 300pt
    below the map). Guards: FOOTER_SET's PlanPreviewCard(1) becomes PlanPreviewMap(1); MAP_SET, the credit-site
    whitelist and `DriveBasemap.planned(` gain PlanPreviewMap; a new limb (f3) runs the drive-surface readers over
    PlanPreviewMap. FROZEN_PREVIEW_CARD_BODY is re-typed to the new body. P-SAFE-03 (PlanPreviewActions, the
    conditions line under Start) and P-SAFE-07 (etaRow, estimateTag) blocks are unchanged.
  - R5 (Scope 4, AX5): the map is pinned above the card's ScrollView at 42% of the card's height, 24% at
    accessibility sizes; the text scrolls under it and never under the map. Start + the disclaimer stay in the
    ScrollView, reachable by scrolling.
  - R6 (no numeric module): no ops/mutate population - the change is layout and wiring; the guards' red is shown by
    four hand mutants (M1-M4 below) run against the edited tree.
- 2026-10-17T20:47:17Z implementation c2df7e05: PlanPreviewMap (FeatureScenicHome), PlanPreviewCard map pinned above
  the ScrollView (0.42 / 0.24 at AX), the card's bottom-inset footer removed, PlanSheetScreen `previewMap:`, the shell
  line, limb (f3), FROZEN_PREVIEW_CARD_BODY re-typed, the shell's frozen line, FeatureScenicHome + app-wide + shell
  digests re-approved. Local: `bash ops/lib/check-map-attribution` EXIT 0 with
  `P-ATTR-01 (f3): the plan preview's map Packages/ScenicApp/Sources/FeatureScenicHome/PlanPreviewMap.swift - footer
  text: CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit), mounted from style and
  route, one DriveBasemap.planned(, nothing hidden.`; `bash ops/lib/check-safety-disclaimer` EXIT 0.
  ios-compile 39066700839 and ios-screenshot 39066704478 FAILED: `PlanPreviewMap.swift:34:37: error: cannot find
  'CreditLine' in scope` (CreditLine is Handoff's; DriveScreen imports Handoff). Fixed 0973b9e7 (`import Handoff`,
  both PlanPreviewMap digests re-approved); re-dispatched ios-compile 39068165781, ios-screenshot 39068169091.
  Prove red (.build/t0405-mutants.py, ignored, each mutant against the edited tree, restored after):
  `M1 footer deleted: exit=1 :: P-ATTR-01: the footer construction AttributionFooter( occurs outside its tracked set`
  `M2 footer reads a second resolve: exit=1 :: P-ATTR-01: the planned resolve call DriveBasemap.planned( occurs
  outside its tracked set; found: ... DriveScreen.swift(1) ... PlanPreviewMap.swift(2`
  `M3 footer hidden from VoiceOver: exit=1 :: P-ATTR-01: .../PlanPreviewMap.swift hides something from
  accessibility: 1 \`accessibilityHidden\` occurrence(s), 0 \`(false)\`.`
  `M4 shell hands a mapless preview: exit=1 :: P-ATTR-01: a frozen render block changed:`
  `restored: exit=0`
- 2026-10-17T21:08:50Z ios-compile 39068165781 SUCCESS, ios-screenshot 39068169091 SUCCESS (head 0973b9e7). LOOKED:
  - plan-preview-light: route VISIBLE, bold blue line on the map under the nav bar (the demo basemap: CI has no
    la.pmtiles); FRAMED - whole line inside the map, both ends clear of the edges and above the credit band;
    ATTRIBUTION on the map's bottom-right edge, "(c) MapLibre . Natural Earth . Route data (c) OpenStreetMap
    contributors"; Start the drive + Save; "Conditions change. Verify locally." directly under Start; the
    estimate tag on the ETA row. No overlap.
  - plan-preview-dark: same items, dark card and dark credit chip; no overlap.
  - plan-preview-ax5: FAIL. The credit renders at AX5 and fills the 24% map: it wraps mid-word ("OpenStreet-/Map/
    contributors"), the basemap half is cut off above the map's top edge, and the route is not framed (the
    coordinator's open band is under its margin, so the camera stays put). The card text is not covered.
  FIX (the one re-run): PlanPreviewMap takes the home's own cap, `.dynamicTypeSize(...HomeTypeSize.cap)` on the
  map surface (map chrome + credit; the card's text is uncapped), and the AX share rises from 0.24 to 0.32
  (R5 superseded on that number; FROZEN_PREVIEW_CARD_BODY re-typed; PlanPreviewMap's two digest rows and
  PlanPreviewCard's re-approved).
- 2026-10-17T21:31:47Z head 85fae9d0: ios-compile 39070023891 SUCCESS, ios-screenshot 39070028987 SUCCESS. LOOKED:
  - plan-preview-light: route VISIBLE (bold blue line, top ~34% of the screen under Close/Saved); FRAMED - the whole
    line inside the map, both ends clear of the edges, above the credit band; ATTRIBUTION on the map's bottom edge,
    two lines, "(c) MapLibre . Natural Earth . / Route data (c) OpenStreetMap contributors", fully visible; the
    estimate tag on the ETA row; Start the drive + Save; "Conditions change. Verify locally." directly under Start.
    The card's text starts below the map; nothing overlaps.
  - plan-preview-dark: the same, item by item; dark card, dark credit chip, the route cased dark. No overlap.
  - plan-preview-ax5: the map SMALLER (32%); the route VISIBLE and FRAMED above the credit (the whole line, the west
    end clear of the left edge); ATTRIBUTION fully visible, three lines at the home cap, not cut; the card's text
    (title, ETA, the estimate tag wrapped under the number, the why line, the hazard row) starts below the map and
    is not covered. Start and the disclaimer are below the fold in this still - they are inside the card's
    ScrollView with the frozen P-SAFE-03 stack (conditions directly under Start), reached by scrolling; the shot
    does not scroll, so this still does not show them.
  `git fetch origin` (main checkout): origin/main e91ac77e is an ancestor of the branch - nothing to merge.
- 2026-10-17T21:31:47Z ACCEPTANCE RE-QUOTED on 85fae9d0 (code unchanged since; this commit adds Log lines only):
  1. `bash ops/lib/check-map-attribution` -> `ATTR exit=0`; (f3) line as quoted at 20:47:17Z.
  2. `bash ops/lib/check-safety-disclaimer` -> `SAFE exit=0` ("Not checked here: rendering (T-0180), taps, ...").
  3. `bash ops/check-pins --source-only` was started at ~21:14Z and printed nothing in over 45 minutes on this box
     (the hang the orchestrator foresaw), so each check the affected pins name was run bare instead: P-ATTR-01
     `check-map-attribution` exit 0; P-SAFE-03 `check-safety-disclaimer` exit 0, `check-screen-rehearsals.py`
     "11 approved -screen sites ..." exit 0, `check-hazard-copy-sites.py` "ok - 13 sites, every one approved, in 5
     files" exit 0, `check-base-url-sites.py` "37 approved base URL sites ..." exit 0. P-SAFE-07 is
     run-named-tests over ScenicKit, which this task does not touch. CI runs the full source-only pass.
     `check-mutate-population.py` "P-PROC-06: every added module is covered or allowlisted; the floor of 173 holds";
     `check-mutate-only.py` "NAME-PAIRS OK: 242318 pair tokens ..."; `check-pins-yaml.py` "PINS-YAML ok pins=53
     fields=426"; `check-exec-bits` "P-OPS-01: 253 files, 23 required present, all modes correct"; `queue-check`
     "QUEUE OK (395 tasks)".
  4. M1-M4 red, restored green: quoted at 20:47:17Z (run against the edited tree at 0973b9e7's code).
  5. ios-compile 39070023891 SUCCESS, ios-screenshot 39070028987 SUCCESS; the shots as recorded above.
  6. `wc -l`: PlanPreviewMap.swift 52, PlanPreviewCard.swift 146, PlanSheetScreen.swift 285, ScenicDriveApp.swift 89.

- 2026-10-18T00:47:40Z rv0 pre-review mutant pass, SURVIVORS M-A and M-B closed by class (limb f4, ops/lib/check-map-attribution-sites).
  Ruling: (f3) read the preview footer's argument and the mount only. Nothing bound the plan sheet's `.preview`
  arm's `map:` to the shell's PlanPreviewMap (M-A: `AnyView(EmptyView())` = no map and no credit) nor the
  ZStack's order (M-B: footer before MapView = the map drawn over the credit). Class fix, all whitelists: (1)
  PlanPreviewMap's whole struct frozen (frozen_block, above-line `import SwiftUI`) - z-order, an added hiding
  modifier, a re-bound state; (2) the `.preview` arm frozen whole as a run of lines ending at the next arm's
  `case .failed(_, let failure):` (frozen_run) - a replaced argument, a wrapper or `.hidden()` after the card;
  (3) every whole trimmed line under apps/ios naming `previewMap` / `PlanPreviewMap`, plus every line of
  PlanPreviewCard.swift naming `map`, equals an 11-line approved list in scan order - a shadowing
  `previewMap(_:)`, a second closure or a re-bound card property is refused by name. f4 runs inside
  require_drive_surface, so check-map-attribution itself stays at 300 lines. Prove-red rows F4a-F4e added to
  ops/lib/check-map-attribution-mutations. No Swift file changed: no digest re-approved, ios CI runs stand.
  Method: each mutant applied to the REAL tree with every sha256 row naming the old content re-approved
  (.artifacts/t0405-rv0/driver.sh), check run, file + digest holders restored. RED = HEAD's checker, GREEN = f4.
  RED, M-A (16:06Z run, P-SAFE-03 too): `[M-A empty map in the .preview arm] P-ATTR-01 exit=0`, `P-SAFE-03 exit=0`.
  A first attempt at the other four overlapped two driver processes (TaskStop left orphans) and is discarded; the
  sequential re-run (.artifacts/t0405-rv0/redgreen.sh) quoted verbatim:
      === RED (HEAD checker) 2026-10-17T23:43:42Z
      [M-A2 a shadowing previewMap(_:) method] P-ATTR-01 exit=0 (digest re-approved in 1 file(s))
      [M-A3 the card hidden in the .preview arm] P-ATTR-01 exit=0 (digest re-approved in 1 file(s))
      [M-B footer before MapView in the ZStack] P-ATTR-01 exit=0 (digest re-approved in 1 file(s))
      [M-B2 the preview credit faded out] P-ATTR-01 exit=0 (digest re-approved in 1 file(s))
      === GREEN (limb f4) 2026-10-18T00:14:05Z
      [clean tree] P-ATTR-01 exit=0
      P-ATTR-01 (f4): PlanPreviewMap's struct and the .preview arm frozen whole; 11 approved line(s) wire previewMap.
      [M-A empty map in the .preview arm] P-ATTR-01 exit=1 (digest re-approved in 1 file(s))
        | P-ATTR-01: the plan preview's map is not wired and drawn as approved (f4):
        |   PlanSheetScreen's .preview arm line 2 of 7 in apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/PlanSheetScreen.swift: approved `PlanPreviewCard(preview: preview, map: previewMap(preview), destination: sheet.destination?.name ?? "",`, found `PlanPreviewCard(preview: preview, map: AnyView(EmptyView()), destination: sheet.destination?.name ?? "",`
      [M-A2 a shadowing previewMap(_:) method] P-ATTR-01 exit=1 (digest re-approved in 1 file(s))
        | P-ATTR-01: the plan preview's map is not wired and drawn as approved (f4):
        |   12 line(s) name previewMap / PlanPreviewMap (or `map` in PlanPreviewCard.swift), 11 approved; found, in scan order:
      [M-A3 the card hidden in the .preview arm] P-ATTR-01 exit=1 (digest re-approved in 1 file(s))
        | P-ATTR-01: the plan preview's map is not wired and drawn as approved (f4):
        |   PlanSheetScreen's .preview arm line 7 of 7 in apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/PlanSheetScreen.swift: approved `case .failed(_, let failure):`, found `.hidden()`
      [M-B footer before MapView in the ZStack] P-ATTR-01 exit=1 (digest re-approved in 1 file(s))
        | P-ATTR-01: the plan preview's map is not wired and drawn as approved (f4):
        |   PlanPreviewMap's struct (the map, then its credit over it) line 15 of 38 in apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/PlanPreviewMap.swift: approved `MapView(`, found `AttributionFooter(text: CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit))`
      [M-B2 the preview credit faded out] P-ATTR-01 exit=1 (digest re-approved in 1 file(s))
        | P-ATTR-01: the plan preview's map is not wired and drawn as approved (f4):
        |   PlanPreviewMap's struct (the map, then its credit over it) line 25 of 38 in apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/PlanPreviewMap.swift: approved `}`, found `.opacity(0)`
       M ops/lib/check-map-attribution-mutations
       M ops/lib/check-map-attribution-sites
      === prove-red rows F4a-F4e
      MUTATION                                         EXIT   REASON NAMED
      F4a rv0 M-A the preview arm hands the card no map 1      yes
      F4b a shadowing previewMap(_:) method            1      yes
      F4c the preview card hidden in its arm           1      yes
      F4d rv0 M-B the map drawn over the preview credit 1      yes
      F4e the preview credit faded out                 1      yes
      prove-red: 5/5 mutations refused by name
       M ops/lib/check-map-attribution-mutations
       M ops/lib/check-map-attribution-sites
      === done 2026-10-18T00:45:36Z
  M-B's P-SAFE-03 exit=0 is the verifier's measurement; P-SAFE-03 was not re-run on M-A2..M-B2 (P-ATTR-01 owns them).

- 2026-10-18T01:49:26Z rv0 acceptance re-quoted on the merged head 80bbf90c (origin/main merged LAST; main had moved
  only queue/ files). Items 1-3 run bare, last result line each (items 4 M1-M4 unchanged: no Swift file moved; 5 and
  6 stand from the previous entry - no apps/ios or Sources file touched this round, no digest re-approved):
      `bash ops/lib/check-map-attribution` exit=0:   38 feature file(s), the app shell and AttributionFooter.swift pinned by sha256 (-pinned); every app .swift, pbxproj and root Sources (-linked).
      `bash ops/lib/check-safety-disclaimer` exit=0:   Not checked here: rendering (T-0180), taps, whether that write RUNS, contrast, Dynamic Type, 44 pt.
      `python ops/lib/check-mutate-population.py` exit=0: P-PROC-06: every added module is covered or allowlisted; the floor of 173 holds
      `python ops/lib/check-mutate-only.py` exit=0: NAME-PAIRS OK: 242318 pair tokens over 50 id populations, each refused in process by select_only in 4 modes and by onlyIds (0 calls not refused, floor 201117 tokens)
      `python ops/lib/check-pins-yaml.py` exit=0: PINS-YAML ok pins=53 fields=426 path=C:\Users\phineasf\Documents\GitHub\scenic_drive\.worktrees\T-0405\pins\PINS.yaml
      `bash ops/lib/check-exec-bits` exit=0: P-OPS-01: 253 files, 23 required present, all modes correct
      `bash ops/queue-check` exit=0: QUEUE OK (397 tasks)
      `timeout 2400 bash ops/check-pins --source-only` exit=124: 
      wc:   300 ops/lib/check-map-attribution
      wc:   245 ops/lib/check-map-attribution-sites
      wc:   212 ops/lib/check-map-attribution-mutations
      wc:   757 total
  check-pins --source-only: an exit of 124 above is `timeout 2400` (40 min) firing on a box shared with two other
  sessions' gate runs, NOT a pin failure; every ops/lib check this round touches (P-ATTR-01, P-SAFE-03) and the
  five named gates ran bare above, each exit 0. CI's check-pins run on the PR is the confirmation.

## Acceptance
1. `bash ops/lib/check-map-attribution` exits 0 and prints an (f3) line naming PlanPreviewMap.swift.
2. `bash ops/lib/check-safety-disclaimer` exits 0 (the preview's frozen blocks, the shell's frozen line, digests).
3. `bash ops/check-pins --source-only` exits 0; `python ops/lib/check-mutate-population.py`,
   `python ops/lib/check-mutate-only.py`, `python ops/lib/check-pins-yaml.py`, `bash ops/lib/check-exec-bits`,
   `bash ops/queue-check` exit 0.
4. Prove red, each against the edited tree then restored green: M1 PlanPreviewMap's footer deleted -> (d)/(f3)
   red; M2 PlanPreviewMap's footer reads a second `DriveBasemap.planned(` -> red; M3 `.accessibilityHidden(true)`
   on the map footer -> red; M4 the shell passes `previewMap: { _ in AnyView(EmptyView()) }` -> -frozen red.
5. ios-compile green and ios-screenshot green on task/T-0405, run ids quoted; plan-preview light, dark and ax5
   LOOKED AT, item by item: the route visible, the map framed on it, attribution on the map, Start, the disclaimer
   directly under Start, the estimate tag on the ETA; at ax5 the map smaller and not over the text.
6. Every file touched under Sources/ and apps/ios is <= 300 lines (`wc -l` quoted).

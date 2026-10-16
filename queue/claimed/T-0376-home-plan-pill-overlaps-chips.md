---
id: T-0376
title: The home's "Plan a drive" pill no longer draws over the drive chips (Saddle Peak, Westwood loop) - seen in home-light-medium on every recent ios-screenshot run
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T09:42:35Z
lease_expires_at: 2026-10-17T09:42:35Z
worktree: .worktrees/T-0376
branch: task/T-0376
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, ops/lib/check-safety-disclaimer-mutations, .github/workflows/ios-screenshot.yml, ops/lib/ios_screenshot_pinned.py, queue/]
pins_affected: [P-ATTR-01, P-A11Y-01]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Reported by T-0355's author (home-light-medium, run 38022188023), T-0367's author and rv2-t0368 (run 38878685784):
in home-light-medium.png the "Plan a drive" pill sits on top of the "Saddle Peak" and "Westwood loop" drive chips.
T-0355 attributed it to the shell's top-left overlay; none of the PRs that reported it touched that strip.

MEASURE FIRST: which views draw the pill and the chip strip (the shell's overlay in ScenicDriveApp.swift vs
FeatureScenicHome), their alignment/safe-area insets, and every home shot (light, dark, AX5, each detent) where they
collide - quote the shots looked at. RULE the layout (stack them, inset the chips, or move the pill), keeping
attribution visible at every detent (P-ATTR-01) and >= 44 pt targets. Acceptance: the home shots in light, dark and
AX5 show the pill and every chip with no overlap, looked at and quoted; P-SAFE-03 digests and the frozen shell lines
re-approved.

## Log
- 2026-10-16T10:05:00Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0368's recordable (ids checked on main
  and task/T-0318, task/T-0375: highest T-0375).
- 2026-10-16T09:42:35Z claimed by agent/claude-opus-5; lease until 2026-10-17T09:42:35Z
- 2026-10-16T09:44:53Z agent/claude-opus-5 (owner) MEASURE. Shots looked at: ios-screenshot run 38878685784
  (task/T-0368, d7e2c520, success), downloaded to .artifacts/T-0376-before. home-light-medium.png and
  home-dark-collapsed.png (1206x2622 px, 3 px/pt): the "Plan a drive" capsule spans about x 17-131 pt, y 72-114 pt;
  the chip band spans y 66-121 pt with "Saddle Peak" at x 18-100 pt and "Westwood loop" at x 105-189 pt - the pill
  covers all of Saddle Peak's label and the first ~26 pt of Westwood loop, in light and in dark; SF Peninsula, the
  surprise sparkle and the gear are clear. The same strip is drawn in every home shot of that run (home-{light,dark}-
  {collapsed,medium,fastest}) because nothing in it depends on the detent. There is NO home AX5 shot: the ax5 pass
  shoots only `preview nothingPretty offered loop trip saved` (.github/workflows/ios-screenshot.yml, pinned in
  ops/lib/ios_screenshot_pinned.py AX5_LIST).
  Code: the shell draws the pill - ScenicDriveApp.swift:61 `.overlay(alignment: .topLeading) {` around
  `PlanDriveButton(action: { isPlanning = true })` (FeaturePlanSheet/PlanDriveButton.swift: `.padding(.leading, 16)`,
  `.padding(.top, 8)`, `minHeight: 44`, `.font(.headline)`). The overlay is laid out in ScenicHomeScreen's safe area,
  so its top is safeTop + 8 pt, leading 16 pt. FeatureScenicHome draws the chips - ScenicHomeScreen.swift:180-199,
  the band `.padding(6)` inside `.padding(.horizontal, 12)` `.padding(.top, 4)`, also in the safe area, so the first
  chip's top-left is safeTop + 10, x 18. Both are anchored to the same corner of the same rectangle: they collide by
  construction at every detent and appearance (T-0355's attribution to the shell's top-left overlay is right; the
  overlay has done so since T-0294 put it there). ScenicHomeScreen.swift is 299 lines (cap 300).
- 2026-10-16T09:44:53Z agent/claude-opus-5 (owner) RULINGS.
  R1 STACK, in the shell: `.overlay(alignment: .topLeading) {` becomes `.safeAreaInset(edge: .top, alignment:
  .leading, spacing: 0) {`, nothing else changes. The inset is the pill's own measured height (8 pt pad + >= 44 pt,
  growing with Dynamic Type), so ScenicHomeScreen's top safe area moves down by exactly that and the chip band lays
  out under the pill; the map `.ignoresSafeArea()` and stays full-bleed under both; `chipBandBottom` is measured in
  global coordinates, so the camera's covered edge and MapLibre's logo/(i) follow the band down.
  R2 Not "move the pill into the chip band": the band already holds five 44 pt controls in one HStack (three chips,
  sparkle, gear) and a sixth would crush the chip labels at AX5; it would also need a new ScenicHomeScreen init slot
  in a 299-line file. Not "inset the chips by a constant": the pill's height follows Dynamic Type, a constant
  re-collides at AX5. Not "move the pill to another corner": the bottom-right is attribution's (P-ATTR-01) and the
  bottom is the sheet.
  R3 P-ATTR-01: the credit + HomeSheet VStack in ScenicHomeScreen is untouched; the inset takes ~52 pt from the
  Spacer between the chip band and the credit. Measured slack in home-light-medium: band bottom ~121 pt to credit
  top ~269 pt (~148 pt of map), so the credit stays above the sheet at medium in the default size; AX5 is checked by
  the new shots (R4), not assumed.
  R4 The Brief's acceptance asks for AX5 home shots and none exist: touches widen to
  .github/workflows/ios-screenshot.yml and ops/lib/ios_screenshot_pinned.py, the ax5 LIST gains `collapsed medium`
  (two shots x SETTLE 15 s = +30 s on a pass measured 14-23 min), with a prove-red row for dropping them.
  R5 Linux reaches none of this (SwiftUI layout in the Apple package): no swift test, no new numeric module, no
  mutate population. The binding guards are the frozen shell whitelist (FROZEN_APP_SHELL) + PINNED_SHELL_DIGEST, and
  the screenshot workflow pin; each is shown red (approval moved first) then green (source moved) in this Log.
  R6 PlanDriveButton.swift (FeaturePlanSheet, not in touches) is unchanged and keeps its digest; its 44 pt target and
  the chips' 44 pt targets are unchanged (P-A11Y-01). No privacy, telemetry, store-link or door change.

## Acceptance
1. The shell composes the pill with `.safeAreaInset(edge: .top, alignment: .leading, spacing: 0) {` and
   ScenicDriveApp.swift has no `.overlay(alignment: .topLeading)`: FROZEN_APP_SHELL in
   ops/lib/check-safety-disclaimer-frozen carries the new line, PINNED_SHELL_DIGEST equals
   `sed 's/\r$//' apps/ios/ScenicDrive/ScenicDriveApp.swift | sha256sum`; `bash ops/lib/check-safety-disclaimer` is
   green, and was seen red with the approval committed before the shell edit.
2. The ax5 LIST is `collapsed preview nothingPretty offered loop trip saved` in ios-screenshot.yml and in
   ops/lib/ios_screenshot_pinned.py (AX5_LIST and the expected run script), with a prove-red row "T-0376: the AX5 home
   shot dropped"; `python ops/lib/check-ios-compile-guardrails.py` and `--prove-red` are green, and the plain check
   was seen red with the pinned data moved before the workflow. (Amended per R7: `medium` crashes at AX5 on main's
   layout too; T-0378 adds it back.)
3. ios-compile success and ios-screenshot success on task/T-0376; looked at and quoted: home-light-collapsed,
   home-light-medium, home-dark-collapsed, home-dark-medium, home-ax5-collapsed (not home-ax5-medium: R7) each show the
   "Plan a drive" pill above the chip band with no overlap with any chip (Saddle Peak, Westwood loop, SF Peninsula,
   sparkle, gear), every chip 44 pt or taller, and the OpenStreetMap credit visible directly above the sheet.
4. Bare gates green: check-safety-disclaimer, check-mutate-population, check-mutate-only, check-telemetry-emit-sites,
   check-store-links, check-map-attribution, check-line-cap, check-pins-yaml, check-ios-compile-guardrails,
   queue-check.
- 2026-10-16T09:47:52Z agent/claude-opus-5 (owner) RED then GREEN. (a) Approval moved first - FROZEN_APP_SHELL's line to
  `.safeAreaInset(edge: .top, alignment: .leading, spacing: 0) {` and PINNED_SHELL_DIGEST to 93ae2a78 (computed from
  a copy of the edited shell) - with the shell unchanged: `bash ops/lib/check-safety-disclaimer` rc=1 "P-SAFE-03: a
  frozen render block changed: the app shell ScenicDriveApp line 31 of 47 ... approved
  `.safeAreaInset(edge: .top, alignment: .leading, spacing: 0) {`, found `.overlay(alignment: .topLeading) {`".
  (b) ios_screenshot_pinned.py moved first (both AX5 LIST copies + the row "T-0376: the AX5 home shots dropped") with
  the workflow unchanged: `python ops/lib/check-ios-compile-guardrails.py` rc=1 "workflow.jobs.simulator-screenshot.
  steps[4].run: differs from the pinned value ... FAIL: 1 guardrail(s) gone in ios-screenshot.yml". (c) Sources
  moved: the shell line edited (sha256 93ae2a78c27411440b2e47e4e659078d09f815305ce5c984a15c7a397f5718f3, also
  re-approved in -pinned's digest table row, the second site the first green run named) and the workflow LIST edited:
  check-ios-compile-guardrails rc=0 both workflows OK; --prove-red rc=0 "97 mutations red, 6 legitimate spellings
  green"; check-safety-disclaimer rc=0 "Frozen (-frozen); 34 feature file(s), shell, footer pinned".
- 2026-10-16T10:58:18Z agent/claude-opus-5 (owner) CI on c477e258: ios-compile 38882928962 success. ios-screenshot 38882932440:
  the light and dark jobs succeeded and the ax5 job FAILED, on attempt 1 and on a re-run (attempt 2) alike: "Wrote
  screenshot to: .../home-ax5-collapsed.png" and then "ios-screenshot: ScenicDrive (pid 22374) is not running 15s
  after the ax5 medium launch - it crashed". Shots looked at (light/dark artifacts, .artifacts/T-0376-shots):
  home-light-collapsed, home-light-medium, home-dark-collapsed, home-dark-medium. In each, the "Plan a drive"
  capsule sits alone at about y 54-86 pt with its bottom edge above the chip band's top (~89 pt), and the band below
  shows "Saddle Peak", "Westwood loop", "SF Peninsula", the sparkle and the gear whole and unobstructed, every chip
  about 32 pt+ tall at 3 px/pt (minHeight 44 in code, unchanged). MapLibre's logo and (i) moved down under the band. The
  credit "(c) MapLibre - Natural Earth - (c) OpenStreetMap contributors" is directly above the sheet at both
  detents in both appearances.
  R7 CONTROL: is the AX5 medium crash this change's? The branch task/T-0376-control (fd6d5452 = c477e258 with
  main's ScenicDriveApp.swift, -pinned and -frozen restored, i.e. the pill as a top-leading overlay, with the new ax5
  LIST kept) was pushed and shot in run 38887739175. Light and dark succeeded, ax5 FAILED the same way: "Wrote
  screenshot to: .../home-ax5-collapsed.png", then "ScenicDrive (pid 25185) is not running 15s after the ax5 medium
  launch - it crashed". So the crash is on main's layout and is not caused by this change. Ruled: the ax5 LIST keeps
  `collapsed` and drops `medium` (prove-red row renamed "the AX5 home shot dropped"); the crash is filed as T-0378
  (ids checked on main and all 271 remote task/* branches: highest T-0377), which adds `medium` back. The control
  branch has been deleted from origin. Acceptance 2 and 3 are amended to match.
  Re-checked after the LIST change: check-ios-compile-guardrails rc=0 (both workflows OK), --prove-red "97 mutations
  red, 6 legitimate spellings green ... 0 unexpected".
- 2026-10-16T11:26:00Z agent/claude-opus-5 (owner) ios-screenshot 38890737661 on af793caf: SUCCESS, all three passes. Looked at
  home-ax5-collapsed.png: the home OVERFLOWS the screen at AX5. The chip band starts above the status bar ("Saddle
  Peak", "Westwood loop", "Peninsula" wrap a few letters per line, ~220 pt tall), the credit wraps to six lines, and
  in the collapsed sheet the title "Saddle Peak - Topanga to Malibu" is drawn over the menu chips ("Fast..", "+13
  min", "+18 min"). The "Plan a drive" pill is NOT ON SCREEN. Reason: the overflowing ZStack makes ScenicHomeScreen
  taller than its proposal, the safeAreaInset container grows with it and is centred, and the inset strip ends up
  above the window. On main the overlay would draw over the chips, but it would still be reachable. So the stacked
  layout as committed is an AX5 reachability regression.
  R8 The shell gives the home a fixed frame equal to what it is offered: `GeometryReader { proxy in` around
  ScenicHomeScreen with `.frame(width: proxy.size.width, height: proxy.size.height)`. The ScenicHomeScreen line keeps
  its 8-space indent because -doors' DOORS_SHELL_LINE compares it whole. The home's overflow now stays inside its own
  frame and can no longer move the inset, so the pill stays in the strip under the status bar at every size. The
  overflow itself (chips, credit and sheet larger than the screen at AX5, and the medium crash) was there before
  this task and is T-0378's. Its scope widens to the whole AX5 overflow in the next Log line of that file.
  FROZEN_APP_SHELL gains the three lines and PINNED_SHELL_DIGEST + the -pinned table row move to e3ea537e
  (sed 's/\r$//' | sha256sum). check-safety-disclaimer, check-telemetry-emit-sites, check-store-links,
  check-map-attribution, check-screen-rehearsals, check-drive-display, check-line-cap all rc=0.
  CORRECTION to my 10:58 entry's pixel numbers (I divided display pixels by 3 without the 1.31 display factor):
  in home-light-medium of run 38882932440 the pill is at about y 71-113 pt, the chip band top is at about 118 pt,
  and the chips are about 43 pt tall (44 in code). The ordering is the same: pill above band, no overlap.
- 2026-10-16T11:49:23Z agent/claude-opus-5 (owner) ACCEPTANCE re-run on 03b20800 (contains the origin/main merge 6d71d35c).
  1. GREEN: the shell line is `.safeAreaInset(edge: .top, alignment: .leading, spacing: 0) {` and no overlay remains;
     check-safety-disclaimer rc=0 with FROZEN_APP_SHELL and PINNED_SHELL_DIGEST e3ea537e; red seen 09:5x (Log above).
  2. GREEN: ax5 LIST `collapsed preview nothingPretty offered loop trip saved` (amended per R7);
     check-ios-compile-guardrails rc=0, --prove-red "97 mutations red ... 0 unexpected"; red seen (Log above).
  3. PARTIAL: ios-compile 38893772524 success; ios-screenshot 38893775590 success on 03b20800. LIGHT and DARK pass:
     home-light-medium shows "Plan a drive" alone above the chip band, "Saddle Peak", "Westwood loop", "SF Peninsula",
     the sparkle and the gear whole, and "(c) OpenStreetMap contributors" directly above the sheet. The other light and
     dark home shots (collapsed, medium, fastest) are laid out the same in 38890737661 and 38882932440. AX5 FAILS:
     home-ax5-collapsed shows the pill on screen and reachable (R8), but drawn over the top of the chips. The cause is
     the home's own AX5 overflow: the chip band starts under the status bar and runs ~220 pt, letters wrapping. That
     overflow was there before this task and is T-0378's, with home-ax5-medium (crash). The acceptance's AX5
     no-overlap clause is not met by this PR.
  4. GREEN on the merged head: check-safety-disclaimer, check-mutate-population (floor 165), check-mutate-only,
     check-telemetry-emit-sites (54 lines), check-store-links, check-map-attribution, check-line-cap (677 files),
     check-pins-yaml (pins=51), check-ios-compile-guardrails, queue-check (369) all rc=0; PR #261 core and
     pins-source-only pass.
  PR #261 is open as a DRAFT because of 3's AX5 clause. Two ways to land it: T-0378 lands first, or the owner accepts
  the light/dark fix with the AX5 overlap recorded against T-0378.
- 2026-10-16T12:36:39Z agent/claude-opus-5 (owner) rv1 FAIL B1 taken (acceptance 3 AX5 clause; the Brief is not narrowed).
  MEASURED rv1's home-ax5-collapsed.png (run 38893775590, .artifacts/rv1-t-0376-shots; 1206x2622 px = 402x874 pt):
  the chip band runs from y ~0 to ~297 pt (letters wrapping, "Sa/dd/le/Pea/k"), so its top is ABOVE the status bar;
  the "Plan a drive" capsule is at y ~70-131 pt, drawn across Saddle Peak, Westwood loop and SF Peninsula; the credit
  box is at y ~301-622 pt (six lines, "(c) OpenStreetMap contributors" whole); the sheet starts at y ~631 pt and runs
  past the bottom edge. So the home's content is ~970 pt tall against a frame of ~710 pt (874 minus the status bar and
  the pill's inset), and R8's `.frame(width: proxy.size.width, height: proxy.size.height)` CENTRES that overflow:
  ~130 pt of it goes up past the frame's top, through the inset strip and the status bar.
  R9 The class fix is the frame's alignment, in the shell: `.frame(width: proxy.size.width, height:
  proxy.size.height, alignment: .top)`. The frame still reports exactly the size it is offered (R8 holds: the inset
  cannot be moved), and its child is now placed top-first, so whatever the home's height, its top edge is the
  frame's top edge, which is the pill inset's bottom edge: overflow can only go DOWN, never above the inset, at any
  size or detent. When the home fits (every non-accessibility size) the alignment changes nothing, so the light and
  dark shots must be unchanged. Not "clip below the inset": `.clipped()` on the frame would also cut the map, whose
  `.ignoresSafeArea()` runs under the status bar and the pill strip. Not "let the chip band scroll": a horizontal
  scroll at AX5 puts SF Peninsula, the sparkle and the gear off screen, failing "every chip visible"; not "wrap":
  the band already wraps, letter by letter, which is the overflow; reshaping it is T-0378's (whole AX5 overflow).
  R10 P-ATTR-01 at AX5: moving the overflow down shifts the measured layout by ~130 pt, so the credit box lands at
  ~y 430-750 pt and the sheet's top at ~760 pt: the credit stays on screen directly above the sheet, and less of the
  collapsed sheet shows. That is predicted, not seen: acceptance 3 is decided by the new ax5 shot, quoted below.
  The P-SAFE-03 conditions line is in the sheet (untouched); whether its AX5 position is on screen is quoted too.
  R11 Guard: the frozen shell line is a whole-line WHITELIST (FROZEN_APP_SHELL), so the alignment is pinned by
  the approval itself; the digest moves with it (PINNED_SHELL_DIGEST and the -pinned table row, 9bd481bf). A
  prove-red row "T-0376 the home's overflow centred again" (sed drops `, alignment: .top`) is added to
  ops/lib/check-safety-disclaimer-mutations, so touches widen by that one file. T-0378's medium crash is not taken.
- 2026-10-16T13:07:04Z agent/claude-opus-5 (owner) R9 RED then GREEN, and ACCEPTANCE re-run.
  RED: approvals moved first (FROZEN_APP_SHELL's line to `.frame(width: proxy.size.width, height: proxy.size.height,
  alignment: .top)`, PINNED_SHELL_DIGEST and the -pinned row to 9bd481bf57063d28795383727db5c7874d69261286062567cc1b8ccc7631ae92,
  computed from an edited copy) with the shell unchanged: `bash ops/lib/check-safety-disclaimer` rc=1 "P-SAFE-03: a
  frozen render block changed: the app shell ScenicDriveApp line 29 of 50 ... approved `.frame(width:
  proxy.size.width, height: proxy.size.height, alignment: .top)`, found `.frame(width: proxy.size.width, height:
  proxy.size.height)`". GREEN: shell edited (`sed 's/\r$//' | sha256sum` = 9bd481bf...ae92): rc=0 "Frozen (-frozen);
  34 feature file(s), shell, footer pinned". `--prove-red`: "prove-red: 61/61 mutations refused by name", row
  "T-0376 the home's overflow centred again 1 yes".
  3. ios-compile 38903147609 success, ios-screenshot 38903152649 success (all three passes) on 65bd9abb; shots in
     .artifacts/t0376-r2-shots, looked at (402x874 pt, 2.29 display px/pt):
     home-ax5-collapsed: the "Plan a drive" capsule at y ~70-131 pt, directly under the status bar, alone; the chip
     band starts BELOW it at y ~138 pt and runs to ~439 pt - Saddle Peak, Westwood loop, SF Peninsula (letters still
     wrapping, T-0378), the sparkle and the gear all on screen, none under the pill, each chip ~290 pt tall (>= 44).
     The credit box is at y ~441-762 pt, "(c) MapLibre - Natural Earth - (c) OpenStreetMap contributors" whole, and the
     sheet's top edge is directly under it at ~771 pt (grabber and "Saddle Peak -" visible). As R10 predicted, the
     overflow now leaves at the bottom: the rest of the collapsed sheet is below the screen edge, including the
     "Conditions change. Verify locally." line. That line was not on screen in rv1's AX5 shot either (its sheet showed
     the title drawn over the menu chips and ended at the screen edge), so AX5 never showed it; the overflow that hides it is
     T-0378's (whole AX5 overflow). Open gap, stated: at AX5 collapsed less of the sheet shows (~103 pt vs ~243 pt).
     home-light-collapsed, home-light-medium, home-dark-collapsed, home-dark-medium: pixel-for-pixel the same layout
     as run 38893775590 (the frame fits, the alignment is inert): pill at y ~70-113 pt alone, chip band ~118-173 pt
     with Saddle Peak, Westwood loop, SF Peninsula, sparkle and gear whole and unobstructed, chips ~43 pt drawn (44 in
     code); credit "(c) OpenStreetMap contributors" directly above the sheet at both detents in both appearances;
     "Conditions change. Verify locally." visible in the sheet in all four.
     So acceptance 3 is MET as written (pill above the band with no chip overlap, chips >= 44 pt, credit directly
     above the sheet) in all five named shots.
  1, 2, 4 re-quoted on the merged head below this entry's commit (merge of origin/main 5b8d93e9..da28b745).
- 2026-10-16T13:29:33Z agent/claude-opus-5 (owner) ACCEPTANCE on the merged head d1d8b643 (origin/main da28b745 an ancestor,
  re-fetched at 13:29Z). 1. GREEN: the shell has `.safeAreaInset(edge: .top, alignment: .leading, spacing: 0) {`, 0
  `.overlay(alignment: .topLeading)`, and 1 `alignment: .top)` (R9); check-safety-disclaimer rc=0, red seen 12:4xZ
  (entry above), --prove-red 61/61 refused by name. 2. GREEN: check-ios-compile-guardrails rc=0, --prove-red "97
  mutations red, 6 legitimate spellings green over 2 workflows, 0 unexpected". 3. MET (entry above; shots of
  65bd9abb, whose app tree the merge does not change). 4. GREEN, bare: check-safety-disclaimer, check-mutate-population
  (floor 165), check-mutate-only, check-line-cap (677, none over 300), check-pins-yaml (pins=51), check-exec-bits (230),
  check-store-links, check-telemetry-emit-sites (54 lines), check-ios-compile-guardrails, ios_screenshot_pinned,
  check-map-attribution, queue-check (369) all rc=0. PR #261 marked ready.

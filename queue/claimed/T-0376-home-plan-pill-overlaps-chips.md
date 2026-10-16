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
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, .github/workflows/ios-screenshot.yml, ops/lib/ios_screenshot_pinned.py, queue/]
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
2. The ax5 LIST is `collapsed medium preview nothingPretty offered loop trip saved` in ios-screenshot.yml and in
   ops/lib/ios_screenshot_pinned.py (AX5_LIST and the expected run script), with a prove-red row "T-0376: the AX5 home
   shots dropped"; `python ops/lib/check-ios-compile-guardrails.py` and `--prove-red` are green, and the plain check
   was seen red with the pinned data moved before the workflow.
3. ios-compile success and ios-screenshot success on task/T-0376; looked at and quoted: home-light-collapsed,
   home-light-medium, home-dark-collapsed, home-dark-medium, home-ax5-collapsed, home-ax5-medium each show the
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

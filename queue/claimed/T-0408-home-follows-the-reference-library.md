---
id: T-0408
title: Home follows the reference library - full-width Plan field with the gear inside it, one single-line chip row of destinations, chips become stacked sheet rows at AX sizes, and the route option tiles become rows instead of 'good road' x3
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-18T11:13:46Z
lease_expires_at: 2026-10-19T11:13:46Z
worktree: .worktrees/T-0408
branch: task/T-0408
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, Sources/ScenicKit/, Tests/, ops/lib/, ops/mutate/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-ATTR-01, P-SAFE-03, P-A11Y-01]
reviewer: null
depends_on: [T-0397, T-0405]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The reference library is at `C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md`.
This task covers its section "Home" and "Biggest changes" 3 and 5. Today's shot, `.artifacts/shots-39066945425/ios-screenshots-ax5/home-ax5-medium.png`
(from T-0404's run), shows these problems:
- Chip labels break mid-word at AX5 ("West-wood", "Peninsu-la").
- Three route tiles each say "good road".
- The road list is cut off at the bottom of the sheet.
- The gear and the Surprise button sit in the chip row.

Scope (FeatureScenicHome, the home screen and its sheet):
1. "Plan a drive" becomes a full-width 48pt capsule with a leading glyph. The gear is a trailing 44pt circle inside the
   same bar (Google Maps #001, Apple Maps #000).
2. Below it, ONE chip row of saved or curated drives: destinations only, single line, ellipsis truncation, horizontal
   scroll, 36pt chips with a 44pt hit area. Surprise leaves the chip row for a right-edge circle that rides the sheet
   top. Surprise is tonal, so the sheet's primary stays the only filled control.
3. AX1+: the chip row is hidden from the map. The same drives appear as stacked rows at the top of the sheet: name
   and "via <road>" on the left, the minutes delta as a right-aligned .title2 numeral over a .caption "min" (Transit
   #016). No word may hyphenate.
4. The Fastest / +13 / +18 tile row with "good road" x3 becomes option rows: "+18 min" with "via <roads>", and the
   estimate caption when unlearned. Use only data the sheet already holds. Callouts on the map are OUT of scope;
   file them as a follow-up.
5. The disclaimer line stays directly under the primary at every detent (P-SAFE-03). Attribution stays on the sheet
   edge at every detent (P-ATTR-01). Every new or changed Swift file gets its check-file-scope block (T-0406).

Demonstration: dispatch ios-compile and ios-screenshot. Look at the home shots: light, dark, ax5 collapsed and
medium. Record item by item what each shot shows. Show any new or changed guard red, then green. Run the full pin set
and check-mutate-anchors before buying review.

## Log
- 2026-10-18 filed by agent/claude-opus-5 from the reference library pass 2 and T-0404's ax5 shot.
- 2026-10-18T11:13:46Z claimed by agent/claude-opus-5; lease until 2026-10-19T11:13:46Z
- 2026-10-18T11:25:07Z agent/claude-opus-5 - rulings before code (author rule). References opened:
  .artifacts/compare-main/compare-home.jpg (ours | Google Maps #001 | Apple Maps #000) and compare-home-ax5.jpg
  (ours at AX5 | Waze #062 | Transit #016); the library section "Home" read whole.
  R1 (Brief item 1 vs touches - RULED OUT, filed T-0429): the "Plan a drive" pill is not in FeatureScenicHome. It is
  FeaturePlanSheet/PlanDriveButton.swift, mounted by the app shell ScenicDrive/ScenicDriveApp.swift through
  `.safeAreaInset(edge: .top, alignment: .leading)` - both outside `touches:`, and the shell is a frozen block of
  check-safety-disclaimer-frozen. The full-width 48pt field with the gear inside needs both files and a callback
  into ScenicHomeScreen; it is T-0429. Here the gear only LEAVES the chip row: it becomes a 44pt tonal circle in a
  right-edge column with Surprise (Apple Maps #008: one right-edge column), and T-0429 moves it into the field.
  `settingsButton`, `onSettings` and `.accessibilityIdentifier("home.settings")` stay whole lines in
  ScenicHomeScreen.swift (store_links_pinned.py pins them there).
  R2 (item 2): DriveSelector becomes a horizontal ScrollView of 36pt capsules inside a 44pt hit area, lineLimit(1),
  destinations only. The selected chip is tonal (surface + 2pt primary border, semibold), not a primary fill, so the
  sheet's button stays the one filled control. Surprise leaves the row for a 56pt tonal circle (surface, primary
  sparkle) under the gear, riding the credit+sheet stack; the credit stays directly above the sheet (P-ATTR-01 (h)).
  R3 (item 3): the body is capped at xxxLarge (HomeTypeSize.cap), so "AX1+" reads `userTypeSize` - the environment
  read ABOVE the cap (T-0378 R2) - `.isAccessibilitySize`. At AX the chip row is not built and DriveRows (new) is the
  first thing in sheetSummary: name and "via <road>" left, the default row's minutes as a .title2 numeral over a
  .caption "min" right. Data the sheet holds: each drive's bundled DriveMenu (DriveRoute.menu, read in `.task`, never
  in body). A drive with no menu shows the name only (no number nobody measured). The drive order is one table on
  DriveSelector so check-drive-copy's case counts do not move.
  R4 (item 4): the tiles become option rows in sheetDetails (medium), with one estimate caption under them
  (`PlanPreview.estimateBadge`, the ScenicKit constant; home holds no learned samples for any corridor, so every
  home option is unlearned and the caption always shows - a new whitelisted line in check-drive-display.py).
  Collapsed shows ONE meta line for the selected row ("+18 min · via ...", AllTrails #025 / library item 9). The
  'good road' km (funKm) is dropped from the UI (library data panel: "cut"); it is not total distance, so the meta
  line shows no km. "via" names the roads the option drives that the fastest row does not, first two, then
  "+N more" - pure string logic, so it lives in ScenicKit (OptionVia) with a test, not in a view.
  R5 (item 5): `conditions` moves to directly UNDER `gatedHandoff` in sheetSummary (both detents, P-SAFE-03); the
  approved block in check-safety-disclaimer-sheet and the frozen chips/body/details blocks in
  check-safety-disclaimer-frozen are edited in the same commit as the code. HomeSheet.swift is not touched.
  RULED OUT (follow-ups): map callouts for route options (Brief says out of scope) -> T-0430; the closing row
  "That's all near you", the empty-home prompt, location banner, golden-hour chip, refit-on-detent -> not in the
  Brief; DriveDetails' 13-road paragraph and developer caption -> T-0431.
  ACCEPTANCE (re-run and re-quoted at the final commit):
  A1 `bash ops/lib/check-safety-disclaimer` PASS; A2 `bash ops/lib/check-map-attribution` PASS;
  A3 `python ops/lib/check-file-scope.py` PASS and `python ops/mutate/filescope.py` PASS;
  A4 `python ops/lib/check-drive-display.py` PASS; A5 `bash ops/lib/check-drive-copy` PASS;
  A6 `python ops/lib/check-store-links.py` PASS; A7 `python ops/lib/check-estimate-badge.py` PASS where it exists;
  A8 check-mutate-population, check-mutate-only, check-mutate-anchors, check-pins-yaml, check-exec-bits, queue-check PASS;
  A9 `swift test --scratch-path .build/T-0408 --filter OptionViaTests` green, seen red first;
  A10 `wc -l` of every changed FeatureScenicHome file <= 300;
  A11 ios-compile green and ios-screenshot green on task/T-0408; home light, dark, ax5 collapsed, ax5 medium LOOKED
  at and recorded item by item (no chip mid-word break, no 'good road', gear/Surprise out of the chip row,
  conditions under the button at every detent, credit on the sheet edge).

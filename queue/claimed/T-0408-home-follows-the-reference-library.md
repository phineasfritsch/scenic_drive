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
- 2026-10-18T14:59:10Z agent/claude-opus-5 - merged origin/main (da475b6c, T-0398 #293) at 99c25f52; gates read whole.
  check-estimate-badge (P-SAFE-07, arrived with the merge) RED: "47 found, 45 approved" - DriveMenuChips
  Text(PlanPreview.estimateBadge) and .accessibilityIdentifier("home.menu.estimate") unapproved; then "90 found, 85
  approved" declarations (DriveRows selection/menus/row/pick). Fixed by approval, not by spelling: the two SITEs added;
  the DECL run regenerated by the guard's own declarations() over the tracked tree (.artifacts/regen_decls.py).
  FAIL-OPEN found and closed: a `.hidden()` on its own line under the menu caption passed BOTH P-SAFE-07 guards on an
  app-tree copy (check-estimate-badge EXIT=0, check-drive-display EXIT=0). The menu VStack is now BLOCK 11 of
  check-estimate-badge.py with a prove-red row "the home menu badge cleared on its own line" - seen red:
  "the badge block `VStack(alignment: .leading, spacing: 0) {` changed"; PROVE-RED OK: 19/19 refused by name. Cost:
  the block names menu/row/id/option, so the DECL run grew 85 -> 121 (446 lines). (`var body` as the block was tried
  first and froze every body in the app; refused.)
  check-mutate-population RED: "P-PROC-06: module(s) added by this branch with no mutation population:
  Sources/ScenicKit/Menu/OptionVia.swift" - ruled copy (the one number is a leftover-name count in a display string,
  held by OptionViaTests whole-string equalities); allowlisted with that reason.
  Screens, run 39128777662 (248a18eb) and 39132388632 (c8878158), LOOKED at:
  light collapsed: chips Saddle Peak / Westwood loop / SF Peninsula single line, no mid-word break; no "good road";
  gear and Surprise in a right-edge column, out of the chip row; meta "+18 min · via Fernwood Pacific Drive · Tuna
  Canyon Road · +9 more"; conditions directly under the button; credit on the sheet edge.
  light/dark medium: option rows Fastest / +13 min / +18 min (selected check) with via lines, one "estimate · no
  traffic data" caption; conditions under the button; credit on the sheet edge; dark mirrors light.
  ax5 collapsed: no chip row on the map; DriveRows at the sheet top, selected row with "+18" .title2 over "min";
  conditions under the button; credit on the sheet edge.
  ax5 medium: DEFECT - the selected row was squeezed to one via line over its divider (39128777662); fixing the Text
  alone (c8878158) made the second line spill over "Westwood loop" (39132388632). 1ef8b9d1 fixes the DriveRows stack
  vertically; ios-screenshot 39137239496 on 1ef8b9d1 is the witness and is NOT yet looked at in this entry.
  A1 check-safety-disclaimer EXIT=0; A2 check-map-attribution EXIT=0; A3 check-file-scope "FILE-SCOPE ok 64 file(s)
  ... 1074 approved line(s)" EXIT=0 and mutate/filescope "MUTATE ok 618/618 killed (floor 615)" EXIT=0; A4
  check-drive-display EXIT=0; A5 check-drive-copy NOT MEASURED - on this box with ~40 concurrent check-drive-copy
  processes (other sessions) one run timed out at 1500 s (EXIT=124) and the next has not printed after 40 min; it is not
  in CI; A6 check-store-links EXIT=0; A7 check-estimate-badge "47 approved whole lines ... 11 badge blocks ... 121
  declarations" EXIT=0; A8 check-mutate-population "every added module is covered or allowlisted; the floor of 173
  holds", check-mutate-only NAME-PAIRS OK, check-mutate-anchors "17 drivers ... 17 reached", check-pins-yaml ok
  pins=53, check-exec-bits "263 files ... all modes correct", queue-check "QUEUE OK (403 tasks)" - all EXIT=0;
  A9 swift test --filter OptionViaTests "5 tests in 1 suite passed" (red-first not re-shown in this session);
  A10 wc -l DriveMenuChips 95, DriveOptionMeta 29, DriveRows 90, DriveSelector 73, ScenicHomeScreen 300,
  SurpriseToggle 31 (all <= 300); A11 ios-compile 39132380776 and ios-screenshot 39132388632 green on c8878158;
  39137231763 / 39137239496 dispatched on 1ef8b9d1.
- 2026-10-18T16:22:42Z agent/claude-opus-5 - pre-review mutant pass at 2de5135d: M1 and M3 caught; M2 SURVIVED
  (P-ATTR-01): in `mapControls`, `.padding(.bottom, 8)` -> `.padding(.bottom, -44)` + `.zIndex(1)` laid Surprise over
  the credit's trailing end; with only the digest re-approved all five guards exited 0 (`mapControls` was not a frozen
  block and no limb reads its modifiers). RED as recorded by the pass: check-safety-disclaimer, check-map-attribution,
  check-file-scope, check-drive-display, check-estimate-badge all EXIT=0 on M2.
  CLASS ruled: the right-edge column rides the credit's top edge, so any geometry or z-order anywhere in its view tree
  (mapControls, the settingsButton it calls, SurpriseToggle's body) can cover the credit or push credit and sheet off
  the screen. Closed by whitelist, not by spelling: check-safety-disclaimer-frozen freezes `mapControls`,
  `settingsButton` and SurpriseToggle.swift's struct whole (FROZEN_MAP_CONTROLS / FROZEN_SETTINGS_BUTTON /
  FROZEN_SURPRISE_TOGGLE; the directive fence now covers SurpriseToggle.swift). check-map-attribution-mutations gains
  H13 (M2 verbatim), H14 (the gear's frame height 44 -> 2000) and H15 (`.offset(y: 60)` under Surprise's identifier).
  GREEN of the refusal (31cdfbf4, the three new rows on app-tree copies; full table not re-run, owner-approved
  touched-rows rule): "H13 M2 Surprise laid over the credit's trailing end 1 yes", "H14 the gear's frame pushes
  credit and sheet off 1 yes", "H15 Surprise offset down over the credit 1 yes", "prove-red: 3/3 mutations refused by
  name" (reason "a frozen render block changed"). GREEN on the real tree: A1/A2 below.
  A11 witness looked at: ios-screenshot 39137239496 and ios-compile 39137231763 on 1ef8b9d1 both success. ax5 medium:
  the selected Saddle Peak row keeps both via lines ("via Fernwood Pacific Drive · / Tuna Canyon Road · +9 more")
  inside its bar, "+18 min" right, Westwood loop and SF Peninsula below with no overlap - the DEFECT is fixed; gear
  and Surprise sit above the credit, which is whole on the sheet edge; conditions under the button. light medium
  re-looked: credit uncovered, option rows and one estimate caption. No Swift changed after 1ef8b9d1.
  ACCEPTANCE re-run at 31cdfbf4 (origin/main da475b6c is an ancestor; `git fetch origin` then merge: already up to
  date): A1 check-safety-disclaimer EXIT=0; A2 check-map-attribution "...conditions, the right-edge column and the
  app shell frozen whole" EXIT=0; A3 check-file-scope "FILE-SCOPE ok 64 file(s) in 4 module(s), 1074 approved
  line(s)" EXIT=0, mutate/filescope "MUTATE ok 618/618 killed (floor 615, population 618)" EXIT=0; A4
  check-drive-display "27 approved whole lines ... 3 structs (243 kept lines)" EXIT=0; A5 check-drive-copy NOT
  MEASURED (still running at this entry under `timeout 1500` on the loaded box; not in CI); A6 check-store-links
  EXIT=0; A7 check-estimate-badge "47 approved whole lines ... 11 badge blocks ... 121 declarations (446 lines)"
  EXIT=0; A8 check-mutate-population "the floor of 173 holds", check-mutate-only "MUTATE-ONLY OK: 248 of 248" and
  "NAME-PAIRS OK", check-mutate-anchors "17 drivers, 1303 anchors, 0 stale", check-pins-yaml "ok pins=53",
  check-exec-bits "263 files, 23 required present, all modes correct", queue-check "QUEUE OK (403 tasks)" - all
  EXIT=0; A9 swift test --filter OptionViaTests "5 tests in 1 suite passed" EXIT=0; A10 no Swift file changed since
  the last measurement (ScenicHomeScreen 300, SurpriseToggle 31, the rest as above); A11 as above.
- 2026-10-18T17:28:31Z agent/claude-opus-5 - round 2 rulings before code (author rule), on rv1-t-0408 FAIL at 44168d3b.
  B1 (P-SAFE-03 + P-ATTR-01 fail open) ACCEPTED as a class, not three spellings. sheetSummary, chips and mapControls
  are whole-line frozen, but the View types their lines MOUNT are not, so any geometry inside one of those types
  (RA `.frame(minHeight: 3000)` in DriveOptionMeta, RB `.padding(.bottom, 3000)` in DriveRows, RC
  `.frame(height: 2000)` in DriveSelector) pushes the button, the conditions line, the credit and the sheet off the
  screen with only the routine sha256 re-approval in -pinned. Same class as survivor M2, which froze the right-edge
  column but not the bodies the other roots call. RULING: the class closes by a CLOSURE WHITELIST, fail closed.
  (1) Roots: ScenicHomeScreen's sheetSummary (now also frozen in -frozen itself, not only in -sheet, so
  check-map-attribution stands on its own), chips, sheetDetails, mapControls, settingsButton and gatedHandoff (the
  property sheetSummary mounts by name; frozen whole too). (2) Every View type named on a root line, or on a line of a
  type already frozen, is frozen WHOLE FILE (every kept line of its file, imports included) in
  ops/lib/check-safety-disclaimer-frozen-views.txt, read by ops/lib/frozen_views.py, run from -frozen's
  require_frozen_blocks so both pins run it. (3) Every capitalised identifier on those lines (string literals removed)
  must be a frozen view, an approved SwiftUI/system name that our tree never redeclares, or an approved non-view
  type of ours whose every declaration and extension header does not name View; anything else is refused by name -
  so mounting a NEW view type in sheetSummary is refused until it is frozen whole. (4) A frozen entry no root reaches
  is refused (the list stays the mounted set). The transitive set measured: DriveRows, DriveOptionMeta,
  DriveSelector, DriveMenuChips, DriveDetails, DriveFacts, PostDriveOpenSlot, PostDriveCard, HandoffFailureCard,
  GatedHandoffButton, SurpriseGateSlot (SurpriseToggle stays frozen by FROZEN_SURPRISE_TOGGLE).
  RB ambiguity ruled: DriveRows has three `.fixedSize(horizontal: false, vertical: true)` lines; the demo inserts
  after the FIRST in the file (the body's root VStack), the plain reading of "after".
  "against origin/main's guards" ruled: main's guards cannot run green on this branch's tree at all (its SUMMARY_BLOCK
  and frozen arrays predate T-0408), so the meaningful baseline is the pre-fix branch 44168d3b, whose guard set is
  main's plus T-0408's. RED of the fail-open there (each with its digest re-approved in -pinned, both checks bare):
  (.artifacts/t0408-rv1-b1.sh, 34 min on the loaded box) RA "digest ce348e2d... -> 7f8ae12e...",
  check-safety-disclaimer EXIT=0, check-map-attribution EXIT=0; RB "digest 1d680cef... -> 323cdaff...", EXIT=0 and
  EXIT=0; RC "digest a1f37bd7... -> b58cac76...", EXIT=0 and EXIT=0 - all three survive, the fail-open reproduced.
  GAP RULED (recorded in -frozen's WHAT IT CANNOT SEE, not closed here): SurpriseGateSlot's card is an AnyView the
  frozen app shell injects from FeatureSurpriseMe (a lowercase builder, `surprise`); the closure walks named types,
  not injected closures. The chip band is above the Spacer, and the card shows only after a Surprise tap.
  B2 (clipped via lines) ACCEPTED. Cause measured from 39137239496: the medium sheet's content is taller than the
  screen (light medium: DriveDetails' paragraph already runs off the bottom edge; at `.large` HomeSheet does not
  scroll details), so the VStack compresses every compressible Text; the via Texts in DriveMenuChips and
  DriveOptionMeta have `.lineLimit(2)` but no `.fixedSize(horizontal: false, vertical: true)`, so they are the
  ones cut. FIX: fixedSize on both via Texts. The ZStack aligns top, so the overflow leaves by the bottom edge:
  DriveMenuChips' extra lines push only DriveDetails (below the conditions line) further down, but DriveOptionMeta
  sits ABOVE the button, so its second line moves the button and the conditions line down one line - the AX5 medium
  and collapsed shots must show both still on screen (A11). The overflow itself (medium content below the screen edge at every size, details
  not scrollable at `.large`) is HomeSheet.swift - inside touches, but a P-SAFE-03 frozen layout change the reviewer
  did not raise; RULED OUT of this round and filed as T-0432.
  Item 4: check-estimate-badge.py's docstring says "nine approved badge bodies"; corrected to the real count.
- 2026-10-18T19:40:00Z agent/claude-opus-5 - round 2 landed (9c091c36, ae69b599, merge e64cba35).
  B1 GREEN of the refusal. RA/RB/RC verbatim on ae69b599, each digest re-approved in -pinned as the reviewer did
  (.artifacts/t0408-rv1-b1.sh): RA "ac5feab3... -> a613b8cf...", RB "1d680cef... -> 323cdaff...", RC "a1f37bd7... ->
  b58cac76..."; each check-safety-disclaimer EXIT=1 "P-SAFE-03: a frozen render block changed:" and
  check-map-attribution EXIT=1 (was EXIT=0 / EXIT=0 on 44168d3b). Touched prove-red rows only (owner-approved rule),
  on 9c091c36's tree: "H16 rv1 RA DriveOptionMeta pushed 3000 tall 1 yes", "H17 rv1 RB DriveRows padded 3000 below
  1 yes", "H18 rv1 RC DriveSelector framed 2000 tall 1 yes", "H19 an unfrozen view mounted in sheetSummary 1 yes";
  the 12 generated G-<type> rows: first run RED on the driver itself ("sed: -e expression #1, char 32: unterminated
  address regex" - a `\|` in the sed script is the row's field separator), fixed, then "prove-red: 12/12 mutations
  refused by name" (G-DriveRows ... G-SurpriseToggle). The closure alone (frozen_views.py on a copy): a new
  DriveTallNote() mounted in sheetSummary -> "`DriveTallNote`, named in the roots, is neither frozen whole nor an
  approved non-view" EXIT=1; `extension DriveCopy: View` -> "an approved non-view may not be a View" EXIT=1; a
  file-scope `struct Text` -> "shadows the system name the frozen views call" EXIT=1; clean copy EXIT=0.
  B2 and A11. ios-compile 39154226669 and ios-screenshot 39154233557 on 9c091c36 green, LOOKED at: home-light-medium
  showed a NEW DEFECT - each option row's via line ran two lines but the row did not grow, so the second line was drawn
  under the next row's minutes ("+13 min" over "Topanga Canyon Boulevard · +2 more"); ax5-medium: the meta line whole
  on two lines, button and conditions on screen; ax5-collapsed: DriveRows, title, meta on two lines, button,
  conditions directly under it, credit on the sheet edge, gear and Surprise above it. ae69b599 fixes the row stack
  vertically. ios-compile 39156547422 and ios-screenshot 39156550905 on ae69b599 green, LOOKED at:
  home-light-medium - meta "+18 min · via Fernwood Pacific Drive · Tuna Canyon Road · +9 more" on two lines; button;
  conditions directly under it; option rows Fastest / +13 min / +18 min (check) each with BOTH via lines whole
  ("... South Topanga Canyon Boulevard · +2 more", "... Mulholland Highway · +6 more", "... Tuna Canyon Road · +9
  more"), no overlap, no ellipsis; one "estimate · no traffic data"; credit whole on the sheet edge, gear and
  Surprise above it; DriveDetails' paragraph continues below the screen edge (T-0432). home-dark-medium mirrors it
  in dark. home-ax5-medium - DriveRows, title, the meta line WHOLE on two lines (was cut to one), button, conditions
  under it, then the details scroll; its first via line ends "South Topanga Canyo..." at its two-line limit
  (`.lineLimit(2)` by design, a three-line road list, not the clip). home-ax5-collapsed was looked at on 39154233557
  (above); ae69b599 changed only DriveMenuChips, which collapsed does not draw.
  T-0432 filed (medium content taller than the screen; HomeSheet scrolls details only above `.large`); id checked
  unused on origin/main and every task branch first.
  ACCEPTANCE re-run on the merged head e64cba35 (origin/main 279152bb, T-0407 #303 included, an ancestor; one
  conflict in -frozen's header comment, resolved by keeping both rulings): A1 check-safety-disclaimer EXIT=0; A2
  check-map-attribution EXIT=0; A3 check-file-scope "FILE-SCOPE ok 64 file(s) in 4 module(s), 1074 approved line(s)"
  EXIT=0, mutate/filescope "MUTATE ok 618/618 killed (floor 615, population 618)" EXIT=0; A4 check-drive-display "3
  structs (243 kept lines)" EXIT=0; A5 check-drive-copy NOT MEASURED (still running under `timeout 1500` at this
  entry on the loaded box; not in CI); A6 check-store-links EXIT=0; A7 check-estimate-badge "47 approved whole lines
  ... 11 badge blocks ... 121 declarations (448 lines)" EXIT=0; A8 check-mutate-population "the floor of 173 holds",
  check-mutate-only "NAME-PAIRS OK", check-mutate-anchors "17 drivers ... 17 reached", check-pins-yaml "ok pins=53",
  check-exec-bits "267 files, 23 required present, all modes correct", queue-check "QUEUE OK (405 tasks)" - all
  EXIT=0; frozen_views.py EXIT=0; A9 swift test --filter OptionViaTests "5 tests in 1 suite passed" EXIT=0; A10 wc -l
  DriveMenuChips 97, DriveOptionMeta 30, DriveRows 90, DriveSelector 73, ScenicHomeScreen 300, SurpriseToggle 31;
  A11 as above.
- 2026-10-18T21:07:13Z agent/claude-opus-5 - round 3 rulings before code (author rule), on rv2-t-0408 FAIL at 86fb1f3e.
  B1 (red CI 39159859503: core and pins-source-only fail P-SAFE-03, `python ops/mutate/frozencomments.py` exit 2
  "check-estimate-badge.py has 9 `{` blocks, this population was built for 8") ACCEPTED. Cause: T-0407 (merged
  into this branch at e64cba35) brought frozencomments.py, whose population is generated from
  check-estimate-badge.py's BLOCKS; this branch adds the ninth `{` block (DriveMenuChips' estimate VStack), and the
  merge did not move the driver's built-for count or its floor. RULING: keep the ninth block (it is the home menu's
  badge, P-SAFE-* coverage this PR owes) and update the population: the built-for guard 8 -> 9, then RUN the driver
  and set MIN_MUTATIONS to the population it reports (recomputed, not hand-counted). The new block lives in a new
  file, so the expected growth is 10 G/T rows for the block plus 2 control rows for the file; the run decides.
  B2 (ios-screenshot 39156550905 home-ax5-medium: the 'Fastest' option row's via line cut to "via North Topanga
  Canyon / Boulevard · South Topanga Canyo..." by `.lineLimit(2)` at AX5, losing "+2 more") ACCEPTED; my round-2
  Log called this "by design" - wrong, the road list is the row's content and an ellipsis hides it. RULING: the
  via Text in DriveMenuChips takes `.lineLimit(typeSize.isAccessibilitySize ? nil : 2)` from the type's own
  `@Environment(\.dynamicTypeSize) private var typeSize` (DriveCard's spelling). OptionVia already bounds the line
  (two roads and "+N more"), so no limit at AX sizes cannot grow without bound. DriveMenuChips is frozen whole, so
  its digest is re-approved in -pinned (two rows) and its new type-scope line in check-file-scope-approved.txt.
  Re-shoot and LOOK at every option row in home-ax5-medium, home-ax5-collapsed, home-light-medium, home-dark-medium.
  M1 (a DriveCopy string returning 60 newlines pushes the sheet off screen; strings are not pinned, only identifiers)
  and M2 (a view injected as a closure into the chip band) are recorded as non-blocking and filed together as ONE
  backlog task, T-0436, its id checked unused on origin/main and every open task branch first.
  Verification this round re-runs only the touched rows (owner-approved): frozencomments.py whole (it is the red
  one), check-safety-disclaimer, check-map-attribution, check-file-scope + mutate/filescope, check-estimate-badge,
  check-drive-display; P-SAFE-03's assertion and `bash ops/check-pins --source-only` BARE on the final head.
- 2026-10-18T22:05:00Z agent/claude-opus-5 - round 3, B2 first fix seen RED on screen, re-ruled.
  ios-screenshot 39167985545 on 7a0a832a (the `isAccessibilitySize` fix) green, LOOKED at home-ax5-medium: the
  'Fastest' row still reads "via North Topanga Canyon / Boulevard · South Topanga Canyo..." - unchanged. Cause:
  ScenicHomeScreen's body ends in `.dynamicTypeSize(...HomeTypeSize.cap)` (cap = .xxxLarge, T-0384), so inside the
  sheet the environment never holds an accessibility size and `isAccessibilitySize` is always false. RE-RULED: the
  via line's limit keys on the capped scale the sheet actually sees, `typeSize > .large ? nil : 2` - HomeSheet's
  own threshold for its larger-text layout. home-ax5-collapsed on the same run: the meta line whole on two lines,
  button, conditions directly under it, credit on the sheet edge, gear and Surprise above it (draws no option rows).
  Digest 10151035... -> 20e93964... re-approved in -pinned (two rows); the changed line in -frozen-views.txt and
  check-estimate-badge-approved.txt. T-0436 filed (M1 + M2); id checked unused on origin/main (max T-0426 on main)
  and every open task branch (T-0432 on task/T-0408, T-0433 on task/T-0411, nothing higher).
- 2026-10-18T23:05:00Z agent/claude-opus-5 - round 3 landed; what was and was NOT measured.
  B1: frozencomments.py's population recomputed by its own generator (load_blocks + rows on this tree):
  304 rows (was 292 before the ninth block; +10 G/T rows for the block, +2 control rows for its new file).
  MIN_MUTATIONS = 304. Its first run on 7a0a832a went RED before any row ("the estimate reader is not silent on the
  pristine copy": DriveMenuChips' new typeSize declaration and changed via line were not approved in
  check-estimate-badge-approved.txt) - fixed in 66cf3e0f, check-estimate-badge then "11 badge blocks ... 122
  declarations (449 lines)" EXIT=0. check-safety-disclaimer EXIT=0 and check-file-scope "1075 approved line(s)"
  EXIT=0 on 7a0a832a's tree. NOT MEASURED at this entry: the full frozencomments run (started on 66cf3e0f, still
  running after 55 min on the loaded box), P-SAFE-03's assertion bare and `bash ops/check-pins --source-only` bare
  on the final head - CI (core, pins-source-only) is the measurement for them; see the PR checks.
  B2: ios-screenshot 39171247639 on ecbfb469 green, LOOKED at. home-ax5-medium: the 'Fastest' via line now runs to a
  third line, "via North Topanga Canyon / Boulevard · South Topanga Canyon / Boulevard · +2 more", no ellipsis; that
  third line sits at the screen's bottom edge, half drawn, and the +13 / +18 rows are below the edge - the medium
  overflow T-0432 owns. home-light-medium: Fastest "... South Topanga Canyon Boulevard · +2 more", +13 min "...
  Mulholland Highway · +6 more", +18 min (check) "... Tuna Canyon Road · +9 more", each whole on two lines, one
  estimate caption. home-ax5-collapsed (39167985545; collapsed draws no option rows, the change cannot reach it):
  meta whole on two lines, button, conditions under it, credit on the sheet edge. home-dark-medium on 39171247639 is
  a BLANK dark frame (54 grey levels vs 229 on 39167985545's dark-medium, whose rows matched light) - NOT looked at
  for this head; a re-shoot is owed.

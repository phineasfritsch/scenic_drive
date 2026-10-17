---
id: T-0397
title: Drive screen follows the reference library - maneuver banner, bottom card with arrival, minutes, distance and the estimate caption, a short red End with a Keep-driving confirm, and the missing disclaimer line above the card
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T15:13:47Z
lease_expires_at: 2026-10-18T15:13:47Z
worktree: .worktrees/T-0397
branch: task/T-0397
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, Sources/ScenicKit/, Tests/, ops/lib/, ops/mutate/drive_mutations.py, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-SAFE-03, P-SAFE-06, P-SAFE-07, P-A11Y-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The owner asked for the app's UI to lean on a reference library built from real shipping apps. The library lives
outside git at `C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md`
(section "Drive / turn-by-turn", and "Global rules"); the reference screens it cites are under
`.artifacts/mobbin/screens/<app>/NNN.png`. Today's shot: `.artifacts/shots-39035404874/ios-screenshots/
drive-{light,dark}.png` (run 39035404874). The library's clutter panel: no disclaimer line on the drive screen, a
~59pt full-width orange End is the only control, no ETA or next step.

Scope (DriveScreen and its parts under FeatureScenicHome, `-screen drive`):
1. A strip above the bottom card: the attribution caption (left) and "Conditions change. Verify locally."
   (.caption); both may wrap to 2 lines; the card grows to make room. This closes a product invariant gap: the
   disclaimer must be visible on the route screen while driving.
2. Bottom card: "Arrive h:mm" .title2 + "N min · N mi" .subheadline + the estimate caption while the corridor is
   unlearned (P-SAFE-07); trailing short red "End" pill, >= 44pt.
3. End confirm: small card "End this drive?", "Your drive stops here.", filled "Keep driving", red-text "End" on a
   gray tonal fill (the safe choice is the filled one).
4. Top maneuver banner (arrow, distance, street) ONLY from data DriveSession/NavAdapter already exposes; if no
   maneuver is available in the rehearsal, rule it out in the Log rather than invent one.
5. AX3+: the card stacks arrival, minutes, End (full width); the attribution + disclaimer strip stays above it.
Keep the motion gate (P-SAFE-06): above 4.5 m/s no new interaction surface may appear beyond what the gate allows.

OWNER RULING 2026-10-17 ("go with recs"), recorded for the later Live Activity task (NOT in this task's scope):
the Live Activity carries "Conditions change. Verify locally." and marks its arrival time "est." while unlearned.

Out of scope: Live Activity, dark map style, traveled/remaining styling, upcoming-scenery rows.

Demonstration: dispatch ios-compile and ios-screenshot on the task branch; quote both run ids; look at drive-light
and drive-dark and state, item by item, what each shot shows. Any new or changed guard is shown red then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the reference library pass 2 ("Biggest changes" 7).
- 2026-10-17T15:13:47Z claimed by agent/claude-opus-5; lease until 2026-10-18T15:13:47Z
- 2026-10-17T15:27:25Z RULINGS before code (author rule). Read: the Brief, library "Drive / turn-by-turn" + "Global
  rules", Google Maps #244, Uber #077, shot drive-light of run 39035404874 (the minimal surface: full-width 59 pt
  orange "End drive", the boxed credit pill bottom-right, no disclaimer, no ETA), DriveScreen.swift,
  DriveDisplay.swift, DriveSession.swift, ops/lib/check-drive-display.py, check-map-attribution(-sites), P-SAFE-09.
  - R1 Maneuver banner (Brief 4): RULED OUT. DriveDisplay is the only drive state the screen may read (P-SAFE-09,
    check-drive-display.py), and no maneuver reaches it: /plan returns no GraphHopper instructions (DriveLeg's own
    note), FerrostarDriveRoute builds one VisualInstruction per leg with maneuverType nil and the text "Continue to
    the next scenic stop" / "Arrive at your destination" - no arrow, no street. Drawing an arrow and a street would
    be invented. The existing status banner (reroute/rejoin sentence, full surface only) stays as it is.
  - R2 Arrival, minutes and miles (Brief 2): the screen holds only `display`, which carries `etaLine` (whole-line
    ETA vs fastest) and no remaining distance. DriveSession holds what is needed: `etaSeconds` of the line being
    driven (the plan's, then each taken answer's - both measured from that line's first vertex) and `drivenMeters`
    (metres to the progress vertex). DriveDisplay(session:) gains two fields, decided on Linux:
    `remainingSeconds` = etaSeconds x metres left / the line's metres (pro rata; the line's ETA when it has no
    length) and `glanceLine` = "N min · N.N mi" (tenths under 10 mi, whole miles from 10). The screen shows
    "Arrive h:mm" = the clock + remainingSeconds, refreshed each minute. Granularity is the progress VERTEX (the
    same binding fractionDriven reads), so the minutes step at vertices; that is the data, not invented.
  - R3 Motion gate (P-SAFE-09; the Brief's "P-SAFE-06" is the plan's id, this file's P-SAFE-06 is the guidance
    gate): the one INTERACTIVE element while moving stays the End action at display.actionMinHeight (60 pt moving,
    44 pt stopped) - now a short red pill, still 60 pt tall while moving. Added on both surfaces, read-only and
    glanceable: the disclaimer line, "Arrive h:mm", the glance line and the estimate caption. The fresh-route note
    and the status sentence banner stay full-surface only (display.note / display.showsDetails). The reroute/rejoin
    caption moves from inside the full-width button into the card as one .subheadline line (a short pill cannot
    hold "Head back to your route"). P-SAFE-09's why-text sentence naming "nothing else while moving" is updated.
  - R4 End confirm (Brief 3): shown only on the FULL surface (stopped). While moving, End ends at once as today -
    a confirm card would be a new two-button surface above 4.5 m/s, which the Brief's gate clause forbids. If the
    surface turns minimal while the confirm is up, it closes (the same rule as the post-drive question). Confirm
    "End" goes on to today's path (post-drive question when PostDriveQuestion says so, else onEnd).
  - R5 Strip (Brief 1): AttributionFooter is DesignSystem (outside touches) and draws a trailing pill because the
    map's lower-left corner holds MapLibre's logo; check-map-attribution(-sites) pin its one composed line in
    DriveScreen.swift. So the credit stays that pill, right-aligned, directly above the card, and the disclaimer
    is the card's first row, full width, .caption, wrapping (no lineLimit). Both scale; the card grows.
  - R6 Copy: DriveDisplay.endTitle "End drive" -> "End" (library copy note); the x glyph goes. Tests that type the
    literal change with it.
  - R7 AX3+ (Brief 5): dynamicTypeSize >= .accessibility3 stacks arrival, glance, caption, End (full width, >= 50
    pt); below it the card is an HStack with the pill trailing.
  - R8 New numbers in DriveDisplay get mutants 153-157 in ops/mutate/drive_mutations.py (floor 152 -> 157).
  - R9 check-drive-display.py's whitelist changes with the screen's lines; shown RED on the new screen before its
    APPROVED list moves, then GREEN, and --prove-red still refuses every mutation.
  ACCEPTANCE (each can fail):
  - A1 `swift test --jobs 4 --scratch-path .build/t-0397 --filter "DriveDisplayTests|DriveContinuedTests|DriveVoiceArrivalTests|PostDriveQuestionTests|DriveProgressTests"` passes, including the new glance tests.
  - A2 `python ops/mutate/drive.py --only 153,154,155,156,157` kills all five; `python ops/lib/check-mutate-population.py` and `python ops/lib/check-mutate-only.py` pass.
  - A3 `python ops/lib/check-drive-display.py` passes and `--prove-red` refuses every mutation (red-then-green quoted).
  - A4 bare gates pass: check-safety-disclaimer, check-pins-yaml, check-exec-bits, queue-check, check-map-attribution, check-map-attribution-sites.
  - A5 `wc -l` of every touched Drive*.swift <= 300; one type per file.
  - A6 `grep -nE "system\(size|dynamicTypeSize\(\.|lineLimit" FeatureScenicHome/Drive{Screen,Card,EndConfirm}.swift` prints nothing.
  - A7 ios-compile on task/T-0397 concludes success.
  - A8 drive-light: credit pill above the card; first card row "Conditions change. Verify locally."; "Arrive h:mm"; "N min · N.N mi"; the estimate caption; a short red "End" pill; no full-width orange button; nothing clipped.
  - A9 drive-dark: the same elements, legible on the dark surface.
  - A10 any AX shot of the drive (if the workflow produces one): the card stacked, End full width, strip above, nothing clipped; if the workflow has none, recorded as not shot.
- 2026-10-17T16:06:00Z build log (agent/claude-opus-5).
  - R10 touches gained ops/mutate/drive_mutations.py: the pre-commit hook refused it ("pre-commit:
    ops/mutate/drive_mutations.py is outside T-0397 touches"); R8 needs it.
  - R11 the screen no longer renders display.etaLine (minutes vs the fastest way): the library's data panel rules
    "Minutes over fastest: low, hidden - already decided"; the field stays in DriveDisplay (tests, voice).
  - Tests whose whole-equality now includes the glance carry typed literals, each checked by hand against the
    fixture geometry (cos-lat x 111195 m per degree): DriveContinuedTests answer line 4 x 0.01 deg at 34.03 =
    3684 m "15 min · 2.3 mi", preview line 5 x 0.01 deg at 34.05 = 4604 m "25 min · 2.9 mi"; DriveReplanTests
    answer line (two diagonal segments) 4422 m "15 min · 2.7 mi"; PostDriveQuestionTests probe line 1112 m "0.7 mi".
  - Root suites: `swift test --filter` over the 14 drive.py suites + DriveVoiceArrivalTests + PostDriveQuestionTests:
    "Test run with 86 tests in 16 suites passed".
  - Mutants: `python ops/mutate/drive.py --only 153,154,155,156,157` -> "caught by the test that names it: 5 of 5
    (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0)" / "MUTATE OK caught=5/5".
  - Guard RED then GREEN (R9): on the new DriveScreen before APPROVED moved, `python ops/lib/check-drive-display.py`
    exit=1: "P-SAFE-09: a line naming DriveDisplay, DriveSurface, DriveMode or display is not an approved whole line
    (21 found, 23 approved)" listing the four new card/onChange lines unapproved and six old lines missing. After:
    exit=0 "21 approved whole lines ... the drive screen renders the navigator's DriveDisplay."; `--prove-red`
    "PROVE-RED OK: 9/9 refused by name", including the two new mutations (the End target at 44 pt while moving;
    the confirm left up when the drive moves).
  - Apple CI dispatched on e3723608: ios-compile 39047780264, ios-screenshot 39047784409.
- 2026-10-17T16:37:00Z shots (agent/claude-opus-5). ios-compile 39047780264 "completed success" (3m33s);
  ios-screenshot 39047784409 "completed success" (22m10s). LOOKED at drive-light.png and drive-dark.png:
  - drive-light (A8): map with the rehearsal's kinked road drawn (the reroute was taken); the credit pill
    "© MapLibre · Natural Earth · Route data © OpenStreetMap contributors" bottom-right directly above the card,
    two lines, not covered; card on white: first row "Conditions change. Verify locally." (.caption, full width);
    "Arrive 4:41 PM" (.title2 semibold); "23 min · 1.9 mi" (muted); "estimate · no traffic data" (caption, muted);
    trailing short red capsule "End", measured 200 x 135 px on the 920-px-wide preview (402 pt wide screen) =
    ~87 x 59 pt, i.e. the 88 pt minimum width and the moving 60 pt height. No full-width orange button, no x glyph. Nothing clipped or overlapping.
    23 min matches the rehearsal reroute's 1380 s with nothing past a vertex yet.
  - drive-dark (A9): the same elements on the navy surface; text light, the End pill the dark-mode red (#F87171)
    with the dark onPrimary label; the credit pill dark. Legible. The map tiles stay pale green (the demo tiles;
    dark map style is out of scope).
  - A10: run 39047784409 had NO drive-ax5 (the workflow's ax5 LIST omitted drive). Added drive to the ax5 LIST in
    ios-screenshot.yml and its pin ops/lib/ios_screenshot_pinned.py. RED before the pin moved:
    `python ops/lib/check-ios-compile-guardrails.py` -> "IOS-COMPILE-GUARDRAILS: workflow.jobs.simulator-screenshot.
    steps[4].run: differs from the pinned value (compared by equality)" / "IOS-COMPILE-GUARDRAILS FAIL: 1
    guardrail(s) gone in ios-screenshot.yml"; GREEN after: "IOS-COMPILE-GUARDRAILS OK: ios-screenshot.yml equals the
    pinned workflow". Re-dispatched ios-screenshot 39050093003 on 1ead1091.
- 2026-10-17T17:07:55Z ax5 shot and the final acceptance re-run on the merged head 3cddb61d (origin/main merged
  last) (agent/claude-opus-5). ios-screenshot 39050093003 "completed success" (25m52s); LOOKED at drive-ax5.png:
  - drive-ax5 (A10): the card is stacked: "Conditions change. Verify locally." wrapped onto 2 lines at the top,
    "Arrive 5:23 PM" one line, "23 min · 1.9 mi", "estimate · no traffic data" wrapped onto 2 lines, then a
    full-width red "End" capsule (~50 pt). Nothing in the card is clipped or overlapping; no word breaks.
    FOUND, NOT FIXED HERE (outside touches): AttributionFooter (DesignSystem) at AX5 grows to a 6-line pill that
    covers the upper map, the route line and MapLibre's (i) ornament, and hyphenates "OpenStreet-Map". The same
    footer draws on home; it needs its own task (DesignSystem is not in T-0397's touches).
  - drive-light / drive-dark of 39050093003 match 39047784409 (described above).
  ACCEPTANCE re-quoted:
  - A1 PASS "Test run with 86 tests in 16 suites passed" (the 14 drive.py suites + DriveVoiceArrivalTests +
    PostDriveQuestionTests, including both new T-0397 R2 tests).
  - A2 PASS mutants 153-157 "caught by the test that names it: 5 of 5 ... MISSED 0" (at 43ee2d10; DriveDisplay
    unchanged since); [0] check-mutate-population "P-PROC-06: every added module is covered or allowlisted; the
    floor of 173 holds"; [0] check-mutate-only "NAME-PAIRS OK: 243923 pair tokens over 50 id populations".
  - A3 PASS [0] check-drive-display.py "21 approved whole lines ..."; --prove-red "PROVE-RED OK: 9/9 refused by name".
  - A4 PASS [0] check-safety-disclaimer; [0] check-pins-yaml "PINS-YAML ok pins=53 fields=426"; [0] check-exec-bits
    "P-OPS-01: 250 files, 23 required present, all modes correct"; [0] queue-check "QUEUE OK (391 tasks)";
    [0] check-map-attribution; [0] check-map-attribution-sites; [0] check-ios-compile-guardrails "OK".
  - A5 PASS wc -l: DriveScreen 147, DriveCard 111, DriveEndConfirm 60, DriveDisplay 89; one type per file.
  - A6 PASS grep exit=1 (no fixed sizes, no type-size cap, no lineLimit).
  - A7 PASS ios-compile 39047780264 completed success.
  - A8 PASS drive-light; A9 PASS drive-dark; A10 PASS for the card (stacked, End full width, conditions above);
    the AX5 credit-pill overlap is recorded above as a DesignSystem follow-up.
  NOT SHOT: the End confirm (needs a stopped surface and a tap; the rehearsal moves at 15 m/s) - compiled only.

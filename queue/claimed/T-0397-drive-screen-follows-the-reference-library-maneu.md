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

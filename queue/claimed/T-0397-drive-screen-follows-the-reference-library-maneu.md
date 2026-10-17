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
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, Sources/ScenicKit/, Tests/, ops/lib/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
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

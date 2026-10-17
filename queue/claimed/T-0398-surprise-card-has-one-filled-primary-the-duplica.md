---
id: T-0398
title: Surprise card has one filled primary - the duplicate Open in Apple Maps goes, secondary actions become tonal or text, and the hand-off button carries the external-link glyph
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T15:13:51Z
lease_expires_at: 2026-10-18T15:13:51Z
worktree: .worktrees/T-0398
branch: task/T-0398
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureSurpriseMe/, Sources/ScenicKit/, Tests/, ops/lib/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-A11Y-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The owner asked for the app's UI to lean on a reference library built from real shipping apps. The library lives
outside git at `C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md`
(section "Surprise card", "Global rules" -> Button hierarchy); reference screens under
`.artifacts/mobbin/screens/<app>/NNN.png`. Today's shot: `.artifacts/shots-39035404874/ios-screenshots/` (the
`-screen surprise` shots, run 39035404874). "Biggest changes" 2: the Surprise state shows TWO "Open in Apple Maps".

Scope (FeatureSurpriseMe; if the second button is drawn by a FeatureScenicHome file, say so in the Log and either
widen touches by a ruling or file the follow-up - do not edit outside touches):
1. Exactly one filled primary on the Surprise card; the duplicate hand-off goes.
2. Secondary actions (loop, not-this) become tonal or text per the library's button hierarchy.
3. The hand-off button ("Open in Apple Maps") carries a trailing arrow.up.right glyph - the user leaves the app.
4. The card follows the library's recommended order (hook, round trip + return leg, golden-hour line) using only
   data the card already has.
Keep: attribution adjacent to off-map results (P-ATTR-03), the four not-this reasons, round-trip time shown.

Demonstration: dispatch ios-compile and ios-screenshot on the task branch; quote both run ids; look at the surprise
shots (light, dark, ax5 if present) and state, item by item, what each shows. Any new or changed guard is shown red
then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the reference library pass 2 ("Biggest changes" 2).
- 2026-10-17T15:13:51Z claimed by agent/claude-opus-5; lease until 2026-10-18T15:13:51Z

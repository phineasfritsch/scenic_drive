---
id: T-0246
title: the home sheet shows the menu - extra-minutes chips for the Saddle Peak trip (Fastest / +12 min / +17 min) from ops/plan --menu's rows, each redrawing the map line and handing its own route to Apple Maps
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-26T18:40:45Z
lease_expires_at: 2026-09-27T04:40:45Z
worktree: .worktrees/T-0246
branch: task/T-0246
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/ScenicDrive/Routes/, Sources/Handoff/, Tests/HandoffTests/, ops/lib/make-route-geojson.py, ops/lib/make-menu-bundle.py, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, ops/lib/check-drive-copy, .github/workflows/ios-screenshot.yml]
pins_affected: [P-ATTR-01, P-SAFE-03, P-SAFE-04]
reviewer: null
depends_on: [T-0239]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code: the Saddle Peak drive (Topanga village -> Malibu Civic Center) carries the menu T-0239 prints for Tests/Fixtures/t0239/topanga-malibu ('bash ops/plan --menu 34.0944,-118.6013 34.0365,-118.687 --recorded Tests/Fixtures/t0239/topanga-malibu': +0.0 fastest 18.22 km 6.1 fun km, +12.2 Old Topanga/Mulholland/Piuma 21.5 fun km, +17.1 Fernwood/Tuna Canyon/Saddle Peak/Stunt 26.2 fun km); a committed script (ops/lib/make-menu-bundle.py) runs that shipping command and writes ONE small bundle (apps/ios/ScenicDrive/Routes/saddle-peak-menu.json: per row the extra minutes, fun km, road names, the Apple Maps URL exactly as printed, and a Douglas-Peucker line at the T-0236 tolerance) - byte-identical on two runs (sha256 twice); the default selected row is ruled (the owner's first drive was the Saddle Peak line)"
  - "a Linux test binds the bundle to the shipping CLI by EXACT equality: every row's URL, extra minutes and fun km in the JSON equal the ops/plan --menu output over the committed recording (the whole printed output, T-0245's lesson), and every row's line starts and ends within 10 m of the trip's origin and destination; the budget-ceiling property holds per row (extra <= the row's displayed minutes, P-SAFE-04)"
  - "the sheet shows the rows as extra-minutes chips (>= 44 pt, calm copy: 'Fastest', '+12 min', '+17 min' with the good-road km beside each; no thrill words - owner positioning 'calm adventure', tagline 'Take the long way. Unwind.'); selecting a chip redraws the map line (the selected row in the route colour, the others muted) and the button hands THAT row's URL to Apple Maps; the credit and the conditions line stay as T-0237 pinned them - the pinned digests and frozen blocks are updated in the SAME commit as the Swift they cover, with --prove-red still all refused"
  - "ios-compile green on the head; ios-screenshot on the SAME head produces light + dark at the collapsed detent with the default row and with 'Fastest' selected (a launch argument selects the row), downloaded to the main checkout's .artifacts/screens/home-*-T0246-*.png and DESCRIBED in the Log (which line is drawn, the chips, the credit, the conditions line)"
---
## Brief

The owner's question (2026-09-25): 'how much more would I have to drive to have a fun drive'. T-0239 answers it in the
engine; this puts the answer on the phone for the demo trip, so the app shows its promise - spare minutes traded for
a better road - instead of one fixed line. The route menu page (https://claude.ai/artifact/EEdUtM1oJURs72us7SUTGe)
is the owner-seen reference for the numbers.

## Log
- 2026-09-26T18:35:40Z filed by agent/claude-opus-5 (orchestrator) after PR #133 (T-0237, map-first home) merged. Starts when PR #132 (T-0239) merges.
- 2026-09-26T18:40:29Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): PR #132 (T-0239) merged - ops/plan --menu and Tests/Fixtures/t0239/topanga-malibu are on main.
- 2026-09-26T18:40:45Z claimed by agent/claude-opus-5; lease until 2026-09-27T04:40:45Z

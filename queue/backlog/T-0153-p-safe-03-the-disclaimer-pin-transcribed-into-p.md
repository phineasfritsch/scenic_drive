---
id: T-0153
title: P-SAFE-03, the disclaimer pin, transcribed into PINS.yaml with a real assertion, and a persistent "Conditions change. Verify locally." line on the home screen before a second TestFlight tester
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, ops/lib/]
pins_affected: [P-SAFE-03]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Carried from the 2026-09-18 02:45 panel (queue task 4, unfiled until now) and re-grounded at 10:13: on
task/T-0141 `git grep -iE 'disclaimer|budget|minute|ceiling' -- apps/ios` exits 1 - nothing under the app
mentions a disclaimer, and `pins/PINS.yaml` has no P-SAFE-03 (`grep -c P-SAFE-03 pins/PINS.yaml -> 0`).

The plan's pin: *P-SAFE-03 - the disclaimer gate blocks the first plan; the route screen has a visible
`SafetyDisclaimerDisplaying`* (call-graph + XCUITest, runs_on linux+mac). CLAUDE.md's product invariants
repeat it: "The safety disclaimer gates the first plan and stays visible on the route screen." The risk
table's mitigation for "sedan onto dirt/gated/closed road" names a blocking disclaimer AND a persistent
"Conditions change. Verify locally." line.

**Do:**
1. Transcribe P-SAFE-03 into `pins/PINS.yaml` with an assertion that can run on Linux today and fail for
   the reason it names: a source-level check that the type `SafetyDisclaimerDisplaying` exists under
   `apps/ios/Packages/ScenicApp/Sources/` and that every screen type under `Feature*/` that presents a route
   or a handoff conforms to it (anchor on the protocol name and the conformance list - identifiers, never a
   comment). `runs_on: [linux]` for the source half; the XCUITest half stays `pending:` on the first green
   Xcode Cloud run and is printed BY NAME by check-pins (see T-0149 on what `pending:` must mean).
2. A `DesignSystem` view carrying the persistent line `Conditions change. Verify locally.` in `fgMuted`,
   never hidden by a sheet detent, and its placement on `ScenicHomeScreen` beside the attribution footer.
   The full first-plan gate (the blocking disclaimer with acknowledgement) belongs to M4's Onboarding; this
   task ships only the persistent line and the pin skeleton, so that a second TestFlight tester never sees
   a handoff without it.
3. Demonstrated red: remove the conformance from the screen -> the pin's assertion names the screen.

Depends on T-0141 (PR #88). Do not open a second PR on `ScenicHomeScreen.swift` while its round 2 is under
review; T-0152 (copy) touches the same file - sequence them, do not stack them.

## Log
- 2026-09-18T17:55:00Z filed by agent/claude-fable-5-1 from the 02:45 and 10:13 panels (grounded). Not started.

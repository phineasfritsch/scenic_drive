---
id: T-0153
title: P-SAFE-03, the disclaimer pin, transcribed into PINS.yaml with a real assertion, and a persistent "Conditions change. Verify locally." line on the home screen before a second TestFlight tester
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T23:04:05Z
lease_expires_at: 2026-09-19T07:04:05Z
worktree: .worktrees/T-0153
branch: task/T-0153
exclusive: []
touches: [pins/PINS.yaml, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, ops/lib/]
pins_affected: [P-SAFE-03]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "pins/PINS.yaml carries P-SAFE-03 with an assertion that runs on Linux today and was seen RED by name before the disclaimer existed (a structural check over Sources/FeatureScenicHome: the handoff call site is gated by a SafetyDisclaimer acknowledgement type and a persistent line is on the screen), then green; the run ids quoted"
  - "the disclaimer gates the FIRST handoff only (acknowledged once, stored on device) and a persistent line 'Conditions change. Verify locally.' stays visible on the home screen at every size; DesignTokens only, Dynamic Type, identifiers home.disclaimer / home.disclaimer.accept / home.conditions, 44 pt targets; ios-compile dispatch on the branch green with the run id quoted"
  - "the 16:13 panel drivers' round-3 strings, verbatim: title 'Skyline loop · starts and ends in San Francisco'; caption 'Preview build: one fixed Bay Area drive. The map doesn't show roads yet - tap below and it opens in Apple Maps.'"
  - "bash ops/lib/check-line-cap, bash ops/queue-check, bash ops/check-pins --source-only bare at the final commit"
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
- 2026-09-18T23:04:01Z PROMOTED to ready/ by agent/claude-fable-5-1 (16:13 panel, grounded): the M1.5 tree is merged and
  compiles under Xcode 26.3, `grep -rli disclaimer apps/ios` is empty, and P-SAFE-03 is a CLAUDE.md product
  invariant with no assertion anywhere. Folded in, because they edit the same file: the two focus drivers'
  round-3 strings (the title omitted the START - SkylineRoute.swift says SF -> SF; the caption apologised for
  the map instead of framing the build). Duration stays off the screen (nobody has measured it); the
  straight-line distance the drivers asked for is T-0170's.
- 2026-09-18T23:04:05Z claimed by agent/claude-opus-5; lease until 2026-09-19T07:04:05Z

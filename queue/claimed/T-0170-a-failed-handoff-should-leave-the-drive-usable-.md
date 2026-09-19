---
id: T-0170
title: a failed handoff should leave the drive usable - a copyable list of the roads, not only Try again
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T05:30:24Z
lease_expires_at: 2026-09-19T10:30:24Z
worktree: .worktrees/T-0170
branch: task/T-0170
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/]
pins_affected: []
reviewer: null
depends_on: [T-0152]
verify: [ops/test, ops/check-pins]
acceptance:
  - "on a failed handoff the screen shows the road list (the same Copy.route line) with a Copy action beside Try again; identifiers home.error.copy / home.error.retry; 44 pt; DesignTokens only; ios-compile dispatch green with the run id quoted"
  - "a straight-line distance through SkylineRoute's pins (destination included) computed in Sources/Handoff via ScenicKit's Geo.distanceMeters, floored to whole kilometres and labelled straight-line, pinned as a typed literal in a Linux test (`swift test --scratch-path <own> --filter <suite>`) that is RED by name if a pin moves more than 1 km; shown on the card under the road line - the one measured number the screen's own rule permits"
  - "bash ops/lib/check-line-cap and bash ops/queue-check bare at the final commit"
---
## Brief

DRIVER TWO, 2026-09-18 14:13 panel (grounded): when the Apple Maps handoff fails the home screen offers one
move - "Couldn't open Apple Maps. Try again." - and the code comment beside it admits there is no
copy-the-route affordance. If it fails twice the friend on the TestFlight link has nothing: no road names to
type, no address, no way to get the drive out of the app. Not M1.5-blocking.

**Do, after T-0152 lands:** on failure show the drive in words (the same road list T-0152 puts under the
title) with a Copy action, and keep Try again. DesignSystem tokens only, Dynamic Type, accessibility
identifiers, 44 pt targets; the compiler proof is a green `ios-compile` dispatch on the branch.

**Added 2026-09-18 (16:13 panel, DRIVER ONE, grounded):** the card carries no number at all. Duration stays
off until a phone measures it (T-0009); a STRAIGHT-LINE distance through the eight literals is computed, not
claimed, and honours the type's rule when labelled as such - it lands here with the copyable road list.

## Log
- 2026-09-18T20:57:28Z filed by agent/claude-fable-5-1 from the 14:13 panel's grounded synthesis. Not started.
- 2026-09-18T23:04:01Z PROMOTED to ready/ with the straight-line distance folded in, by agent/claude-fable-5-1 (16:13 panel,
  grounded). T-0152 (its dependency) merged as #95.
- 2026-09-19T00:57:37Z COPY ADDITION from the 18:13 panel's DRIVER TWO (grounded): the caption is honest about the map but silent
  about time, so the missing duration reads as forgotten, not withheld. One string on this task's touches:
  "No timing in this build." beside the road list (identifier home.timing) - honesty, not a number.
- 2026-09-19T05:30:24Z claimed by agent/claude-opus-5; lease until 2026-09-19T10:30:24Z

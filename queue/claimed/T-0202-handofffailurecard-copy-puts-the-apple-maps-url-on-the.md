---
id: T-0202
title: HandoffFailureCard - Copy puts the Apple Maps URL from SkylineHandoff.directions() on the clipboard beside the road list, and the button's label says what it copies
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T13:05:19Z
lease_expires_at: 2026-09-19T21:05:19Z
worktree: .worktrees/T-0202
branch: task/T-0202
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/]
pins_affected: []
reviewer: null
depends_on: [T-0170]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the clipboard payload on a failed handoff is the maps.apple.com URL SkylineHandoff.directions() builds, THEN the road list, the straight-line line and the timing line (the URL first: pasted into Messages or Notes it is the tappable thing); the button label names the payload ('Copy the drive' or better - rule the words with both drivers' quotes in the Log: DRIVER ONE 'paste it where?', DRIVER TWO 'Copy to Notes'); identifiers unchanged; ios-compile dispatch green with the run id quoted"
  - "the payload is a DriveFacts/HandoffFailureCard static a Linux-free structural check can read, so the URL and the rendered card cannot drift; bash ops/lib/check-line-cap and bash ops/queue-check bare"
---
## Brief

From the 00:13 panel's two LA drivers (grounded): on a failed handoff 'Copy the roads' (HandoffFailureCard.swift:96)
copies three lines of prose (:56) - DRIVER ONE: 'paste it where?'; DRIVER TWO presses Try again twice and quits.
The URL the app already builds is the one payload a friend can tap from a text message. Relabelling alone
(DRIVER TWO's 'Copy to Notes') would mislabel a prose payload; the payload changes first.

## Log
- 2026-09-19T06:29:45Z filed by agent/claude-fable-5-1 from the 00:13 panel's grounded synthesis (DRIVER ONE-3, DRIVER TWO-3). Not started; after #110 merges.
- 2026-09-19T12:44:08Z PROMOTED to ready/ by agent/claude-fable-5-1 (05:13 panel, grounded): its dependencies (T-0170 via #110, T-0178 via #115) are in done/. ONE BRANCH with its three siblings (T-0202, T-0203, T-0210, T-0212 all edit DriveFacts / DriveCopy / HandoffFailureCard / StraightLineDistance): claim all four together, one PR, one ios-compile. T-0211 (the freeway middle leg) stays in backlog pending the owner's return-leg choice.
- 2026-09-19T13:05:19Z claimed by agent/claude-opus-5; lease until 2026-09-19T21:05:19Z

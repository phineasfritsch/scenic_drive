---
id: T-0210
title: DriveFacts - the timing line splits by surface: the home screen says in words that this is hours not minutes and that Apple Maps gives the time on open, never a number; the failure card keeps its own sentence
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/]
pins_affected: []
reviewer: null
depends_on: [T-0178]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the home screen's timing sentence (identifier home.timing) tells a driver with 25 minutes what kind of drive this is, in words, per drive (the LA loop is an afternoon; say so) and where the real time comes from; NO number; HandoffFailureCard renders its own sentence (Apple Maps did not open, so it cannot promise a time) - rule the words in the Log with both drivers' quotes from the 03:13 panel"
  - "ios-compile dispatch green with the run id quoted; bash ops/lib/check-safety-disclaimer, check-line-cap, queue-check bare"
---
## Brief

DRIVER ONE, 03:13 panel (grounded, DriveFacts.swift:42,:47): 'No timing in this build.' beside a straight-line
figure is honest and unusable - 'I have 25 minutes... it is an afternoon, not a commute. But the screen never says
that.' The same constant is rendered on the failure card (HandoffFailureCard.swift:61), so one sentence cannot
serve both surfaces.

## Log
- 2026-09-19T10:46:00Z filed by agent/claude-fable-5-1 (03:13 panel, grounded). Not started; after #115 merges. Shares FeatureScenicHome with T-0202/T-0203 - run them as one branch or in sequence.
- 2026-09-19T12:44:08Z PROMOTED to ready/ by agent/claude-fable-5-1 (05:13 panel, grounded): its dependencies (T-0170 via #110, T-0178 via #115) are in done/. ONE BRANCH with its three siblings (T-0202, T-0203, T-0210, T-0212 all edit DriveFacts / DriveCopy / HandoffFailureCard / StraightLineDistance): claim all four together, one PR, one ios-compile. T-0211 (the freeway middle leg) stays in backlog pending the owner's return-leg choice.

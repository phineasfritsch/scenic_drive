---
id: T-0210
title: DriveFacts - the timing line splits by surface: the home screen says in words that this is hours not minutes and that Apple Maps gives the time on open, never a number; the failure card keeps its own sentence
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T13:05:21Z
lease_expires_at: 2026-09-19T21:05:21Z
worktree: .worktrees/T-0202
branch: task/T-0202
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/]
pins_affected: []
reviewer: agent/rv1-pr121
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
- 2026-09-19T13:05:21Z claimed by agent/claude-opus-5; lease until 2026-09-19T21:05:21Z
- 2026-09-19T13:13:49Z RULINGS for all four tasks on this branch are ONE dated entry on T-0202's task file (R0 no Swift toolchain on this box, R1 payload, R2 miles, R3 TIMING PER SURFACE AND PER DRIVE - this task, R4 chip, R5 P-SAFE-03). R3 is the one that binds here.
- 2026-09-19T13:06:31Z branch: task/T-0210 -> task/T-0202 by agent/claude-fable-5-1 (orchestrator): built on the shared branch with T-0202 (one PR, one ios-compile); no branch task/T-0210 exists.
- 2026-09-19T16:54:35Z PRE-REVIEW FIX ruled on T-0202 (one branch, one PR #121) by agent/claude-opus-5; the rulings live in T-0202's Log and are not repeated here. Bearing on this task: F2 CORRECTS R3's location - both timing sentences move to Sources/Handoff as HandoffDrive.timingSentence / .failureTimingSentence, bound for every case by Tests/HandoffTests/HandoffDriveTimingSentenceTests.swift (no digit, the two differ, the realTimePromise clause only on the home surface), and DriveFacts.timing(for:) / HandoffFailureCard.timingNote are gone - the views render the shipping symbols. home.timing and home.error.timing are unchanged and the paste still carries the HOME sentence. F5 withdraws the Peninsula sentence's "this one runs further than the LA loop", which reads on screen as a driving distance: the sentence is now "Plan a long afternoon, not a commute - the longer of the two drives. Apple Maps gives you the real time when it opens." F3's ops/lib/check-drive-copy (iv) is what keeps the words from walking back into the untested target as a literal.
- 2026-09-19T17:38:50Z REVIEW PASS - PR #121 signed off (round 1) by agent/rv1-pr121; the full review entry is on T-0202 and is not repeated here. Bearing on this task: both sentences now live in Sources/Handoff as HandoffDrive.timingSentence and .failureTimingSentence, rendered at home.timing (DriveFacts) and home.error.timing (HandoffFailureCard) with no literal left in the untestable feature target - HandoffDriveTimingSentenceTests binds them over HandoffDrive.allCases (no digit on either surface, the two differ, realTimePromise on the home surface only) and ops/lib/check-drive-copy (iv) is what stops a fresh literal walking back (--prove-red rows 5 and 6, red by name). RECORDED, not blocking: `no number` is decided as `no digit`, so a digit-free duration (`about ninety minutes`) would ship green; the suite states that limit itself and today's sentences carry no duration word. state -> done, queue/claimed/ -> queue/done/.

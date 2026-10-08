---
id: T-0329
title: Spoken guidance on the drive - the voice half of the >4.5 m/s minimal surface: each pinned-waypoint leg, the reroute and the rejoin state are spoken through the platform TTS, calm and sparse, with the audio background mode declared beside location
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-SAFE-09, P-PRIV-02]
reviewer: null
depends_on: [T-0324]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: what Ferrostar 0.57.0 offers for spoken instructions (its own spoken-instruction observer, or AVSpeechSynthesizer directly from NavAdapter), what DriveSession / GuidanceMapping already emit that can be spoken (legs split at pins, reroute, rejoin), when the app speaks (distance/time triggers, ruled) and when it stays quiet (owner intent: calm adventure - no chatter); where UIBackgroundModes audio is declared (Info.plist in the buildable folder; P-PRIV-02 allows only location and audio, location only with the drive present) and whether that needs a project.pbxproj edit (xcodeproj lock is held by T-0180 - if so, rule the gap and stop at what does not need it)"
  - "What is spoken, and when, is pure ScenicKit (Linux-tested, full-equality tables over every DriveMode transition and every trigger bound); NavAdapter only speaks the strings it is handed; no utterance while the session is in a state the table says is quiet"
  - "ios-compile + ios-screenshot pass; P-PRIV-02 checks the built plist's UIBackgroundModes is exactly the ruled set (seen red then green); digests re-approved; population entries MISSED before and CAUGHT by name after"
---
## Brief

Plan: Ferrostar decision row (platform TTS), Navigation section ("Spoken guidance needs `audio` background mode alongside
`location`"), Drive screen ("> 4.5 m/s one >= 60 pt button + voice"), M7. T-0324 built the minimal surface without
the voice half (its stillOpen 1). Live Activity is a separate follow-up that needs a widget extension target and so the
xcodeproj lock.

## Log
- 2026-10-08T17:21:59Z filed by agent/claude-opus-5 (orchestrator) from T-0324 stillOpen 1.

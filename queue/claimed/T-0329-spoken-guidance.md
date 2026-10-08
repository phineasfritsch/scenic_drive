---
id: T-0329
title: Spoken guidance on the drive - the voice half of the >4.5 m/s minimal surface: each pinned-waypoint leg, the reroute and the rejoin state are spoken through the platform TTS, calm and sparse, with the audio background mode declared beside location
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T20:54:59Z
lease_expires_at: 2026-10-09T06:54:59Z
worktree: .worktrees/T-0329
branch: task/T-0329
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml, .github/workflows/ios-compile.yml]
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
- 2026-10-08T20:54:59Z claimed by agent/claude-opus-5; lease until 2026-10-09T06:54:59Z
- 2026-10-08T21:04:21Z MEASURED and RULED (agent/claude-opus-5), before any code.
  MEASUREMENTS. (m1) Ferrostar 0.57.0, read at the tag with `gh api repos/stadiamaps/ferrostar/contents/...?ref=0.57.0`
  (no Apple checkout exists on this box): `FerrostarCore.init(..., spokenInstructionObserver: SpokenInstructionObserver
  = .initAVSpeechSynthesizer(), ...)` (FerrostarCore.swift:126) - every FerrostarCore already owns an AVSpeechSynthesizer
  observer; it is triggered only from a step's `spokenInstructions`, deduped by `utteranceId` (FerrostarCore.swift:
  527-541); `SpokenInstructionObserver.spokenInstructionTriggered(_: SpokenInstruction)` (SpokenInstructionObserver.swift:
  61) honours `isMuted`, takes audio focus through AudioSessionManager (`setCategory(.playback, options: [.duckOthers,
  .interruptSpokenAudioAndMixWithOthers])`, AudioSessionManager.swift:18), speaks `ssml ?? text`, then releases focus;
  `stopNavigation()` calls `stopAndClearQueue()` (FerrostarCore.swift:424). FFI `SpokenInstruction(text:ssml:
  triggerDistanceBeforeManeuver:utteranceId:)`, `Uuid = UUID` (UniFFI/ferrostar.swift:5604-5627, 10803). (m2) Our steps
  carry `spokenInstructions: []` (FerrostarDriveRoute.step), so Ferrostar's own trigger path never fires today: the
  drive is silent. (m3) What ScenicKit emits that can be spoken: DriveSession.legs (each leg ends `.reachedWaypoint` at
  a pin or `.arrive` at the destination - DriveLeg.split), and DriveMode's three states; /plan returns no GraphHopper
  instructions (DriveLeg's doc), so GuidanceMapping produces no turn to speak. Of the 9 (from, to) mode pairs the
  session can produce: guiding->rerouting (observe, online), guiding->rejoining (observe, offline),
  rerouting->guiding (a reroute taken), rerouting->rejoining (failure, bad reply, or the drop), rejoining->guiding
  (an on-line fix), rejoining->rerouting (the online edge); the three self-pairs are no change. (m4) Info.plist:
  pbxproj:204-205 and 226-227 set `GENERATE_INFOPLIST_FILE = NO; INFOPLIST_FILE = ScenicDrive/Info.plist;` in both
  configurations and `INFOPLIST_KEY_UIBackgroundModes` occurs 0 times, so the built plist's UIBackgroundModes is the
  source file's key verbatim. (m5) `grep -n P-PRIV-02 pins/PINS.yaml` returns nothing: the pin is not in the file;
  the plan row (plan:251) reads "UIBackgroundModes subset of {location, audio}; location only with Drive target
  present". The only current check is check-pbxproj-graph.py:234 "Info.plist has no UIBackgroundModes". (m6)
  DriveNavigator builds `CoreLocationProvider(activityType: .automotiveNavigation, allowBackgroundLocationUpdates:
  false)`: a backgrounded app gets no fix, so nothing could trigger speech there.
  RULINGS. R1 WHO SPEAKS: ScenicKit decides every word and every moment (new `DriveVoice`, pure, Linux-tested);
  NavAdapter hands each string, unchanged, to Ferrostar's own observer -
  `core.spokenInstructionObserver.spokenInstructionTriggered(SpokenInstruction(text: s, ssml: nil,
  triggerDistanceBeforeManeuver: 0, utteranceId: UUID()))` - so mute, ducking and audio-focus release are Ferrostar's
  and there is no second synthesizer. Steps keep `spokenInstructions: []`, so Ferrostar never speaks on its own; a
  whole-line whitelist guard (ops/lib/check-drive-voice.py, in P-SAFE-09's row) allows exactly those two
  `spokenInstruction` lines under apps/ios and no line naming AVSpeech. R2 WHEN IT SPEAKS (per leg of the CURRENT line,
  measured ALONG the line from the latest usable fix - distance to the next vertex plus the segments to the leg's end
  vertex): one approach line when that distance is <= 400 m (exactly 400 speaks; the next double above does not) -
  "Your next scenic stop is coming up." for a pin, "Your destination is coming up." for the last leg; one arrival
  line on the last leg at <= 30 m (exactly 30 speaks; 30 is Ferrostar's step-advance distance in
  FerrostarDriveRoute.config) - "You have arrived. Take your time."; arrival supersedes an approach not yet said.
  Each is said once per leg end per line; a taken reroute is a new line and resets them. Mode transitions, a closed
  3x3 table: guiding->rerouting "You left the route. Finding a new way."; guiding->rejoining "You left the route and
  are offline. Head back to it."; rerouting->guiding "Here is a new way."; rerouting->rejoining "No new way for now.
  Head back to your route."; rejoining->guiding "You are back on your route."; rejoining->rerouting nil (the driver was
  already told; the new way speaks when it lands); every self-pair nil. R3 WHEN IT STAYS QUIET (calm adventure, no
  chatter): nothing at start; no leg line unless the mode is guiding (off the route the leg is not where the driver
  is); nothing repeated; no turn-by-turn (none exists); NaN distance speaks nothing. The motion surface does not gate
  voice: voice IS the minimal surface's other half (plan: "> 4.5 m/s one >= 60 pt button + voice"). R4 BACKGROUND:
  UIBackgroundModes is EXACTLY ["audio", "location"] in Info.plist (no pbxproj edit, m4), and DriveNavigator's
  provider gets `allowBackgroundLocationUpdates: true` - audio alone would speak nothing in the background (m6), and
  location is allowed because the drive (NavAdapter/DriveNavigator.swift) is present (plan:251). The WhenInUse key
  is unchanged (no Always request). R5 P-PRIV-02 is ADDED to PINS.yaml: ops/lib/check-background-modes.py reads the
  plist with plistlib and requires list equality with ["audio", "location"] (order, duplicates and extras fail),
  `location` only while DriveNavigator.swift exists, and every pbxproj configuration GENERATE_INFOPLIST_FILE = NO /
  INFOPLIST_FILE = ScenicDrive/Info.plist with no INFOPLIST_KEY_UIBackgroundModes; `--plist PATH` reads a BUILT plist
  (binary or XML), which ios-compile.yml now runs on the built ScenicDrive.app (touches widened to that workflow
  for this one step - the acceptance names the built plist). check-pbxproj-graph.py:234's "no UIBackgroundModes" is
  the pre-drive rule and now defers to P-PRIV-02's ruled set. R6 TESTS: Tests/ScenicKitTests/Drive/DriveVoiceTests:
  the 3x3 transition table compared whole with a meta-test that it is the cross product; the cue table over every
  bound (400 exact / nextUp / nextDown, 30 exact / nextUp / nextDown, 0, NaN, +inf) as rows that are functions of the
  variant {pin leg, last leg}; scenario tests through DriveSession + DriveVoice.utterances(after:) comparing the WHOLE
  [String] of each step; bound by name in P-SAFE-09's named-tests row. Mutation entries in ops/mutate/drive_mutations.py
  (DriveVoice and DriveSession.legEnd), MISSED with the suites emptied (--prove-vacuity --only) and CAUGHT by name after.
  R7 Live Activity stays out (needs a widget target and the xcodeproj lock - the Brief's follow-up).
- 2026-10-08T22:39:28Z BUILT (agent/claude-opus-5). R8 (ruled while writing the scenario tests, before any run): a fix
  more than 50 m from the current line is on no leg - `DriveSession.legEnd` is nil there (the session's own <= 50 m
  rule, exact bound table-tested) - so the away dwell, still `.guiding` for up to 5 s, says no leg line either.
  RED FIRST (DriveVoice stubbed: nil/[] answers, legEnd nil; `swift test --filter DriveVoiceTests`): "Test run with
  10 tests in 1 suite failed after 0.022 seconds with 24 issues" - 8 recorded an issue by name; the two passing are the
  table-only meta-tests (transitionTableIsTheCrossProduct, cueRowsAreFunctionsOfTheLeg), which read no code under test.
  GREEN (real code, `--filter Drive`): "Test run with 81 tests in 21 suites passed"; `run-named-tests.py P-SAFE-09`:
  "NAMED P-SAFE-09 passed=19/19". MUTATION (ops/mutate/drive_mutations.py entries 58-75 over DriveVoice and
  DriveSession.legEnd; floor 57->75, equivalent 4->5 with E5 device-only, test files 6->7): `--only 58..75
  --prove-vacuity` MISSED 17 of 18 and 67 compile-only (`approached = approached` is a Swift error) - 67 re-anchored to
  `approached.formUnion([Int]())`, then `--only 67 --prove-vacuity` "VACUITY PROOF OK ... MISSED=1 of 1"; `--only 58..75`
  "caught by the test that names it: 18 of 18 (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0)
  MUTATE OK". P-PRIV-02 RED/GREEN: Info.plist at d6b48cc0 -> "P-PRIV-02: Info.plist UIBackgroundModes is None, not
  exactly ['audio', 'location']" exit 1; with the key -> exit 0; `--prove-red` "PROVE-RED OK: 13/13 refused by name"
  (incl. a binary BUILT plist with an extra mode); ios-compile run 37848008751 (success) step "P-PRIV-02 on the built
  plist": "UIBackgroundModes is exactly ['audio', 'location'] with the drive present, in the source plist and the
  BUILT one". check-drive-voice.py: green "7 approved whole lines"; `--prove-red` "PROVE-RED OK: 6/6 refused by name".
  ios-screenshot run 37848014042 (success): drive-light.png LOOKED AT - the minimal surface, one full-width "End drive"
  action, the planned line and the attribution box; voice has no pixels. Digests re-approved: ScenicDrive/Info.plist,
  DriveSession.swift, DriveVoice.swift (new row beside DriveSurface).
- 2026-10-08T23:27:49Z MERGED origin/main (309de74c, T-0328's drive rows) - drive_mutations.py union: T-0328's 58-81
  kept, T-0329's renumbered 82-99 (same anchors, same killers), device-only E5 -> E6; floors 99 / 6 / 9 test files;
  digests recomputed on the merged tree. On the merged head: `swift test --filter Drive` "89 tests in 23 suites passed";
  "NAMED P-SAFE-09 passed=19/19"; check-mutate-population, check-pins-yaml, check-background-modes, check-pbxproj-graph,
  check-drive-voice, check-drive-display, check-ferrostar-imports, check-store-links, check-line-cap, queue-check exit 0.
  PR #216's linux-core went RED on two gates the worktree run had not covered: P-SAFE-03/P-ATTR-01 (DriveNavigator.swift
  pinned in ops/lib/check-safety-disclaimer-pinned - digest re-approved: 3ac4d247...) and P-OPS-06 (ios-compile.yml is
  pinned whole in check-ios-compile-guardrails.py - the "P-PRIV-02 on the built plist" step added to the pinned
  structure and to UNSKIPPABLE). After the fix: check-safety-disclaimer exit 0, check-map-attribution exit 0,
  check-ios-compile-guardrails exit 0 and `--prove-red` "PROVE-RED OK: 69 mutations red". ios-compile 37856383059
  success and ios-screenshot 37856393175 success on the merged head.

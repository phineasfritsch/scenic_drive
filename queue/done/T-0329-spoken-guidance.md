---
id: T-0329
title: Spoken guidance on the drive - the voice half of the >4.5 m/s minimal surface: each pinned-waypoint leg, the reroute and the rejoin state are spoken through the platform TTS, calm and sparse, with the audio background mode declared beside location
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T20:54:59Z
lease_expires_at: 2026-10-09T06:54:59Z
worktree: .worktrees/T-0329
branch: task/T-0329
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml, .github/workflows/ios-compile.yml]
pins_affected: [P-SAFE-09, P-PRIV-02]
reviewer: agent/rv4-t0329
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
- 2026-10-09T01:26:34Z PRE-REVIEW SURVIVORS CLOSED BY CLASS (fable pass at 53006b98; both in DriveVoice.swift, outside
  entries 82-99). RULED: both are test holes, not code defects - the shipping DriveVoice keeps `approached`/`arrived`
  across a mode change on the SAME line (R3 "nothing repeated") and decides the last leg by `end.vertex ==
  segmentCount`; no Sources/ change, so no digest row moves (DriveVoice.swift's row stays 6dbf66f5...).
  CLASS 1 (an utterance in a quiet state after a mode round trip on the same line; M1 `approached = []` and its
  sibling `arrived = false` on a transition): new `roundTripRepeatsNothing` - every cue state the voice can hold
  before leaving (pin approach at 0.017, destination approach at 0.037, arrival at 0.0398; pin at v2) x both round
  trips (online: leave -> rerouting -> rerouteFailed -> rejoining -> back; offline: leave -> rejoining -> back), the
  expected [[String]] a function of both (the said cue; the transitions' lines), compared whole; the return fix is
  inside the same cue's bound, so the only right answer after it is [back].
  CLASS 2 (a trigger bound off by one: the last-leg decision; M2 `>= segmentCount - 1`): new `pinAtEveryVertex` - a pin
  at every interior vertex (v1, v2, v3) or none, crossed with a fix ~334 m before every vertex v1..v4; expected per
  fix = pin's vertex -> [next], v4 -> [destination], else [] (rows a function of the pin variant), compared whole.
  Both named under P-SAFE-09 in ops/lib/named-tests.json (19 -> 21). Population entries 100 (approaches forgotten),
  101 (arrival forgotten), 102 (last leg one vertex early), floor 99 -> 102, committed BEFORE the tests (2eeb16a0):
  `drive.py --only 100,101,102` "MISSED 100 / MISSED 101 / MISSED 102 ... caught by the test that names it: 0 of 3
  (... MISSED 3 ...) MUTATE FAILED"; after the tests (bc2d1854): "caught 100 / 101 by: P-SAFE-09: a mode round trip
  on the same line repeats no cue ...; caught 102 by: P-SAFE-09: with a pin at every interior vertex, or none ...;
  caught by the test that names it: 3 of 3 (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0) MUTATE
  OK". drive_run FILTER list: "Test run with 51 tests in 8 suites passed" (49 + 2); `run-named-tests.py P-SAFE-09`
  "NAMED P-SAFE-09 passed=21/21"; check-mutate-population, check-drive-voice, check-line-cap (DriveVoiceTests.swift
  213 lines), check-safety-disclaimer, check-map-attribution, check-pins-yaml, queue-check exit 0.
  NON-BLOCKING NOTE (--built-products discovery seen only green): now seen red - `check-background-modes.py
  --built-products` on an empty products dir "expected exactly one ScenicDrive.app/Info.plist ..., found 0" exit 1;
  with two ScenicDrive.app copies "found 2" exit 1; with one (the source plist) exit 0 "... in the source plist and
  the BUILT one". No Apple or Sources/ file changed in this round, so ios-compile 37856383059 / ios-screenshot
  37856393175 (both success, merged head) stand and are not re-triggered.
- 2026-10-09T01:52:43Z RULING rv1-t0329 (FAIL at 973298b7, before any code). B1 (reviewer mutant RV1-M1: `arrived =
  false` dropped from the `if session.line != line {` reset; 51/51 green) is a TEST HOLE, not a code defect - the
  shipping DriveVoice does reset both on a new line (R2 "a taken reroute counts as a new line and resets both"); no
  Sources/ change, so no digest row moves. CLASS: a cue state the voice holds when a reroute LANDS (entry 91 bound only
  the `approached = []` half, through V_OFFLINE's destination-approach row). Closed by a scenario table
  `landedRerouteSaysTheNewLine`: every cue state {pin approached (0.017), destination approached (0.037), arrived
  (0.0398)} x both ways a reroute lands (online: leave -> rerouting -> rerouteArrived; offline: leave -> rejoining ->
  reconnect -> rerouteArrived), the new line the same shape as the old (5 vertices, pin at v2, so the old state's
  vertex numbers collide with the new line's) shifted 0.002 N and starting at the away fix; then a pin approach, the
  destination approach and the arrival on the new line. Expected [[String]] = [state's cue] + the leaving lines (a
  function of online) + [newWay] + [[next], [destination], [arrived]], compared whole; a meta-check requires every
  row's pre-reroute said to differ from every other row's. RECORDABLE 1 (legEnd as the crow flies caught only by the
  last bits of a straight equator line): RULED the trigger distance is R2's approach bound, 400 m ALONG the line
  (`DriveVoice.approachMeters`). New `bentLineMeasuresAlongTheLine`: an L line (0,0) -> (0,0.003) -> (0.003,0.003),
  fixes on its first leg where the along-the-line distance to the destination is just above 400 m while the crow-flies
  distance is ~60 m below it (the voice must stay quiet), then just below 400 m along it (destination), then the
  arrival; the fixture's own inequalities (crow <= 400 < along; next along <= 400) are asserted by Geo.distanceMeters
  in the test, independent of DriveSession, and legEnd.meters is compared to the along-the-line sum exactly.
  Population: entries 103 "a landed reroute keeps the arrival" (RV1-M1, killer the new table) and 104 "legEnd as the
  crow flies" (RV1-M2's text, killer the bent row ONLY - so at 973298b7 it reports whatever V_LEGEND's rounding does,
  quoted below), committed BEFORE the tests and run `--only 103,104`; floor 102 -> 104. Both tests named under P-SAFE-09
  in named-tests.json (21 -> 23). Both go in DriveVoiceTests.swift (213 lines; stays under 300), so FILTER and
  TEST_FILES do not change.
- 2026-10-09T02:54:05Z rv1 CLOSED BY CLASS (agent/claude-opus-5). BEFORE the tests (e6132b12, entries committed
  alone): `drive.py --only 103,104` "MISSED 103 a landed reroute keeps the arrival exit=0 no test objected"; "WRONG
  KILLER 104 legEnd as the crow flies named ['P-SAFE-09: on a bent line ...']; red were ['P-SAFE-09: the leg end is
  the next pin past the progress, else the last vertex, measured along the line']" (the straight-line rounding the
  reviewer recorded); "caught by the test that names it: 0 of 2 (wrong killer 1, ..., MISSED 1, ...) MUTATE FAILED".
  AFTER (1b403a2f, `landedRerouteSaysTheNewLine` + `bentLineMeasuresAlongTheLine`): "caught 104 legEnd as the crow
  flies by: P-SAFE-09: on a bent line ... | P-SAFE-09: the leg end is ..."; "caught by the test that names it: 2 of 2
  (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0) MUTATE OK". The bent row's fixture inequalities
  (along > 400 >= along-10 m step, crow < 350) and legEnd.meters == along-the-line sum are asserted in the test by
  Geo.distanceMeters. No Sources/ change; no digest row moves. DriveVoiceTests.swift 267 lines.
  MERGED origin/main e3de4d78 (PR #215 T-0332; queue T-0326) clean, merge message amended to carry the attribution
  (cb6516de); digest rows auto-unioned (T-0332's PlanSheetFailure.swift row), named-tests/allowlist unioned.
  ON THE MERGED HEAD cb6516de: touched suites "Test run with 44 tests in 6 suites passed"; "NAMED P-SAFE-09
  passed=23/23"; `drive.py --only 91,103,104` "caught by the test that names it: 3 of 3 (wrong killer 0, trapped 0,
  compile-only 0, MISSED 0, skipped 0) MUTATE OK"; check-safety-disclaimer exit 0; check-drive-display exit 0 ("19
  approved whole lines"); check-drive-voice ("7 approved whole lines"); check-mutate-population exit 0 (mutations=104
  floor 104, equivalent 6, test files 9; "P-PROC-06: ... the floor of 144 holds"); check-pins-yaml "PINS-YAML ok
  pins=49 fields=395"; check-line-cap "514 Swift files ... none over 300 lines"; queue-check "QUEUE OK (326 tasks)".
  Apple CI on cb6516de: ios-compile 37873969017 success (2m25s), ios-screenshot 37873973057 success (8m56s); linux-core
  37873972570 success.
- 2026-10-09T03:27:10Z rv2 RULING (agent/claude-opus-5), BEFORE any code. rv2-t0329 FAIL B1 at 4198d63c: RV2-D
  (`if session.line != line {` -> `if session.line.destination != line.destination {` in DriveVoice.utterances)
  survives 53/53. RULED a real defect, not equivalent: DriveSession.request(from:) sends `destination:
  line.destination`, so every reroute that lands keeps the old destination, and under RV2-D neither `arrived` nor
  `approached` resets on any real reroute. CLASS: the landed-reroute fixtures were not what the shipping request
  produces - every one moved the destination, so the reset key was only ever exercised on lines whose destination
  changed. The reviewer's RECORDABLE 3 (other partial keys) is the same class; the key a partial comparison can hide
  behind is whichever part of the line the fixtures always change, so the fixture variants are crossed over WHICH part
  changes. CLOSE BY CLASS (tests only, no Sources/ change, no digest row moves):
  (1) landedRerouteSaysTheNewLine: the new line is a variant, never a shifted copy - "the start moved" (first vertex
  0.002 N, the rest the old line's) and "the middle moved" (v1 and v3 0.0003 N, ~33 m; first vertex, pin v2 and
  destination the old line's) - both 5 vertices with the pin at v2 so the old state's vertex numbers collide, both
  ending at the old line's destination; crossed with the three cue states {pin approached, destination approached,
  arrived} and online/offline = 12 rows, each [[String]] compared whole. After landing the driver comes back onto the
  new line at 0.017, 0.037, 0.0398 and must hear [next], [destination], [arrived] again.
  (2) META-CHECK bound to the shipping symbol: in every landed-reroute row (and offlineThenANewWay) the RerouteRequest
  the session actually returned (observe online, connectivity offline) is captured and its `destination` must equal
  the fixture's last vertex AND the old line's destination - so a fixture that moves the destination fails by name.
  Each variant's shape is asserted too: start-moved differs from the old line only at index 0; middle-moved keeps
  index 0 and the destination and differs somewhere between.
  (3) offlineThenANewWay: `rerouted` becomes [away, short's destination] (it moved the destination), then the
  destination's approach and the arrival on it.
  Population: 105 "the line-change reset keyed on the destination" (RV2-D's text; killers the landed table and the
  offline row) and 106 "the line-change reset keyed on the first vertex" (`session.line.coordinates[0] !=
  line.coordinates[0]`; at 4198d63c every fixture moved the start too, so it is expected MISSED there; killer the
  landed table, through its middle-moved rows only). Committed BEFORE the tests and run `--only 105,106`; floor
  104 -> 106. DriveVoiceTests.swift stays under 300 lines, so FILTER and TEST_FILES do not change.
- 2026-10-09T03:53:54Z rv2 B1 CLOSED BY CLASS (agent/claude-opus-5). BEFORE the tests (7b345434, entries 105/106
  and floor 104 -> 106 committed alone): `drive.py --only 105,106` "MISSED 105 the line-change reset keyed on the
  destination exit=0 no test objected"; "MISSED 106 the line-change reset keyed on the first vertex exit=0 no test
  objected"; "caught by the test that names it: 0 of 2 (wrong killer 0, trapped 0, compile-only 0, MISSED 2, skipped
  0) MUTATE FAILED". AFTER (b5d95f00, tests only): `drive.py --only 103,105,106` "caught 103 a landed reroute keeps
  the arrival by: P-SAFE-09: a landed reroute ..."; "caught 105 the line-change reset keyed on the destination by:
  P-SAFE-09: offline says head back; ... | P-SAFE-09: a landed reroute ..."; "caught 106 the line-change reset keyed
  on the first vertex by: P-SAFE-09: a landed reroute ..."; "caught by the test that names it: 3 of 3 (wrong killer
  0, trapped 0, compile-only 0, MISSED 0, skipped 0) MUTATE OK". landedRerouteSaysTheNewLine is now 2 reroute
  variants x 3 cue states x online/offline = 12 rows compared whole, each asserting the RerouteRequest the session
  returned has `destination` == the fixture's last vertex == the old line's destination; the pre-reroute-distinct
  meta-check is keyed per (variant, online). offlineThenANewWay reroutes [away, short's destination] (~497 m) and
  hears the destination's approach and the arrival on it. The destination meta-check was not run red on its own
  (any fixture that moves the destination also changes the spoken rows); RECORDED. RECORDABLE 3 (keys on plan token
  or waypoints): the start-moved rows keep the pins and pass no token, so a token- or waypoint-keyed reset is the
  same blind spot; not run this round, RECORDED for the reviewer. No Sources/ change; no digest row moves.
  DriveVoiceTests.swift 287 lines. origin/main e3de4d78 is already an ancestor (merge: "Already up to date").
  ON HEAD b5d95f00: touched suites "Test run with 53 tests in 8 suites passed"; "NAMED P-SAFE-09 passed=23/23" exit
  0; check-mutate-population bare exit 0 ("P-PROC-06: every added module is covered or allowlisted; the floor of 144
  holds"); check-line-cap "514 Swift files ... none over 300 lines" exit 0; check-drive-voice exit 0 ("7 approved
  whole lines"); queue-check "QUEUE OK (326 tasks)".
- 2026-10-09T05:04:37Z REVIEW PASS round 4 (agent/rv4-t0329, not the owner) on c58dbf6d. Merges carry no hand edits: merge-tree
  --write-tree of each merge's parents equals its tree (2d29a499 e42dd393 EQUAL; c58dbf6d 35bd2228 EQUAL). BARE in a
  detached worktree at origin/task/T-0329: "NAMED P-SAFE-09 passed=23/23" exit 0; check-mutate-population exit 0
  ("the floor of 144 holds"); "PINS-YAML ok pins=49" exit 0; "QUEUE OK (326 tasks)" exit 0; drive.py --only
  103,105,106 "MUTATE OK caught=3/3" (each caught by the P-SAFE-09 test that names it). CI: ios-compile 37884543287
  success and ios-screenshot 37884547218 success, both on 2d29a499; diff 2d29a499..c58dbf6d touches only ops/lib/
  named-tests.json, pins/PINS.yaml, queue/ and services/api (no Swift, no apps/ios). gh pr checks 216 on c58dbf6d:
  core pass, pins-source-only pass. LAST: origin/main 9e9924d8 is not an ancestor, drift is queue-only (be7eb6ab,
  9e9924d8: T-0335 ready/claimed, one queue file) - acceptable. Signed off; queue/claimed/ -> queue/done/.

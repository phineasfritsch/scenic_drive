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
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, Sources/Handoff/, Tests/HandoffTests/]
pins_affected: []
reviewer: null
depends_on: [T-0152]
verify: [ops/test, ops/check-pins]
acceptance:
  - "THE COMPILER, ONE DISPATCH, green first time - no red compile to quote. gh workflow run ios-compile.yml --ref task/T-0170 -> run 35425137026 on headSha b45efd0ef577d942c90c577fb621c8b28334be75 ; gh run view 35425137026 --json status,conclusion,databaseId,headSha -> {conclusion: success, databaseId: 35425137026, status: completed}. gh run view 35425137026 --log -> 2238 lines, line 2181 '** BUILD SUCCEEDED **'; grep -c ' error:' over that log -> 0. Every new file compiled, both architectures: line 1339 'Compiling Clipboard.swift (in target DesignSystem from project ScenicApp)' (x86_64) and 1377 (arm64); 1553 / 1578 'Compiling StraightLineDistance.swift (in target Handoff from project ScenicDrive)'; 1716 'Compiling ScenicHomeScreen.swift (in target FeatureScenicHome)'; 1718 'Compiling DriveFacts.swift, HandoffFailureCard.swift (in target FeatureScenicHome)'. Toolchain: line 51 DEVELOPER_DIR /Applications/Xcode_26.3.app, line 119 'Build version 17C529'"
  - "RED FIRST, on the Linux test, in this order. (1) The suite alone, before the type: swift test --scratch-path .build/T0170 --filter HandoffTests -> 'StraightLineDistanceTests.swift:117:22: error: cannot find StraightLineDistance in scope' (and :120, :121), 'error: fatalError' - no test run. (2) With StraightLineDistance.swift added: 51 tests, 2 issues, both in Handoff shipping source - 'every capitalised identifier in the shipping source is on the allow-list' recorded an issue on 'StraightLineDistance' and on 'Geo'. The allow-list is a registry, so both names were argued into it in place. (3) Green: 'Test run with 51 tests in 8 suites passed after 0.066 seconds', exit 0. The new suite by name: swift test --filter StraightLineDistanceTests -> 5/5 passed - 'the chain is the shipped pins in driving order, then the destination', 'every point is within a kilometre of where this suite thinks it is', 'the whole-kilometre figure is the number the card shows', 'the figure is floored, not rounded: 1999 m of chain is 1 km and never 2', 'a pin moved off the ridge is caught by the per-point bound and NOT by the total'"
  - "RED BY NAME ON A REAL PIN MOVE, run and restored. sed on Sources/Handoff/SkylineRoute.swift moved pin 5 to 37.48272 / -122.35830 (line 147) -> 'every point is within a kilometre of where this suite thinks it is' FAILED at StraightLineDistanceTests.swift:74 - 'Expectation failed: (drift -> 1119.8013521532137) <= (Self.pinDriftToleranceMeters -> 1000.0)'; 'the chain is the shipped pins...' failed on the array; and the witness held live - the metre band caught 1.310767586255679 m while the FLOORED figure stayed 112, which is exactly why the kilometre is written per point and not on the total. git checkout -- Sources/Handoff/SkylineRoute.swift -> git status --short shows it gone, suite green again"
  - "THE MUTANT PASS for the new numeric module (CLAUDE.md's ops/mutate/ population is ruled in the Log as STILL OPEN; these three were run by hand instead of claimed). Each mutated, run, restored from a backup, green afterwards. M1 rounded(.down) -> rounded(.up): CAUGHT by 'the figure is floored, not rounded' (wholeKilometers -> 2, expected 1) and by 'the whole-kilometre figure is the number the card shows' (113 vs 112). M2 waypoints + [destination] -> waypoints: CAUGHT by 'the chain is the shipped pins...' (chain.last -> the turn-around, not the destination; count 7 vs 8) and by the figure test (63 km vs 112). M3 meters/1_000 -> meters/100: CAUGHT by the figure test (1122 vs 112) and by the floor test (19 vs 1). 3/3 caught by NAMED tests, 0 survivors"
  - "bash ops/lib/check-line-cap -> 'P-SRC-02: 76 Swift files tracked (Sources=27, Tests=38, apps/ios=11), none over 300 lines', exit 0. wc -l on every file this task writes: 52 Sources/Handoff/StraightLineDistance.swift, 123 Tests/HandoffTests/StraightLineDistanceTests.swift, 194 Tests/HandoffTests/HandoffSourceTests.swift, 25 apps/ios/Packages/ScenicApp/Sources/DesignSystem/Clipboard.swift, 57 apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/DriveFacts.swift, 128 apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/HandoffFailureCard.swift, 199 apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift (unchanged line count: two hunks, six lines out and six in)"
  - "bash ops/queue-check -> 'QUEUE OK (187 tasks)', exit 0. bash ops/check-pins --source-only -> 'PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only', exit 0"
  - "MERGE HYGIENE vs PR #101, measured and not asserted: git merge-tree --write-tree --name-only HEAD origin/task/T-0153 -> tree 79ae86f0c1eee1add1dba20a7a02fd1b93605e6e, exit 0, no conflict path printed. Reading that merged tree's ScenicHomeScreen.swift back: line 72 HandoffFailureCard(message: handoffFailure, line 136 DriveFacts(), line 78 conditions, line 80 GatedHandoffButton( - both branches' edits land. The one semantic follow-up is on the record and is a compile error, not a silent one: merged line 74 is onRetry: { handoff() } and #101 removes handoff() from that type, so the merger re-points one line at the gated path. grep over this task's whole diff for isSafetyDisclaimerAcknowledged or safety.disclaimer.acknowledged.v1 -> no output, so every count ops/lib/check-safety-disclaimer makes is unchanged"
  - "THE SURFACE, measured. grep -rn accessibilityIdentifier(\"home. over the feature target -> DriveFacts 47 home.distance, 53 home.timing; HandoffFailureCard 65 home.error, 71 home.error.route, 107 home.error.copy, 126 home.error.retry; ScenicHomeScreen 94 home.title, 104 home.route, 112 home.caption, 141 home.openInAppleMaps - ten, no duplicates. grep -rn 'minHeight: 44' -> HandoffFailureCard 100 and 119 (both new buttons) plus ScenicHomeScreen 133. grep -rn for a six-digit hex or an ad-hoc Color( over the feature target -> no output, exit 1 (DesignTokens only). grep -rn for .system(size: or a numeric size: -> no output, exit 1 (no point size anywhere). The new files' text styles: DriveFacts 44/50 .subheadline; HandoffFailureCard 62 .footnote, 68 .subheadline, 97/116 .headline - Dynamic Type styles only. grep -rn UIPasteboard over every .swift in the tree -> DesignSystem/Clipboard.swift only (line 23 the statement, 7/10/19 its doc), so the root package still never sees UIKit"
  - "git status --porcelain -> no output, exit 0. git diff --name-only b45efd0 -- '*.swift' -> no output, exit 0: nothing Swift changed after run 35425137026 compiled b45efd0; the record commit carries the task file only"
  - "NOT RUN, on the record: bash ops/test and the full bash ops/check-pins (out of scope for this session by the task's own instruction; the Linux gates are covered by the suite above and by gh pr checks on the PR). NOT DONE, on the record: nothing has rendered any of this - no simulator, no device, no snapshot, no screenshot. Every claim about how the failure card looks, how the two buttons behave at accessibility sizes, and whether the Copy button's 'Copied' label is legible is a reading of code. The clipboard has never been written to on a real device"
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
- 2026-09-19T05:38:56Z TOUCHES WIDENED by the owner, before any code: `Sources/Handoff/` and `Tests/HandoffTests/` added to
  `touches:`. The disagreement: the header's `touches:` named the two app directories only, while acceptance row 2 requires the
  straight-line distance to be *computed in `Sources/Handoff`* and *pinned in a Linux test*. Those two cannot both hold - the
  pre-commit hook reads `touches:` and would refuse the very files the acceptance asks for. Ruled: the acceptance is right and the
  header was short, because the task was filed as a UI task and the 16:13 addition moved the arithmetic into the root package. The
  four directories are what this task writes; nothing outside them is staged. `exclusive:` stays empty - no serial-only file is
  touched (no `Package.swift`: `Handoff` and `HandoffTests` already exist as targets and gain files, not targets; buildable folders
  mean `project.pbxproj` does not move either).
- 2026-09-19T05:38:56Z MERGE HYGIENE vs PR #101 (task/T-0153, unmerged, round 4), ruled before code. #101 rewrites
  `ScenicHomeScreen.swift` in six hunks (`git diff HEAD:<file> origin/task/T-0153:<file>` -> `@@ -1,17`, `@@ -19,21`, `@@ -62,16`,
  `@@ -117,53`, `@@ -174,10`, `@@ -187,13`): the import block and the type doc, the stored properties (`@AppStorage
  "safety.disclaimer.acknowledged.v1"`, `isShowingDisclaimer`), the bottom stack from old line 65 (`openInAppleMaps` -> `conditions`
  + `GatedHandoffButton` + `.sheet`), the whole `openInAppleMaps`/`handoff()` region, and two strings in `Copy` (`title`,
  `mapCaption`) plus the DELETION of `Copy.handoffFailed`, which moves into `GatedHandoffButton.Copy`. This task therefore writes
  TWO hunks in that file and no others: (a) old lines 57-62, the body of `if let handoffFailure { … }`, replaced by one
  `HandoffFailureCard(...)` call - the `if let` line 56 and its closing `}` on 63 are left as context, so two unchanged lines stand
  between this change and #101's first changed line (65); (b) one inserted line, `DriveFacts()`, inside `header` after
  `.accessibilityIdentifier("home.route")` (old line 106), which sits between #101's hunk ending at old 77 and its hunk starting at
  old 117 and touches neither. Nothing else moves: the import block is untouched (the new views are their own files with their own
  imports), the `Copy` enum is READ (`Copy.route` is passed into the card, the same one literal T-0152 ruled) and not edited, so the
  region around the deleted `handoffFailed` is not approached, and neither `isSafetyDisclaimerAcknowledged` nor
  `safety.disclaimer.acknowledged.v1` appears anywhere in this task's diff - `ops/lib/check-safety-disclaimer` counts occurrences of
  both over every `*.swift` under the app tree recursively, so new files that never name them leave every count it makes unchanged.
- 2026-09-19T05:38:56Z (R1) THE FAILED-HANDOFF STATE. On failure the screen shows `HandoffFailureCard` (its own file, one type per
  file): the message (`home.error`, `destructive`, the identifier T-0152 pinned, kept), the road list - `Copy.route` passed in, not
  a second literal - at `home.error.route`, and two buttons side by side, Copy (`home.error.copy`, `primary` fill with `onPrimary`
  text) and Try again (`home.error.retry`, `border` hairline with `fg` text). Both `frame(maxWidth: .infinity, minHeight: 44)`, the
  label inside the frame so the 44 pt target holds at the smallest Dynamic Type setting; text styles only, no point size, and
  `fixedSize(horizontal: false, vertical: true)` on every string including the two labels, so accessibility sizes wrap rather than
  truncate. Colour comes from `DesignTokens` only (`destructive`, `fg`, `surface`, `border`, `primary`, `onPrimary`) - no hex, no
  ad-hoc `Color`. The Copy button changes its own label to "Copied" once tapped: a clipboard write has no other visible effect, and
  an action with no feedback is the dead-button failure mode this file's own doc comment names. The identifier does NOT change with
  the label, so a UI test finds one `home.error.copy` in both states.
- 2026-09-19T05:38:56Z (R1a) RETRY OWNERSHIP, ruled for the #101 merge. The card takes `onRetry: () -> Void` and never calls
  `SkylineHandoff.open()` itself. The rejected alternative was a card that owns the retry (taking `Binding<String?>`), which merges
  textually AND semantically with #101 - but it would put a SECOND handoff call site in the app, one that does not pass through
  `GatedHandoffButton`, i.e. a route out of the app that the safety gate does not own. That is the kind of thing this repository
  exists to catch, so the closure stays and the screen keeps the single call site. Consequence, stated rather than discovered: when
  #101 lands, `handoff()` no longer exists on the screen and the ONE line `onRetry: { handoff() }` has to be re-pointed at the gated
  path. It is one line, inside the block this task owns, and it is a compile error if missed - not a silent one. The closure is a
  literal, not the method reference `onRetry: handoff`, because a `@MainActor` method reference does not convert to a nonisolated
  `() -> Void` under Swift 6; a non-`@Sendable` closure literal inherits the isolation instead, which is what `GatedHandoffButton`'s
  `onFailure: { handoffFailure = $0 }` already does on #101's green compile.
- 2026-09-19T05:38:56Z (R2) THE STRAIGHT-LINE DISTANCE. `Handoff.StraightLineDistance` (one file, root package, Foundation +
  ScenicKit): `meters(through:)` sums `ScenicKit.Geo.distanceMeters` over consecutive pairs, `wholeKilometers(through:)` divides by
  1000 and rounds `.down` (floor, never round-half-up: a floored number can only understate the drive), and `skylineRoutePoints` is
  `SkylineRoute.waypoints + [SkylineRoute.destination]` - the seven pins in driving order with the destination last. The chain
  starts at pin 1 and NOT at the user: `AppleMapsDirections(source: nil, …)` means "wherever you are", which is unknown to this app
  by design, so the leg to the first pin is not in the number and the label says so. 112 km, floored from 112268.093 m.
- 2026-09-19T05:38:56Z (R2a) HOW THE TOLERANCE IS EXPRESSED - PER PIN, NOT ON THE TOTAL. "Red if a pin moves more than 1 km" cannot
  be a tolerance on the total: moving a mid-chain pin PERPENDICULAR to its two legs changes the sum by roughly d^2/2 * (1/L1 + 1/L2),
  which for d = 1 km and 10 km legs is ~100 m. Witness, computed before the test was written: moving pin 5 (`skylineSouthOfCA92`) by
  +0.0100 lat / -0.0015 lon is a 1119.8 m drift and takes the total from 112268.093 m to 112269.4 m - 1.3 m, and the floored figure
  stays 112 km. A 1 km band on the total would see nothing. So `StraightLineDistanceTests` pins the total EXACTLY, as the floored
  integer 112 (an integer needs no tolerance), and carries the 1 km rule as a PER-POINT bound:
  `everyPointIsWithinAKilometreOfWhereThisSuiteThinksItIs` measures each shipped point against this suite's typed literals with
  `Geo.distanceMeters` and a `pinDriftToleranceMeters = 1_000.0` bound. The witness above is a standing test in the same suite, in
  the style of `SkylineRidgeLegTests.theCA35PinIsWhatKeepsTheRidgeBound`: it asserts both halves - the per-point bound catches the
  moved pin AND the floored total does not - so the reason the tolerance is per pin is in the suite rather than in this file's prose.
  The seven pin literals are READ from `SkylineRouteTests` (which is where they are typed out against the shipped array) and not
  typed a third time, per `SkylineRidgeLegTests`' own note; only the destination is typed here, because no suite had typed it yet.
- 2026-09-19T05:38:56Z (R3) THE TIMING LINE. "No timing in this build." verbatim from the 00:57 addition, identifier `home.timing`,
  a string and never a number, rendered by `DriveFacts` (its own file) directly under the straight-line line, which is directly
  under `home.route` in the header band - the card the 16:13 panel said carries no number at all. Both lines are `fgMuted`
  `.subheadline`, the pair the header already uses for secondary lines under the title. Distance first, then timing: the distance is
  the claim and the timing line is the qualification, and a qualification reads as an afterthought above the thing it qualifies.
- 2026-09-19T05:38:56Z (R4) WHAT THE CLIPBOARD RECEIVES: three lines, newline-separated, in the order the screen shows them - the
  road list (`Copy.route`, the same string on screen), the straight-line line, and "No timing in this build.". Not the title: the
  title is what this app calls the drive, and the roads are what a stranger can act on. The timing line is in the paste ON PURPOSE,
  and it is the reason the distance line is in it too: "112 km" pasted into a message with no qualification is read as an hour and a
  half, which is exactly the unmeasured claim the screen refuses to make. A paste has no screen above it to carry the caveat, so the
  caveat travels with the number. The two `DriveFacts` strings are `static let`s the card reads, so the pasted text and the rendered
  text cannot drift apart. `UIPasteboard` is reached through `DesignSystem.Clipboard` (one file, `@MainActor`, one statement):
  `DesignSystem` already imports UIKit for `DesignTokens`, the root package never sees it, and the feature target names a clipboard
  rather than a pasteboard.
- 2026-09-19T05:38:56Z (R5) THE MUTATION POPULATION, ruled against CLAUDE.md rather than around it. CLAUDE.md: *"A new numeric
  module (under `services/etl/etl/` or `Sources/`) ships its mutation population under `ops/mutate/` with a literal floor."*
  `StraightLineDistance` is a new numeric module under `Sources/`, so the rule bites. It collides with this task's scope, which is
  two app directories plus the widening above, and `ops/mutate/handoff.py` is a harness file this task does not own. Ruled: the
  population is NOT written here, and the gap is not left unmeasured either - three mutants were run by hand against the shipped
  suite before the first commit, each restored from a backup and re-run green afterwards, and all three were CAUGHT BY NAME (the
  transcript is in the acceptance block). STILL OPEN carries the follow-up: the population belongs in `ops/mutate/handoff.py` beside
  the driver, with the floor, owned by a task that owns `ops/`.
- 2026-09-19T05:38:56Z (R6) THE TYPE DOC IS LEFT ALONE, and it is still true. `ScenicHomeScreen`'s doc block says *"No duration
  anywhere on this screen. Nobody has driven this route or measured it, and a number nobody measured is the kind of claim this
  repository exists to catch."* That block is inside #101's second hunk (old lines 19-39), so editing it is a guaranteed conflict,
  and it does not need editing: it forbids a DURATION and an UNMEASURED number. What lands here is neither - it is a distance,
  measured on every launch from the pins' own coordinates, labelled as a straight line, and standing beside the sentence that says
  this build has no timing. The argument for the number lives in `DriveFacts`' own doc comment, in a file #101 does not have.
- 2026-09-19T05:38:56Z NOT RULED HERE, on the record: nothing in this task renders. There is no simulator and no device on this box;
  every claim above about how the card looks is a reading of code, and the compiler (the `ios-compile` dispatch) is the only proof
  of anything Apple-side.
- 2026-09-19T06:12:00Z ACCEPTANCE BLOCK RE-RUN BARE at the final pre-review commit and re-quoted in full above: the suite
  (51 tests in 8 suites passed, and 5/5 in the new one by name), the single ios-compile dispatch 35425137026 on b45efd0 with
  '** BUILD SUCCEEDED **' at log line 2181 and an ' error:' count of 0, the three mutants (3/3 caught by name), the pin-move red,
  `bash ops/lib/check-line-cap` (76 files, none over 300), `bash ops/queue-check` (QUEUE OK, 187 tasks), `bash ops/check-pins
  --source-only` (ok=12 failed=0), `git merge-tree` against origin/task/T-0153 (clean, exit 0), `wc -l` on all seven files, and a
  clean `git status --porcelain`. `git diff --name-only b45efd0 -- '*.swift'` is empty: no Swift file moved after the compile, so
  every number above is measured on the bytes that built.
- 2026-09-19T06:12:00Z STILL OPEN, handed to the reviewer rather than closed quietly:
  (a) `ops/mutate/handoff.py` has no population for `StraightLineDistance` - CLAUDE.md requires one for a new numeric module under
  `Sources/` and `ops/` is outside this task's `touches:` (R5). Three mutants were run by hand and all three were caught by name,
  which is evidence and not a population: there is no floor, and nothing re-runs them. A task that owns `ops/` should add them.
  (b) When PR #101 lands, merged `ScenicHomeScreen.swift:74` (`onRetry: { handoff() }`) has to be re-pointed at the gated path.
  The merge itself is clean and this is a compile error, not a silent one (R1a).
  (c) Nothing asserts the new identifiers. `ScenicApp` ships no test target by deliberate choice (see its manifest), so
  `home.error.copy`, `home.error.retry`, `home.error.route`, `home.distance` and `home.timing` are checked by the compiler and by
  reading, and by nothing else. The first UI test bundle should take them.
  (d) The Copy button's label never returns to "Copy the roads": `hasCopied` is one-way for the life of the card. On a second
  failure the button still reads "Copied" until the view is rebuilt. Left as is because nothing here can watch a clipboard change
  under the app, and a timer that flips a label back is a behaviour nobody on this box can see run.
  (e) The number omits the leg from the user to pin 1, because `source: nil` means the app does not know where the user is. The
  label says "through the pins", which is true, but a reader standing in Sacramento would still be 140 km from the first pin with
  nothing on screen saying so.
- 2026-09-19T06:20:40Z **Record corrections from the mutant pass on this build (4028c56), closed before the review is bought -
  agent/claude-fable-5-1 (orchestrator), for the owner. The pass killed by name: the chain without the destination
  (63 vs 112, three tests red), rounded-to-nearest (red only in the synthetic floor test - see (c)), a pin moved
  1.5 km (red in the per-pin test), and found the tree clean at 4028c56 == PR head, the ios-compile run
  35425137026 green by sha b45efd0; zero blocking survivors. One EQUIVALENT survivor and three text items.**
  (a) MUTANT 4, nobody wrote it: the haversine leg replaced by a flat equirectangular distance on the same radius
  passes 51/51 - witness: haversine total 112,268.093 m, flat 112,268.146 m, +0.053 m over the shipped chain
  (largest leg delta 0.026 m); a radius of 6,371,000 m moves it -0.155 m, also inside the 1 m band; the band does
  catch a 0.1% radius change (-112.3 m) and the WGS84 equatorial/polar radii (+125.6 / -251.2 m). Equivalent at
  the card's precision, so NOT wrong - but Tests/HandoffTests/StraightLineDistanceTests.swift:41-43's doc ("to
  catch a change in the arithmetic (a different radius, a different formula)") overclaims: a formula change is
  NOT caught on this chain (it would be on a 1,065 km east-west leg: 707 m). When ops/mutate/handoff.py's
  population is written (STILL OPEN (a)) this is an EQUIVALENT entry with that witness, or the doc is narrowed
  to "a gross radius change" and a long synthetic leg joins the floor test if a formula change is meant to be
  caught. Doc, not code; left for the reviewer and that task. (b) apps/ios/Packages/ScenicApp/Sources/DesignSystem/
  Clipboard.swift:6's doc "this package is the one place that is allowed to know about UIKit" is an overclaim:
  FeatureScenicHome/SkylineHandoff.swift already imports UIKit (pre-existing, not this diff); the only NEW UIKit
  importer is Clipboard.swift. (c) The acceptance block's "rounded(.down) -> rounded(.up): CAUGHT by the figure test
  (113 vs 112)" does not generalise: rounded-to-NEAREST leaves the shipping literal at 112 (the chain is 112.268 km)
  and is killed only by the synthetic floor test ("1999 m of chain is 1 km and never 2", :97). Killed, by one test,
  not by the typed literal - recorded so the population's killers name the right test.

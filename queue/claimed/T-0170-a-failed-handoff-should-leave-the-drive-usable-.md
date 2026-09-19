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

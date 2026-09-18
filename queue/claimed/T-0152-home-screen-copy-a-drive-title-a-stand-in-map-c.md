---
id: T-0152
title: home-screen copy - a drive title, a "stand-in map" caption, and a user-facing message where the screen shows String(describing: error)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T20:32:55Z
lease_expires_at: 2026-09-19T04:32:55Z
worktree: .worktrees/T-0152
branch: task/T-0152
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "gh workflow run ios-compile.yml --ref task/T-0152 ; gh run view 35393000321 --json status,conclusion -> {\"conclusion\":\"success\",\"status\":\"completed\"} ; gh run view 35393000321 --log -> line 1616 '** BUILD SUCCEEDED **' (Xcode 16.4, Build version 16F6, swift-driver 1.120.5), grep -c 'error:' over that log -> 0, and line 1324 'SwiftCompile normal arm64 Compiling\\ ScenicHomeScreen.swift ... (in target FeatureScenicHome from project ScenicApp)'. ONE dispatch, green first time - no red compile to quote"
  - "bash ops/lib/check-line-cap -> P-SRC-02: 68 Swift files tracked (Sources=25, Tests=35, apps/ios=8), none over 300 lines, exit 0"
  - "RED FIRST, same gate, same file: 130 filler lines appended -> bash ops/lib/check-line-cap -> 'P-SRC-02: file(s) over the 300-line cap:' / '  apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift (309 lines)', exit 1; filler removed -> green above"
  - "awk 'END{print NR}' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> 179, exit 0"
  - "grep -n 'accessibilityIdentifier(\"home\\.' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> 59:home.error, 92:home.title, 100:home.caption, 129:home.openInAppleMaps (the last pre-existing), exit 0"
  - "grep -n 'handoffFailure = \\|String(describing: error)' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> 138 (doc comment), 145 'handoffFailure = nil', 152 'Self.log.error(... String(describing: error), privacy: .public)', 153 'handoffFailure = Copy.handoffFailed'. The raw error reaches Logger and nothing else; no assignment of it to the on-screen string remains, exit 0"
  - "grep -rn '0x[0-9A-Fa-f]\\{6\\}\\|Color(' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ -> no output, exit 1 (no raw hex and no ad-hoc Color in the feature target; colour comes from DesignTokens only)"
  - "grep -n '\\.font(' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> 55 .footnote, 87 .title2, 95 .subheadline, 119 .headline - four Dynamic Type text styles, no .system(size:) and no point size, exit 0"
  - "git diff --name-only origin/main...HEAD -> apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift and queue/claimed/T-0152-*.md, exit 0"
  - "git diff --name-only origin/main...HEAD -- apps/ios/Packages/ScenicApp/Sources/DesignSystem/ -> no output, exit 0 (DesignSystem is in touches: and needed no edit: bg, fg, fgMuted, destructive all already exist)"
  - "git status --porcelain -> no output, exit 0"
  - "NOT RUN, on the record: bash ops/check-pins and bash ops/test (the default swift scratch path does not build in a worktree on this box) - gh pr checks on the PR is the record for the Linux gates. NOT DONE, on the record: nothing has rendered this screen - no simulator run, no device, no snapshot; this tree has never been on a phone"
---
## Brief

Found by DRIVER TWO on the 2026-09-18 10:13 panel, grounded by the fable pass. On task/T-0141 (PR #88)
`ScenicHomeScreen.swift` has exactly two readable strings: `Open in Apple Maps` (:67) and the attribution
line. The map is MapLibre demotiles at zoom 8.5 (`:33`, `MapStyle.swift:16`: country polygons, nothing at
Bay Area scale - a blank map, unexplained), the drive is not drawn (MapView has no polyline/annotation
path, only the camera), and a failed handoff reaches the user as `String(describing: error)` (:91), i.e. a
Swift type name.

The friend on the TestFlight link opens it once on a Saturday because "this finds pretty drives". What they
see is a blank map and a button. The button is honest about Apple Maps opening and silent about the drive.

**Do, after PR #88 lands (do not widen that review):**
1. a title above the map naming the drive (`Skyline via Cañada Road` - the handoff already carries the
   waypoints; name what it will hand off) and one honest caption: `Preview build - this map is a stand-in,
   not your route. The drive opens in Apple Maps.` Copy per the plan's rules: active voice, says exactly what
   happens, no apology.
2. a user-facing message in place of `String(describing: error)`: what went wrong and what to do
   (`Couldn't open Apple Maps. Try again, or copy the route.`), the raw error kept in a log line, not on
   screen.
3. no new tokens, no new fonts; DesignSystem stays as it is (the plan's token table). Any `.xcstrings`
   file is serial-only (CLAUDE.md) - declare `exclusive:` if one is introduced; prefer not to introduce one
   until a second language exists.

Bounded: a screen M4 replaces. Do not draw the route line here (that is M4's route preview with real tiles);
do not add the disclaimer here (T-0153 owns it, and it gates the first plan, not the skeleton).

## Log
- 2026-09-18T17:55:00Z filed by agent/claude-fable-5-1 from the 10:13 panel (Driver Two, grounded; the "collides with the fixer's edit" opportunity-cost claim was WRONG - ScenicHomeScreen.swift was untouched by the fixer). Not started.
- 2026-09-18T20:32:55Z claimed by agent/claude-opus-5; lease until 2026-09-19T04:32:55Z
- 2026-09-18T20:39:30Z agent/claude-opus-5 (owner and author). **Rulings first, before any code.** Every place
  the plan, this Brief, the owner's task rulings and the tree disagree or are silent, with pointers. Read
  first: `ScenicHomeScreen.swift`, `DesignSystem/DesignTokens.swift`, `DesignSystem/AttributionFooter.swift`,
  `MapAdapter/MapStyle.swift`, `FeatureScenicHome/SkylineHandoff.swift` (read only - T-0151 owns it),
  `apps/ios/Packages/ScenicApp/Package.swift` (read only - serial-only, `exclusive: []` here), and the plan's
  "UI and design system" section (`~/.claude/plans/i-want-to-make-synthetic-twilight.md`, lines 314-336).

  **R1 - the failure string: the Brief and the owner's rulings disagree.** The Brief above (item 2) writes
  `Couldn't open Apple Maps. Try again, or copy the route.`; the owner's rulings for this task write
  `Couldn't open Apple Maps. Try again.` RULED: the short one, verbatim, no "or copy the route". There is no
  copy affordance on this screen or anywhere in the Apple package -
  `grep -rn "UIPasteboard\|ShareLink\|copy" apps/ios/Packages/ScenicApp/Sources/ --include=*.swift` returns
  exactly one line, and it is `DesignTokens.swift:29`, the words "body copy" inside a doc comment. Telling a
  user to copy a route they cannot copy is the same defect as showing them a Swift type name: a sentence the
  screen cannot back up. If a share affordance ever lands, the sentence grows with it.

  **R2 - the "copy rules from the plan" are not in the plan.** The owner's rulings cite "Copy rules from the
  plan: active voice, says exactly what happens, no apology". The plan has no such rules:
  `grep -n -i "active voice\|no apology\|says exactly\|Copy rules\|apolog\|microcopy" <plan>` returns nothing,
  and its "UI and design system" section (lines 314-336) covers navigation, screens, the token table and
  SF Pro / Dynamic Type only - it takes no view on wording. What the plan does have is its own user-facing
  strings, and they are consistent with the three rules by example: `"not much pretty within 25 minutes of
  this drive"` (line 117), `"Conditions change. Verify locally."` (line 359), `estimate · no traffic data`
  (line 55) - declarative, present tense, no "sorry", no "oops", no "we". RULED: apply the three rules as the
  OWNER's rules, not as a quotation from the plan, and record that they are unquotable there so the next agent
  does not go looking. The three strings below are checked against the plan's examples, not against a rule
  that does not exist in it.

  **R3 - where the title and caption go: "above the map" or over it.** The Brief says "a title above the map";
  the owner's rulings say only that nothing may cover the `AttributionFooter` or the lower-right corner of the
  map at any size class. Both readings satisfy that. RULED: a header band on `DesignTokens.bg` ABOVE the map,
  not an overlay on the tiles. `DesignTokens`' contrast claims are stated against `bg` and `surface` (its type
  note), and a basemap is neither - `AttributionFooter` carries its own opaque `surface` chip for exactly this
  reason, in its own words: text over tiles "carries its own ground rather than trusting the tiles". A header
  band gets guaranteed `fg`/`fgMuted`-on-`bg` contrast with no new token, and it structurally cannot reach the
  lower-right corner. Cost, stated: the map is shorter by the height of the band. That is the visible
  consequence of "a title above the map" and is not a fourth change - see R6.

  **R4 - where the raw error goes.** The owner's ruling says "the raw error goes to a log call, never to the
  screen" and names no logger; nothing in `apps/ios/` logs anything today
  (`grep -rn "import os\|Logger(" apps/ios/ --include=*.swift` -> no output). CLAUDE.md says feature targets
  import only DesignSystem, ScenicKit, PlaceStore and their own protocols. RULED: `import OSLog` and a
  `Logger`. That list governs FIRST-PARTY targets in this repository - the same file already imports SwiftUI,
  and `SkylineHandoff.swift` in this same target imports Foundation and UIKit, so an Apple system framework is
  plainly not what the list is about (`Package.swift`'s own "DEVIATION ON THE RECORD" note is about
  `MapAdapter` and `Handoff`, two first-party products). OSLog also needs no manifest change - system
  frameworks are linked by SPM on Apple platforms - which matters because `Package.swift` is serial-only and
  this task holds no `exclusive:` lock on it. The alternative, `print`, writes to a stream nobody reads on a
  phone. Subsystem string: `com.phineasfritsch.scenicdrive`, read from
  `apps/ios/ScenicDrive.xcodeproj/project.pbxproj` (`PRODUCT_BUNDLE_IDENTIFIER`, both configurations).
  Interpolated with `privacy: .public`: `HandoffError`'s two cases carry a latitude/longitude pair and a
  waypoint count (`Sources/Handoff/HandoffError.swift`), and the coordinates in them are the hard-coded route
  constants, never the user's location - `SkylineHandoff.directions()` passes `source: nil`, which is how this
  screen avoids ever holding one. A `<private>` redaction here would log a failure with its reason removed.

  **R5 - the existing doc comment on `handoff()` argues against this task.** It says rewriting the message is
  "how the real reason stops reaching anybody". RULED: the premise is that the on-screen string is the only
  record of the failure. With the raw error going to `Logger`, it is not, so the comment is now false and is
  rewritten to say where the reason went. This is prose, not a check: CLAUDE.md forbids anchoring a pin, test
  or guard on a comment, and nothing here is anchored on one.

  **R6 - "exactly three user-visible changes, nothing else".** Added: a title, a caption, and a new string in
  the failure `Text`. The map being shorter (R3) is the mechanical consequence of putting a title above it, not
  a fourth change. Explicitly NOT touched: the button, its `primary`/`onPrimary` treatment and its 44 pt floor;
  `AttributionFooter` and its text; the map style, centre and zoom; the failure `Text`'s existing `.footnote`
  and `DesignTokens.destructive` treatment (only its STRING and its accessibility identifier change); and
  `DesignSystem`, which gains nothing - every token this screen needs (`bg`, `fg`, `fgMuted`, `destructive`)
  already exists, so `touches:` keeps `Sources/DesignSystem/` and no file under it is edited.

  **R7 - "one private enum" (owner's ruling 3) vs "one type per file, filename == type name" (CLAUDE.md).**
  RULED: a private enum `Copy` NESTED inside `ScenicHomeScreen`, not a second file-scope type. Nested types are
  members of `ScenicHomeScreen`, so the file still declares exactly one top-level type and still equals its
  filename, and the later `.xcstrings` extraction is still mechanical - each `static let` becomes a key and no
  call site moves. No `.xcstrings` file is introduced (serial-only, one language today), so `exclusive:` stays
  empty.

  **R8 - the title is a literal, and says so.** `Skyline via Cañada Road` names the drive
  `SkylineHandoff.waypoints` describes, but it is not derived from it: that file holds coordinates and no name,
  and T-0151 is editing it right now. A rename of the drive and a change to the waypoint list are therefore two
  edits that the compiler will not tie together. Written into the type's doc comment where a maintainer will
  see it, not left implicit.

  **R9 - the two ruled strings are transcribed byte for byte**, including the ASCII hyphen in
  `Preview build - this map is a stand-in, not your route. The drive opens in Apple Maps.` and the apostrophe in
  `Couldn't`. No typographic "improvement" (en dash, curly quote) was applied to copy the owner ruled on; the
  apostrophe is a contraction, not an apology.

  **Not in scope, per the owner's ruling 4 and the Brief:** no safety disclaimer (T-0153 owns it and edits this
  same file after me), no route line drawn, no edit to `SkylineHandoff.swift` (T-0151), no real basemap.

- 2026-09-18T20:39:30Z code written per R1-R9. One file changed:
  `apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift`. `Sources/DesignSystem/` is in
  `touches:` and is NOT edited - no new token was needed (R6). No `.xcstrings`, no manifest change, no edit to
  `SkylineHandoff.swift`.

  **The gate this task claims as proof, demonstrated RED BY NAME first.** `bash ops/lib/check-line-cap` is a
  line-count cap, and a cap that has only ever been seen green is a cap nobody has watched refuse. 130 filler
  lines appended to the file this task edits, then the gate run bare:

      $ for i in $(seq 1 130); do echo "// filler line ..." >> apps/.../ScenicHomeScreen.swift; done
      $ awk 'END{print NR}' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift
      309
      $ bash ops/lib/check-line-cap; echo "exit=$?"
      P-SRC-02: file(s) over the 300-line cap:
        apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift (309 lines)
      exit=1

  It names this file. Filler removed, same command, bare:

      $ awk 'END{print NR}' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift
      179
      $ bash ops/lib/check-line-cap; echo "exit=$?"
      P-SRC-02: 68 Swift files tracked (Sources=25, Tests=35, apps/ios=8), none over 300 lines
      exit=0

  No new check was written by this task, so this is the only red available to demonstrate locally: there is no
  test target in the Apple package (`Package.swift`: "NO TEST TARGETS HERE, deliberately and temporarily"), so
  the other proof is the compiler, dispatched below. `bash ops/check-pins` and `bash ops/test` were NOT run
  locally - the default swift scratch path does not build in a worktree on this box; `gh pr checks` is the
  record for those.

- 2026-09-18T20:47:15Z **the compiler ran, and it is green.** `d428da0` pushed to `task/T-0152`, then
  `gh workflow run ios-compile.yml --ref task/T-0152` -> run **35393000321**
  (https://github.com/phineasfritsch/scenic_drive/actions/runs/35393000321), `status: completed`,
  `conclusion: success`. ONE dispatch; nothing went red on the branch, so there is no red compile to quote and
  this entry does not invent one. From `gh run view 35393000321 --log`:

      1616:  ** BUILD SUCCEEDED **
      114:   Xcode 16.4
      115:   Build version 16F6
      119:   swift-driver version: 1.120.5
      1324:  SwiftCompile normal arm64 Compiling\ ScenicHomeScreen.swift .../FeatureScenicHome/ScenicHomeScreen.swift
             (in target 'FeatureScenicHome' from project 'ScenicApp')

  `grep -c "error:" <log>` -> `0`. The file this task edits is named in the log as compiled for both simulator
  architectures, so the green is about this change and not about a target that was skipped. The build wrote one
  untracked file, the same one the first run on main wrote:
  `?? apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved` - T-0167 owns
  committing it, this task adds no dependency and does not touch it.

  **STILL OPEN - what is NOT proven here.**
  1. **Nothing has rendered this screen.** No simulator run, no device, no snapshot, no screenshot. This whole
     tree has never been on a phone. `xcodebuild ... build` proves the three strings compile into
     `FeatureScenicHome` and that the layout type-checks; it proves nothing about what they look like. Every
     claim below about appearance is a reading of the code, not an observation.
  2. **Contrast is reasoned, not measured.** `fg`/`fgMuted` on `bg` are the token table's own pairs and the
     header band is drawn on `bg` (R3), but no contrast ratio was computed by this task and none is claimed.
  3. **The failure `Text` still draws over map tiles**, inside the bottom stack, in `destructive` at
     `.footnote` - untouched by this task except for its string and its identifier (R6). `destructive` over an
     arbitrary basemap has no guaranteed contrast, exactly the reason `AttributionFooter` carries its own chip.
     Whether it needs a chip is a design decision for the screen M4 replaces, and widening this task to take it
     would have been a fourth visible change.
  4. **No XCUITest anchors on `home.title`, `home.caption` or `home.error` yet.** The identifiers are placed
     for the suite that arrives with a test target; `Package.swift` says why there is none
     ("NO TEST TARGETS HERE, deliberately and temporarily"), and this task did not add one - a suite authored
     on a box with no Apple toolchain could never be seen red.
  5. **The title is not tied to the waypoints by anything mechanical** (R8). Renaming the drive and changing
     `SkylineHandoff.waypoints` are two independent edits; only review connects them.
  6. **Dynamic Type was not exercised.** `.title2`/`.subheadline` plus `fixedSize(horizontal: false,
     vertical: true)` is the intent that the largest accessibility sizes wrap rather than truncate; no size
     class was rendered to confirm the header band does not crowd the map at AX5.
  7. **`bash ops/check-pins` and `bash ops/test` were not run locally** (the default swift scratch path does
     not build in a worktree on this box). `gh pr checks` on the PR is the record for the Linux gates.

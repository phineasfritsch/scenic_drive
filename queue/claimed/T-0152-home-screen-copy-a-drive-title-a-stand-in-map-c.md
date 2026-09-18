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
  - "gh workflow run ios-compile.yml --ref task/T-0152 ; gh run view 35396900851 --json databaseId,headSha,status,conclusion -> {\"conclusion\":\"success\",\"databaseId\":35396900851,\"headSha\":\"d16a5e4713fb830b977d0f2641c91df04cf88399\",\"status\":\"completed\"} ; gh run view 35396900851 --log -> line 1613 '** BUILD SUCCEEDED **', with line 114 'Xcode 16.4', 115 'Build version 16F6', 120 'swift-driver version: 1.120.5'; grep -c 'error:' over that log -> 0; lines 1380 (x86_64) and 1427 (arm64) 'Compiling ScenicHomeScreen.swift (in target FeatureScenicHome from project ScenicApp)'. ONE dispatch for the amendment, green first time - no red compile to quote. The first half's green, 35393000321, sat on d428da0, an ancestor of d16a5e4"
  - "bash ops/lib/check-line-cap -> P-SRC-02: 68 Swift files tracked (Sources=25, Tests=35, apps/ios=8), none over 300 lines, exit 0"
  - "RED FIRST, re-run on the amended file: 130 filler lines appended -> awk 'END{print NR}' -> 329 -> bash ops/lib/check-line-cap -> 'P-SRC-02: file(s) over the 300-line cap:' / '  apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift (329 lines)', exit 1; filler removed -> 199 lines -> green above"
  - "awk 'END{print NR}' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> 199, exit 0"
  - "THE THREE RULED STRINGS, transcribed: grep -n 'static let title\\|static let route\\|static let mapCaption' -A1 <file> -> 180 'Skyline loop · ends back in San Francisco', 186 'I-280 south, Cañada Road north, CA-92 west, Skyline Boulevard south, then back to the city.', 193 'This map doesn't show roads yet. Tap below and the drive opens in Apple Maps.'; sed -n '180p;186p;193p' <file> | od -c -> '302 267' (U+00B7 MIDDLE DOT in the title, not a hyphen), '303 261' (U+00F1 in Cañada), and a plain ASCII apostrophe in doesn't - no typographic substitution was applied to copy the owner ruled on, exit 0"
  - "NO DURATION on the screen: grep -n 'minute\\|hour\\|[0-9] *hr\\|[0-9] *min\\|[0-9]h[0-9]\\|miles\\|[0-9] mi\\b' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> no output, exit 1 (no duration and no distance anywhere in the file: nobody has driven this route and no command here measured one)"
  - "grep -n 'accessibilityIdentifier(\"home\\.' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> 62:home.error, 96:home.title, 106:home.route (new in the amendment), 112:home.caption, 141:home.openInAppleMaps (pre-existing), exit 0"
  - "grep -n 'handoffFailure = \\|String(describing: error)' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> 150 (doc comment), 157 'handoffFailure = nil', 164 'Self.log.error(... String(describing: error), privacy: .public)', 165 'handoffFailure = Copy.handoffFailed'. The raw error reaches Logger and nothing else; the failure message is unchanged by the amendment, exit 0"
  - "grep -rn '0x[0-9A-Fa-f]\\{6\\}\\|Color(' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ -> no output, exit 1 (no raw hex and no ad-hoc Color in the feature target; colour comes from DesignTokens only)"
  - "grep -n '\\.font(' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift -> 58 .footnote, 91 .title2, 99 .subheadline, 109 .subheadline (the new home.route line), 131 .headline - five Dynamic Type text styles; grep -n '\\.system(size:\\|size: [0-9]' over the same file -> no output, exit 1, so no point size anywhere"
  - "git diff --name-only origin/main...HEAD -> apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift and queue/claimed/T-0152-*.md, exit 0"
  - "git diff --name-only origin/main...HEAD -- apps/ios/Packages/ScenicApp/Sources/DesignSystem/ -> no output, exit 0 (DesignSystem is in touches: and needed no edit: bg, fg, fgMuted, destructive all already exist)"
  - "git diff --name-only d16a5e4 -- '*.swift' -> no output, exit 0 (nothing Swift changed after run 35396900851 compiled d16a5e4; the record commit carries this file only)"
  - "gh pr checks 95, run once on head d16a5e4 -> core pass 1m48s .../actions/runs/35396903921/job/105767728624 ; pins-source-only pass 1m14s .../actions/runs/35396903921/job/105767728229, exit 0"
  - "git status --porcelain -> no output, exit 0"
  - "NOT RUN, on the record: bash ops/check-pins and bash ops/test (the default swift scratch path does not build in a worktree on this box) - gh pr checks 95 above is the record for the Linux gates. NOT DONE, on the record: nothing has rendered this screen - no simulator run, no device, no snapshot, no screenshot; this tree has never been on a phone, so every claim about how these three strings look is a reading of code"
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

- 2026-09-18T20:54:53Z PR **#95** opened, base `main`, head `task/T-0152`
  (https://github.com/phineasfritsch/scenic_drive/pull/95), carrying `d428da0` (the Swift) and `979641c` (this
  record). `gh pr checks 95` at first read: both `pending`; watched once to completion:

      core              pass  2m23s  .../actions/runs/35393737278/job/105757714627
      pins-source-only  pass  1m0s   .../actions/runs/35393737278/job/105757714873

  That is the record for the Linux gates this box cannot run in a worktree, and it is the only claim made about
  them - `ops/check-pins` and `ops/test` were not run locally. The ios-compile green (35393000321) sits on
  `d428da0`; `git diff --name-only d428da0 979641c -- '*.swift'` -> no output, so no Swift changed after the
  compiler saw it. `state: claimed` and `reviewer: null` are unchanged: the reviewer of this task is not its
  owner, and this session is the owner.

- 2026-09-18T21:30:52Z agent/claude-opus-5 (owner and author, second session on this task). **PART 2, the
  strings amendment. The ruling and its source first, before any code.** Nothing above this line was edited:
  the dated entries stand as written, including the ones describing the copy this amendment replaces. The
  `acceptance:` block was re-run and rewritten in full at the final commit - that block is a record of the
  current head, not a dated entry.

  **R10 - the copy is replaced, by the owner, verbatim.** Source: the 14:13 expert panel's two focus drivers,
  read against `ScenicHomeScreen.swift`, and the OWNER's ruling on them handed to this session. This session
  did not read the panel transcript and quotes nothing from it; what is ruled in is the three strings
  themselves, transcribed byte for byte:

      title    "Skyline loop · ends back in San Francisco"
      route    "I-280 south, Cañada Road north, CA-92 west, Skyline Boulevard south, then back to the city."
      caption  "This map doesn't show roads yet. Tap below and the drive opens in Apple Maps."

  They replace `Skyline via Cañada Road` and `Preview build - this map is a stand-in, not your route. The
  drive opens in Apple Maps.` from the first half. The failure string, `Couldn't open Apple Maps. Try again.`,
  is NOT touched - R1 above still holds and nothing in this amendment bears on it. The byte check is in the
  acceptance block: the title's separator is U+00B7 (`302 267` in `od -c`), not a hyphen, `Cañada` is `303
  261`, and `doesn't` carries a plain ASCII apostrophe. No typographic "improvement" was applied to copy the
  owner ruled on, exactly as R9 ruled for the first half's strings.

  **R11 - no duration, anywhere on this screen.** Ruled by the owner and adopted here with its reason on the
  record: two panel lenses guessed different numbers for this drive and nobody has measured it. This tree has
  never been on a phone, no handoff has ever been performed, and the ETA machinery the plan describes is not
  wired to this screen - so any minutes printed here would be a number no command produced. The first device
  handoff is what will measure it (T-0009's checklist). Written into the type's doc comment where the next
  author will see it before adding one, and given a grep in the acceptance block that fails if a duration or a
  distance ever appears in this file.

  **R12 - the new line's text style: the ruling names Dynamic Type and the muted token, and is silent on
  which style.** RULED: `.subheadline` and `DesignTokens.fgMuted` - the same pair the caption already uses,
  with `fixedSize(horizontal: false, vertical: true)` like its neighbours so the largest accessibility sizes
  wrap instead of truncating. Two reasons. It adds no new decision to the token table or the type scale
  (R6 from the first half: no new tokens, no new fonts). And the alternative, demoting the roads to
  `.footnote` under a `.subheadline` caption, would print the longest and most useful line on the screen -
  the only line that says where you would actually be - at the smallest size on it. Order in the band: title,
  then roads, then caption, which is the ruling's "a NEW second line under the title" read literally.
  Identifier `home.route`, per the ruling; `home.title`, `home.caption`, `home.error` and
  `home.openInAppleMaps` keep their names, so the identifiers a future XCUITest anchors on are stable across
  this copy change even though two of the strings behind them changed.

  **R13 - `Copy.mapIsAStandIn` is renamed to `Copy.mapCaption`.** The new caption does not say "stand-in", so
  the old member name described a string that no longer exists. Private, nested, one call site; the rename is
  mechanical and the compiler checked it (run below). The three-line `Copy` enum from R7 is otherwise
  unchanged: still nested, still not an `.xcstrings` catalog, so `exclusive:` stays empty.

  **T-0170 will reuse this line.** T-0170 (a copyable road list on a failed handoff) needs exactly the roads
  in order, which is why they are a named member, `Copy.route`, and not an inline literal in the `Text`. The
  note is in the source next to the string as well as here. Nothing in this task makes anything copyable -
  R1's finding still holds: there is no copy affordance anywhere in the Apple package, which is why the
  failure sentence still does not promise one.

  **What this amendment does NOT touch**, each one checked in the acceptance block or by the diff: the failure
  `Text`, its `destructive`/`.footnote` treatment and its string; the button, its `primary`/`onPrimary`
  treatment and its 44 pt floor; `AttributionFooter`, its text, and the map's lower-right corner (the band is
  above the map, R3, so it structurally cannot reach either); the map style, centre and zoom; `DesignSystem`
  (no file under it changed - the tokens used are `bg`, `fg`, `fgMuted`, `destructive`, all pre-existing);
  `SkylineHandoff.swift` and `SkylineRoute.swift` (T-0151 owns them and is editing them now); `Package.swift`
  and every other serial-only file. No safety disclaimer (T-0153 owns it), no route line drawn (M4).

  **The gate, demonstrated RED BY NAME again on the amended file.** `bash ops/lib/check-line-cap` is the only
  gate this box can run against this change, and the first half's red run was against a 179-line file that no
  longer exists. Re-run bare, on the file as amended:

      $ for i in $(seq 1 130); do echo "// filler line $i appended to demonstrate P-SRC-02 red by name" \
          >> apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift; done
      $ awk 'END{print NR}' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift
      329
      $ bash ops/lib/check-line-cap; echo "exit=$?"
      P-SRC-02: file(s) over the 300-line cap:
        apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift (329 lines)
      exit=1

  Filler removed, same command, bare:

      $ awk 'END{print NR}' apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift
      199
      $ bash ops/lib/check-line-cap; echo "exit=$?"
      P-SRC-02: 68 Swift files tracked (Sources=25, Tests=35, apps/ios=8), none over 300 lines
      exit=0

  **The compiler ran on the amendment, and it is green.** `d16a5e4` pushed to `task/T-0152` at
  2026-09-18T21:28:02Z, then `gh workflow run ios-compile.yml --ref task/T-0152` -> run **35396900851**
  (https://github.com/phineasfritsch/scenic_drive/actions/runs/35396900851), `headSha`
  `d16a5e4713fb830b977d0f2641c91df04cf88399`, `status: completed`, `conclusion: success`. ONE dispatch;
  nothing went red on the branch, so this entry has no red compile to quote and does not invent one. From
  `gh run view 35396900851 --log`:

      1613:  ** BUILD SUCCEEDED **
      114:   Xcode 16.4
      115:   Build version 16F6
      120:  swift-driver version: 1.120.5
      1380:  SwiftDriverJobDiscovery normal x86_64 Compiling ScenicHomeScreen.swift (in target
             'FeatureScenicHome' from project 'ScenicApp')
      1427:  SwiftDriverJobDiscovery normal arm64 Compiling ScenicHomeScreen.swift (in target
             'FeatureScenicHome' from project 'ScenicApp')

  `grep -c "error:" <log>` -> `0`, over a 1667-line log. The amended file is named as compiled for both
  simulator architectures, so the green is about this change and not about a skipped target. `gh pr checks 95`
  was read once on the same head: `core pass 1m48s`, `pins-source-only pass 1m14s` (run 35396903921). That is
  the record for the Linux gates - `bash ops/check-pins` and `bash ops/test` were NOT run locally, because the
  default swift scratch path does not build in a worktree on this box.

  **STILL OPEN - unchanged by this amendment, and the list from 20:47:15Z still stands in full.**
  1. **Nothing has rendered this screen.** No simulator run, no device, no snapshot, no screenshot. This tree
     has never been on a phone. The compiler proves the three strings and the third `Text` type-check into
     `FeatureScenicHome`; it proves nothing about what they look like. Whether three left-aligned lines in one
     band read as a hierarchy, whether the roads line wraps to two lines or four on a small phone, and whether
     the band crowds the map at AX5 are all unobserved.
  2. **The route line is prose about roads nothing verifies.** `Copy.route` names five roads; `SkylineHandoff`
     holds coordinates and no road names, and no test, pin or build step ties the sentence to the waypoints
     (R8, now covering the road list as well as the title). Only review connects them, and the coordinates
     themselves are being edited by T-0151 in another worktree as this is written.
  3. **No duration is claimed, and none is known.** R11: nobody has driven this route. The absence is the
     honest state, not a gap this task left for tidiness.
  4. **Contrast is reasoned, not measured** (20:47:15Z item 2), and the failure `Text` still draws over map
     tiles in `destructive` (item 3) - untouched here.
  5. **No XCUITest anchors on `home.route`** any more than on `home.title` or `home.caption`: there is still
     no test target in the Apple package (`Package.swift`: "NO TEST TARGETS HERE, deliberately and
     temporarily"), and a suite authored on a box with no Apple toolchain could never be seen red.
  6. **Dynamic Type was not exercised** (20:47:15Z item 6). R12's choice of `.subheadline` for the roads is an
     argument, not an observation.

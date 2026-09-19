---
id: T-0195
title: the app renders the LA Protomaps tiles - MapStyle gains a protomaps case (the built la.pmtiles through MapLibre's pmtiles protocol, services/tiles/styles as the style), attributionText becomes '(c) OpenStreetMap contributors - Protomaps', the demo-tiles case retired from the walking skeleton
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T06:53:46Z
lease_expires_at: 2026-09-19T12:53:46Z
worktree: .worktrees/T-0195
branch: task/T-0195
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/MapAdapter/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/]
pins_affected: []
reviewer: agent/rv1-pr112
depends_on: [T-0165]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MapStyle has a protomaps case whose style is one of services/tiles/styles/*.json (light/dark by appearance) and whose source is the LA PMTiles - RULE in the Log how the file reaches the device in this build (bundled in the app target for the walking skeleton, sized and quoted; the first-run download sheet is M4's) and how MapLibre reads it (the pmtiles:// protocol handler pinned by version in Package.resolved - exclusive: on that file if it changes); attributionText for that case is exactly '(c) OpenStreetMap contributors - Protomaps' (the plan's string, the (c) as the copyright sign) and a Linux-free test in the Apple package or a structural check pins it"
  - "the home screen's map surface uses the protomaps case; AttributionFooter shows the Protomaps string at every detent (the invariant); ios-compile dispatch green with the run id quoted; no MapLibre import outside MapAdapter (the structural check the package already has)"
  - "the demo-tiles case stays only if something still needs it - say what, or delete it and its '(c) MapLibre - Natural Earth' string"
  - "bash ops/lib/check-line-cap and bash ops/queue-check bare at the final commit"
---
## Brief

From T-0165's STILL OPEN 3 (the PMTiles build, PR #109): the artifact exists and the corner is reserved, but the
app still renders MapLibre's demo tiles and credits '(c) MapLibre - Natural Earth' - the product invariant
(attribution visible on every map surface) is only half met until the tiles ARE Protomaps and the string is the
plan's. M1.5's exit clause is the owner opening the app on the phone and tapping into Apple Maps on a drive the
owner can drive - in Los Angeles, over LA tiles. T-0009 (TestFlight) is the human step that puts it on the phone.

## Log
- 2026-09-19T05:38:57Z filed by agent/claude-fable-5-1 from T-0165's STILL OPEN 3 (PR #109). Not started; after #109 merges.
- 2026-09-19T06:53:41Z PROMOTED to ready/ by agent/claude-fable-5-1: #109 (T-0165) merged e31a7f1 - la.pmtiles 63,520,949 bytes is on disk in the shared work dir and the styles are committed; this task is the tiles-to-phone half the 00:13 panel named, and it touches MapAdapter/DesignSystem only, so it does not collide with #110 or T-0178 on ScenicHomeScreen.swift.
- 2026-09-19T06:53:46Z claimed by agent/claude-opus-5; lease until 2026-09-19T12:53:46Z
- 2026-09-19T07:00:19Z RULINGS by agent/claude-opus-5 (owner/author), before any code.

  **R1 - MapLibre 6.31.0 reads PMTiles natively; the source URL is `pmtiles://<file URL>`.**
  Evidence, all from the pinned SDK's own repository (`maplibre/maplibre-native`, which
  `maplibre-gl-native-distribution` ships as the binary XCFramework):

      $ gh api -H "Accept: application/vnd.github.raw" \
          repos/maplibre/maplibre-native/contents/platform/ios/CHANGELOG.md | grep -n -i pmtiles
      46:- Convert a PMTiles metadata decompression failure into an error response ... (#4399).
      60:- Implement ambient cache for PMTiles sources (#4290).
      89:- core: better handle tile compression in PMTiles sources (#4159).
      222:- Force PMTiles metadata to always have XYZ tile scheme (#3403).
      269:- Add support for [PMTiles](https://docs.protomaps.com/pmtiles/) with `pmtiles://` URL scheme (#2882).

      $ ... | grep -n "^## " | head
      5:## 6.31.0   10:## 6.30.0   ...   266:## 6.10.0   273:## 6.9.0

  Line 269 sits between the `## 6.10.0` heading (266) and the `## 6.9.0` heading (273), so `pmtiles://`
  landed in **iOS 6.10.0** and the pin, 6.31.0 (heading at line 5), is 21 minor releases past it - with the
  scheme still under active maintenance inside that window (#4399, #4290, #4159 are all above line 89, i.e.
  6.2x releases). Merged PRs, independently: 2882 (2025-01-07), 3403, 4159, 4278, 4399
  (`gh api "search/issues?q=repo:maplibre/maplibre-native+pmtiles+in:title+is:pr+is:merged"`).
  The SDK's own documentation, `platform/ios/MapLibre.docc/PMTiles.md`, states the two accepted forms:

      Starting MapLibre iOS 6.10.0, PMTiles archives are supported as tile sources. Prefix any tile
      source URL with `pmtiles://` to read from a PMTiles archive:
      - `pmtiles://https://` - stream tiles from a remote file
      - `pmtiles://file://`  - read a file from the device filesystem, including the app bundle
      ... Note: PMTiles sources do not support offline pack downloads or caching.

  So: no plugin, no protocol registration, no local tile server, and no `Package.resolved` change - the pin
  stays 6.31.0 exactly and no serial file is touched. The style's source URL is the literal string
  `"pmtiles://" + archiveURL.absoluteString`, i.e. `pmtiles://file:///.../la.pmtiles`. The doc's own caveat
  (no offline packs, no caching for PMTiles sources) is why nothing here tries to pre-warm a cache.

  **R2 - how the 63,520,949-byte archive reaches a device. Resolution order, in `BasemapResolver`:**
  (a) the app bundle - `Bundle.main.url(forResource: "la", withExtension: "pmtiles", subdirectory: "Tiles")`
      first, then the same lookup with no subdirectory (Xcode 26 buildable folders may flatten a
      synchronized folder's resources into the bundle root; checking both means the owner's copy is found
      either way rather than depending on an Xcode behaviour nobody here can run). The local, **gitignored**
      folder is `apps/ios/ScenicDrive/Tiles/`, carrying its own `.gitignore` - the root `.gitignore:47`
      already ignores `*.pmtiles` tree-wide, and the local one exists so the folder is in the checkout
      (a buildable folder that does not exist has nothing to synchronize) and so the rule is where the
      owner looks. The owner's one step before a device build, from the MAIN checkout:
          cp services/tiles/work/la.pmtiles apps/ios/ScenicDrive/Tiles/la.pmtiles
      63,520,949 bytes, sha256 3b711c7918f7ba7dcf88998e150c3423056aafe3c2948d19bb0ce290ae2b5a0a
      (`services/tiles/work/la.pmtiles.json`). It is NEVER committed.
  (b) `Application Support/tiles/la.pmtiles` - the home M4's first-run download sheet writes to. Nothing
      writes it today; the resolver reads it so that M4 is a download, not a rewiring.
  (c) neither present -> `.maplibreDemoTiles` with its existing, honest caption. This is the ios-compile
      runner's path and every device build before the owner copies the file: no `la.pmtiles` exists there,
      and nothing in this code requires it to. **The Protomaps credit is never shown over non-Protomaps
      tiles**, because the credit is not a separate string - it is `MapStyle.attributionText`, on the same
      case as `MapStyle.url`, decided by one `switch`.

  **R3 - the attribution string and the check that pins it.**
  `MapStyle.protomapsAttribution` is a `public static let` holding exactly the plan's string
  (`CLAUDE.md:58`): `© OpenStreetMap contributors · Protomaps` - copyright sign, middle dot with spaces.
  `MapStyle.demoAttribution` holds the demo line the same way. The type rule stands: `url` and
  `attributionText` switch over the same cases in the same file, and `BasemapResolver` returns a `MapStyle`
  (never a bare URL), so there is no way to select a basemap without carrying its credit.
  A test in the Apple package is unavailable by deliberate choice (that manifest ships no test target; an
  XCTest bundle authored on a box with no Apple toolchain could never be seen red), and a bash check under
  `ops/lib` or `apps/ios/ci_scripts` is outside this task's `touches:`. **Ruled:** the structural check is
  the greppable identifier. **RECORDED FOR T-0197** (pin P-ATTR-01), the exact assertions:
      grep -c 'public static let protomapsAttribution = "© OpenStreetMap contributors · Protomaps"' \
          apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapStyle.swift   # == 1
      grep -c 'return MapStyle.protomapsAttribution' .../MapStyle.swift                              # == 2
      grep -c 'public init(text: String)' .../DesignSystem/AttributionFooter.swift                   # == 1
        (no default argument: a default is the string that stays put when the tiles change)
      grep -rn 'AttributionFooter(' apps/ios/Packages/ScenicApp/Sources | grep -v 'style.attributionText'
        # empty: every mount takes its text from the style it rendered
  None of those anchor on a comment.

  **R4 - the style JSON travels as an embedded literal, not a bundle resource.**
  `apps/ios/Packages/ScenicApp/Package.swift` declares `MapAdapter` with `path:`, `dependencies:` and
  `swiftSettings:` and **no `resources:`** - so a `.json` dropped into `Sources/MapAdapter/` is an
  unhandled file: SPM warns and does not copy it, and the app would load nothing. Making it a resource
  means editing `Package.swift`, a SERIAL-ONLY file, for a 194-line document read once at launch.
  **Ruled: no serial-file change, no `exclusive:`.** Each style becomes one type in one file -
  `ScenicLightStyle.json` / `ScenicDarkStyle.json` - a raw string literal (`#"""`) that is **byte-equal**
  to `services/tiles/styles/scenic-{light,dark}.json`, 194 lines of content inside a ~215-line file, under
  the 300-line cap. A raw literal needs no escaping, so the bytes are the file's bytes.
  **RECORDED FOR T-0197/T-0201:** `services/tiles/tests` must assert that byte-equality (extract the lines
  between `#"""` and `"""#` from each Swift file and compare with the JSON, trailing newline aside), so
  that regenerating a style with `make_styles.py` and not the Swift file goes red. That test is outside
  `touches:`; the equivalent comparison is demonstrated red and green in this Log below instead.
  **The placeholder:** `make_styles.py` writes `"url": "pmtiles://la.pmtiles"` into `sources.protomaps` and
  `services/tiles/README.md` says "the app rewrites it to the on-device file URL". `ScenicStyleDocument`
  replaces that exact literal with `pmtiles://<archive file URL>` and writes the result to
  `Caches/ScenicDrive/Styles/scenic-{light,dark}.json` (Caches: regenerable, and the one path
  `MapStyle.url` names for those cases). If the placeholder is **absent** the substitution returns nil and
  the resolver falls back to (c) - a drifted style can never be rendered under the Protomaps credit.

  **R5 - the demo case stays, as (c) and only as (c).**
  Disagreement ruled: `MapStyle`'s own doc says the demo case "is **not** a fallback and must not become
  one ... When the PMTiles style lands, this case goes away". Taken literally, an app with no archive on
  the device would have no basemap at all - and the ios-compile runner and every pre-copy device build are
  exactly that. What that sentence was protecting against is a *silent* fallback: tiles swapped under a
  credit line that keeps naming the old ones. That failure is structurally impossible here (R3: one case
  carries both halves), so the case is **kept as the explicit, credited fallback** and its doc is rewritten
  to say which of the two it is. With no LA archive on the device the home screen shows what it shows
  today: MapLibre demo tiles under `© MapLibre · Natural Earth`. Nothing regresses; nothing is faked.

  **Not mine, recorded for T-0178 (PR #110 owns `FeatureScenicHome`).** The switch cannot live in a
  MapAdapter default: `ScenicHomeScreen.swift:35` names the case itself
  (`private let style = MapStyle.maplibreDemoTiles`). The ONE-LINE change, when T-0178 takes it:
      -    private let style = MapStyle.maplibreDemoTiles
      +    private let style = BasemapResolver.losAngeles()
  `BasemapResolver.losAngeles()` returns a `MapStyle`, so `style.url` (`:60`) and `style.attributionText`
  (`:93`) are untouched, and the stale comment at `:90-92` ("This is NOT the plan's `©
  OpenStreetMap contributors · Protomaps` line") becomes wrong on a device that has the archive and should
  go with it. `DesignSystem/` needs no change at all: `AttributionFooter` already takes its text from the
  style, which is why the Protomaps string reaches it the moment that one line changes.

- 2026-09-19T07:19:30Z BUILT by agent/claude-opus-5 (owner/author). Six files under `touches:`, no serial file,
  no `exclusive:` taken, `DesignSystem/` unchanged (R5's last paragraph says why).

      apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapStyle.swift            105 lines (was 56)
      apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapAppearance.swift        50 lines (new)
      apps/ios/Packages/ScenicApp/Sources/MapAdapter/ScenicStyleDocument.swift  83 lines (new)
      apps/ios/Packages/ScenicApp/Sources/MapAdapter/BasemapResolver.swift      88 lines (new)
      apps/ios/Packages/ScenicApp/Sources/MapAdapter/ScenicLightStyle.swift    221 lines (new, generated)
      apps/ios/Packages/ScenicApp/Sources/MapAdapter/ScenicDarkStyle.swift     221 lines (new, generated)
      apps/ios/ScenicDrive/Tiles/.gitignore                                     21 lines (new, 100644 data)

  `MapStyle` gains **two** protomaps cases, `protomapsLALight` and `protomapsLADark`, not one. Ruled, since
  the acceptance says "a protomaps case": the enum is `String`-raw-valued and `CaseIterable`, and an
  associated value would take both away; the two generated styles are two documents at two paths, so `url`
  cannot answer for "protomaps" without knowing which appearance - and giving `url` an argument would let a
  caller take a URL without the matching credit, which is the one thing this type exists to prevent. The
  acceptance's own words ("light/dark by appearance") are what two cases spell in a raw-value enum.

  **RED FIRST, twice, both named.**

  (1) The embedded-style byte-equality property - R4's check, recorded for `services/tiles/tests` under
  T-0197/T-0201, run here from a throwaway script under `DerivedData/` (gitignored; not committed, because
  `ops/` and `services/` are outside `touches:`):

      $ python DerivedData/T-0195-tools/embedded_styles.py check     # before the files existed
      DRIFT ScenicLightStyle.swift: missing
      DRIFT ScenicDarkStyle.swift: missing
      EMBEDDED-STYLES failed=2
      exit=1

      $ python DerivedData/T-0195-tools/embedded_styles.py gen
      $ python DerivedData/T-0195-tools/embedded_styles.py check
      OK    ScenicLightStyle.json == scenic-light.json (4563 bytes)
      OK    ScenicDarkStyle.json == scenic-dark.json (4591 bytes)
      EMBEDDED-STYLES failed=0
      exit=0

  A missing file is a weak red, so the real failure mode - drift - was demonstrated too: one hex digit
  changed in the Swift copy (`#FFF7ED` -> `#FFF7EE`, the `background` layer's paint):

      DRIFT ScenicLightStyle.json != scenic-light.json
            line 27: json='        "background-color": "#FFF7ED"' swift='        "background-color": "#FFF7EE"'
      EMBEDDED-STYLES failed=1
      exit=1

  then regenerated and green again. That is exactly what a `make_styles.py` run that forgets this copy looks
  like, which is why the assertion is written out for T-0197/T-0201 rather than left as a promise.

  (2) `bash ops/lib/check-line-cap` (P-SRC-02), red by name on a real file - 220 filler lines appended to
  `BasemapResolver.swift`:

      P-SRC-02: file(s) over the 300-line cap:
        apps/ios/Packages/ScenicApp/Sources/MapAdapter/BasemapResolver.swift (308 lines)
      red_exit=1

  **Worth recording, because it cost a first attempt:** the same 308-line file produced
  `P-SRC-02: 73 Swift files tracked ... none over 300 lines`, exit 0, while it was still **untracked**. The
  check reads `git ls-files` by design (its own header: "so untracked build junk is never counted and the
  check matches what is actually committed"), so a new file is exempt from the cap until it is staged. The
  red above is the run after `git add`. Nothing to fix - but an agent who writes a 400-line file, runs this
  check green and commits has been told OK by a check that could not see the file.

  After restoring the file (88 lines):

      P-SRC-02: 78 Swift files tracked (Sources=26, Tests=37, apps/ios=15), none over 300 lines
      green_exit=0

  `apps/ios` went 10 -> 15: the five new Swift files are in the population, under the cap, and counted.

  **THE COMPILER. ios-compile run 35428810018, dispatched ONCE, green first time.**

      $ gh workflow run ios-compile.yml --ref task/T-0195
      $ gh run view 35428810018 --json status,conclusion,headSha
      completed success d442f37555f3c2ba6ef89df72389dc99ffa250d3      <- this branch's commit

      $ gh run view 35428810018 --log > ios-compile.log   # 660,477 bytes
      $ grep -c '\*\* BUILD SUCCEEDED \*\*' ios-compile.log   -> 1
      $ grep -c ' error:' ios-compile.log                     -> 0
      simulator-build  build for the iOS Simulator  2026-09-19T07:16:33.8136920Z ** BUILD SUCCEEDED **

  The one warning in the build step is `appintentsmetadataprocessor ... No AppIntents.framework
  dependency found`, which is the toolchain and not this code. **What that run did and did not prove:**
  the five new files compile under Swift 6 language mode against MapLibre 6.31.0 and link into the app,
  and the app still builds with the resolution order in it. The runner has no `la.pmtiles` and no way to
  get one, so it necessarily exercised branch (c) - `BasemapResolver.archiveURL` returned nil and the
  resolver returned `.maplibreDemoTiles`. Nothing on any machine has yet rendered the LA tiles; the first
  proof of that is the owner's device build (STILL OPEN 4).

  **Handed to T-0197, whose acceptance already asks for exactly this.** `queue/backlog/T-0197-...md`
  (`depends_on: [T-0165, T-0195]`) says P-ATTR-01's assertion, until T-0180's XCUITest exists, is "the
  structural check that MapStyle's attributionText for the protomaps case is the plan's string and that
  AttributionFooter is not accessibilityHidden ... demonstrated red first". Both anchors now exist as
  identifiers rather than as prose: `MapStyle.protomapsAttribution` (with `attributionText` returning it for
  both protomaps cases) and `AttributionFooter`'s `.accessibilityIdentifier("attribution.footer")` /
  `.accessibilityHidden(false)`, which T-0141 already wrote as explicit stated values for this reason. The
  four assertions written out in R3 are the ones to lift.

  **Handed to T-0201/T-0197: the embedded-style drift test.** It belongs under `services/tiles/tests`
  (outside this task's `touches:`), and the script that demonstrated it here was deliberately not committed
  for the same reason. Red is free: change a hex digit in either Swift file, or regenerate the JSON without
  the Swift.

  **THE WHOLE ACCEPTANCE BLOCK, RE-RUN BARE AT THE FINAL PRE-REVIEW COMMIT** (2026-09-19T07:39Z; the only
  change to the tree after these runs is this Log entry).

  A1 - *"MapStyle has a protomaps case whose style is one of services/tiles/styles/*.json (light/dark by
  appearance) and whose source is the LA PMTiles ... attributionText for that case is exactly the plan's
  string and a Linux-free test in the Apple package or a structural check pins it"*: `protomapsLALight` /
  `protomapsLADark` (R1 on two cases above), each `url` the materialised copy of the matching generated
  style, each source the archive `BasemapResolver` found, each `attributionText`
  `MapStyle.protomapsAttribution`. How the file reaches the device is R2, sized and quoted
  (63,520,949 bytes); how MapLibre reads it is R1 (native `pmtiles://` since 6.10.0, pin 6.31.0 - and so
  `Package.resolved` does NOT change and no `exclusive:` was taken). The check is structural and greppable
  by identifier; T-0197 owns turning it into P-ATTR-01, and its acceptance already asks for exactly it.

      $ grep -c 'public static let protomapsAttribution = "© OpenStreetMap contributors · Protomaps"' \
            apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapStyle.swift
      1
      $ grep -c 'return MapStyle.protomapsAttribution' \
            apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapStyle.swift
      1        # one `return` serving both protomaps cases in a single `case a, b:` arm

  A2 - *"the home screen's map surface uses the protomaps case; AttributionFooter shows the Protomaps
  string at every detent; ios-compile dispatch green with the run id quoted; no MapLibre import outside
  MapAdapter"*: **HALF MET, AND SAID SO.** The home screen is `FeatureScenicHome`, which is outside this
  task's `touches:` and owned by T-0178 / PR #110; editing it here is the collision the promotion note
  says this task avoids. The one-line change is written out above and repeated in the PR as STILL OPEN 1,
  and `AttributionFooter` needs no change to show the string once it lands. The rest is met:

      $ gh run view 35428810018 --json status,conclusion,headSha
      completed success d442f37555f3c2ba6ef89df72389dc99ffa250d3
      $ grep -c '\*\* BUILD SUCCEEDED \*\*' ios-compile.log -> 1 ; grep -c ' error:' -> 0

      $ grep -rn "import MapLibre" apps/ios
      apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapView.swift:2:import MapLibre
      apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapView.swift:7:/// **The only `import MapLibre` ...

  One import, in MapAdapter, unchanged by five new files in that target.

  A3 - *"the demo-tiles case stays only if something still needs it - say what, or delete it"*: it stays,
  and what needs it is every device and every CI runner without a 63 MB archive - R5, and the ios-compile
  run above is the witness, since that runner took branch (c) to reach BUILD SUCCEEDED. Its
  `© MapLibre · Natural Earth` string stays with it, now as `MapStyle.demoAttribution`.

  A4 - *"bash ops/lib/check-line-cap and bash ops/queue-check bare at the final commit"*, plus
  `ops/check-pins --source-only` once:

      $ bash ops/lib/check-line-cap
      P-SRC-02: 78 Swift files tracked (Sources=26, Tests=37, apps/ios=15), none over 300 lines
      exit 0
      $ bash ops/queue-check
      QUEUE OK (196 tasks)
      exit 0
      $ bash ops/check-pins --source-only
      PINS ok=13 skipped=14 pending=1 expired=0 failed=0 tier=linux source-only
      exit 0

      $ wc -l apps/ios/Packages/ScenicApp/Sources/MapAdapter/*.swift
         88 BasemapResolver.swift      50 MapAppearance.swift        105 MapStyle.swift
         66 MapView.swift (untouched) 221 ScenicDarkStyle.swift      221 ScenicLightStyle.swift
         83 ScenicStyleDocument.swift  834 total
      $ python DerivedData/T-0195-tools/embedded_styles.py check
      OK ScenicLightStyle (4563 bytes) / OK ScenicDarkStyle (4591 bytes) / failed=0, exit 0

  `ops/test` is in `verify:` and was NOT run: this session's environment forbids it, and it could only
  report the Linux tier, which nothing here touches (no file outside `apps/ios/` changed). Recorded as a
  gap rather than implied by silence; the reviewer's own run is the one that counts.

  STILL OPEN, all five, are in the PR body: the home-screen line (T-0178), P-ATTR-01 unfiled (T-0197), the
  embedded-style drift test uncommitted (T-0197/T-0201), no device has drawn these tiles (T-0009), and
  appearance is a defaulted parameter not yet wired to `colorScheme` (same file T-0178 owns). One more,
  found while writing and not fixed here because the compiler proof above is bound to this exact tree:
  `BasemapResolver.losAngeles()` rewrites the style document on every call, and SwiftUI may call a screen's
  property initialiser repeatedly - the write is ~4.5 KB and atomic, but an idempotent skip (compare bytes
  first) belongs in whichever task wires the call site. Changing it after a green run would leave the
  claimed compiler proof pointing at a commit that no longer exists.

  state: claimed and reviewer: null are untouched by this entry. Never self-review.
- 2026-09-19T07:53:50Z **Record from the structural mutant pass on this build (e73ffd5), closed before the review is bought -
  agent/claude-fable-5-1 (orchestrator), for the owner. The pass read every new file, confirmed the shipped
  tree correct (MapStyle.swift:99-102 hands the Protomaps credit to the two protomaps cases and the demo credit
  to the demo case; the literals byte-equal services/tiles/styles; 'import MapLibre' in MapView.swift only; no
  serial file changed; ios-compile 35428810018 green by sha d442f37) and found THREE survivors, none blocking,
  all of one class: nothing on Linux refuses a wrong credit or a wrong source - (M1) the two credit arms
  swapped: no pin, check or test refuses it, and the four grep assertions recorded for T-0197 at Log :100-107
  would not either (both 'static let' and 'return MapStyle.protomapsAttribution' counts are unchanged when the
  two return lines trade arms) - T-0197 needs an ARM-anchored assertion (the line after 'case .protomapsLALight,
  .protomapsLADark:' returns protomapsAttribution; the demo arm likewise); (M2) the resolution order swapped so
  demo wins with the archive present is benign (demo URL + demo credit travel together), but the credit is tied
  to the CASE, not to what MapLibre actually loaded - a style-load or archive-open failure at runtime draws
  nothing under the Protomaps credit, and only a device can see it (STILL OPEN 4); BasemapResolver.losAngeles
  has zero call sites in the shipped tree, so today nothing mounts it; (M3) the placeholder substitution made a
  no-op hands the renderer a relative 'pmtiles://la.pmtiles' - blank map under the Protomaps credit; and the
  two protomaps cases are public RawRepresentable cases whose url is a Caches path with no existence check, so
  a caller bypassing BasemapResolver gets a URL to a file that may not exist. Recorded here and on T-0197; the
  reviewer judges whether the direct-case path should refuse (an internal initializer) in this PR.**
- 2026-09-19T08:05:21Z **REVIEW PASS by agent/rv1-pr112 (reviewer, not the owner) - PR #112, head 8eceeb4, base main.**
  Reviewed on a detached worktree at 8eceeb4 (`.worktrees/rv1-pr112`, removed after). Nothing fixed here; every
  finding below is recordable and named for a later task.

      $ git diff main...8eceeb4 --stat
      ... MapAdapter/{BasemapResolver,MapAppearance,MapStyle,ScenicDarkStyle,ScenicLightStyle,ScenicStyleDocument}.swift
      ... apps/ios/ScenicDrive/Tiles/.gitignore | 21 ++ ; the task file | 311 ++ ; 8 files, 1069 insertions(+), 25 deletions(-)
      $ git diff --name-only main...8eceeb4 | grep -E "Package.swift|pbxproj|Package.resolved"     # empty, exit 1
      $ git diff main...8eceeb4 -- <task file> | grep -c "^-[^-]"                                   # 0 (append-only)
      $ git diff --name-only d442f37..8eceeb4                                                       # the task file only
      $ gh run view 35428810018 --json status,conclusion,headSha
      completed success d442f37555f3c2ba6ef89df72389dc99ffa250d3       (read by id once; no Swift moved since)

  **Gates, bare.** `bash ops/lib/check-line-cap` -> `P-SRC-02: 78 Swift files tracked (Sources=26, Tests=37,
  apps/ios=15), none over 300 lines`, exit 0. `bash ops/queue-check` -> `QUEUE OK (196 tasks)`, exit 0.
  `bash ops/check-pins --source-only` -> `PINS ok=13 skipped=14 pending=1 expired=0 failed=0 tier=linux
  source-only`, exit 0. `grep -rn "import MapLibre" apps/ios` -> `MapView.swift:2` and its own doc line, nothing
  else. `git ls-files -s apps/ios/ScenicDrive/Tiles/.gitignore` -> `100644`; it ignores `*.pmtiles` and
  `*.pmtiles.json` and keeps itself. Every `wc -l` the Log quotes re-measured and equal (88/50/105/221/221/83).

  **R4 re-derived by the reviewer, not read from the Log.** A python extractor pulled the bytes between
  `public static let json = #"""` and `"""#` out of each Swift file and compared them with the JSON:

      literal 4563 bytes sha256 b1b3435c638e124d == services/tiles/styles/scenic-light.json  (4563, same sha)
      literal 4591 bytes sha256 29a090cf12d7f9fa == services/tiles/styles/scenic-dark.json   (4591, same sha)
      placeholder "url": "pmtiles://la.pmtiles" = 1 in each literal and 1 in each JSON; 0 CR bytes on either side

  Stronger than the Log claims: the JSON files carry **no** trailing newline, so the literals are byte-identical,
  not "byte-equal bar the trailing newline". **R1 re-derived:** `gh api ... platform/ios/CHANGELOG.md` - the
  `pmtiles://` URL-scheme line (#2882) is line 269, between `## 6.10.0` (266) and `## 6.9.0` (273); the pin is
  `exact: "6.31.0"` at `apps/ios/Packages/ScenicApp/Package.swift:45`, heading line 5. Both hold.

  **THREE MUTANTS OF THE REVIEWER'S OWN** (read + structural; no Swift compiler on this box), each applied to the
  worktree, run against every check the repository can bring to bear (`check-line-cap`, `queue-check`, the
  byte-equality extractor, R3's four recorded greps, the `import MapLibre` structural check), then
  `git checkout --` restored with `git status --short` empty:
  - **(a) `.atomic` dropped** from `ScenicStyleDocument.materialize`'s write (`ScenicStyleDocument.swift:80`):
    SURVIVOR, every check byte-identical to baseline. It matters more than it looks: this Log already records
    that SwiftUI may re-run a screen's property initialiser, so two overlapping non-atomic writes to the one
    caches path hand the renderer a truncated style - a parse error under the Protomaps credit. Recordable with
    the idempotent-skip note the owner already left for the call-site task.
  - **(b) the Application Support existence guard deleted** (`BasemapResolver.swift:79-82`): SURVIVOR. The wider
    point the mutant exposes is in the shipped tree: **`archiveURL` asks "does it exist", never "is it whole"**.
    `Bundle.url(forResource:)` answers yes for a 0-byte `la.pmtiles`, `fileExists` likewise, and
    `materialize` never opens the archive - so an interrupted 63 MB `cp` (the owner's documented step) yields
    `.protomapsLALight` and puts `© OpenStreetMap contributors · Protomaps` over tiles MapLibre cannot read.
    The material for a floor is already committed: `services/tiles/work/la.pmtiles.json` carries the byte count
    and the sha256. NOT blocking in round 1 - `grep -rn "BasemapResolver\|losAngeles" apps/ios` outside
    `Sources/MapAdapter/` is **empty**, and `ScenicHomeScreen.swift:35` still mounts `.maplibreDemoTiles` with
    `AttributionFooter(text: style.attributionText)` at `:93`, so the credit the shipped tree actually draws is
    the true one. Recorded for whoever wires the call site (T-0178) and for T-0197.
  - **(c) `MapAppearance.styleJSON`'s light/dark arms swapped** (`MapAppearance.swift:23-28`): SURVIVOR,
    including against the byte-equality test recorded for T-0201 - that test compares each literal with its JSON
    and never looks at which literal an appearance picks. Consequence is not a false credit (both arms are
    Protomaps tiles under the right string) but the materialised document is mis-named on the device
    (`scenic-dark.json` holding the light style), which is what a support bundle is read from. One arm-anchored
    assertion in T-0201's drift test closes it.

  **Two more recordables.** (1) The fourth P-ATTR-01 assertion recorded in R3 -
  `grep -rn 'AttributionFooter(' apps/ios/Packages/ScenicApp/Sources | grep -v 'style.attributionText'  # empty` -
  is **already red** on this tree and on main: it matches `MapStyle.swift:92`, a doc comment. T-0197 must not
  lift it verbatim (CLAUDE.md: never anchor a pin on a comment) - it wants the mount sites, not the string.
  (2) **R4's shape is right; keep the literal.** A `resources:` declaration would edit the serial
  `apps/ios/Packages/ScenicApp/Package.swift` and buy nothing the drift test does not. But nothing committed
  sees these files today: `grep -rln "protomapsAttribution\|ScenicLightStyle\|BasemapResolver\|MapStyle" ops pins
  services` is empty. The drift test is the whole guard and it is still uncommitted (STILL OPEN 3).
  **R2, what the tree can and cannot answer:** `project.pbxproj` declares `ScenicDrive` as a
  `PBXFileSystemSynchronizedRootGroup` for the app target with `membershipExceptions = (Info.plist,)`, so a file
  dropped into `apps/ios/ScenicDrive/Tiles/` does get target membership - that much is verifiable here. Whether
  Xcode preserves the `Tiles/` subdirectory in the bundle or flattens it is not, and the resolver hedges both;
  whether Xcode copies a 63 MB unknown-type file at all can only be answered by a device build (T-0009).

  **Verdict: PASS.** No BLOCKING finding: the shipped tree produces no false credit on any surface (no surface
  calls the resolver yet) and no wrong source under the Protomaps credit. The P-ATTR-01 gap - nothing in the
  repository refuses a swapped credit - is T-0197's by prior record, not a finding against this PR. STILL OPEN
  1-4 stand as the PR states them: the home-screen one-liner (T-0178), P-ATTR-01 unfiled (T-0197), the drift test
  uncommitted (T-0197/T-0201), no device has drawn these tiles (T-0009). Not done by this review: `ops/test` and
  the full `ops/check-pins` (forbidden to this session), and no Swift was compiled here - run 35428810018 is the
  only compiler proof and it exercised fallback branch (c). `queue/claimed/` -> `queue/done/`.

---
id: T-0195
title: the app renders the LA Protomaps tiles - MapStyle gains a protomaps case (the built la.pmtiles through MapLibre's pmtiles protocol, services/tiles/styles as the style), attributionText becomes '(c) OpenStreetMap contributors - Protomaps', the demo-tiles case retired from the walking skeleton
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T06:53:46Z
lease_expires_at: 2026-09-19T12:53:46Z
worktree: .worktrees/T-0195
branch: task/T-0195
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/MapAdapter/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/]
pins_affected: []
reviewer: null
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

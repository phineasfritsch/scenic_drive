---
id: T-0141
title: M1.5 walking skeleton: the Apple package authored here, compiled by Xcode Cloud - map, attribution, one hard-coded Skyline handoff
state: claimed
owner: agent/claude-fable-5-1
owner_session: 01GCfruUmkJyV6Gxgq8x4o93
claimed_at: 2026-09-18T01:40:00Z
lease_expires_at: 2026-09-18T13:40:00Z
worktree: .worktrees/T-0141
branch: task/T-0141
exclusive: [pbxproj, package-swift]
touches: [apps/ios/, ops/lib/, pins/PINS.yaml, queue/]
pins_affected: [P-SRC-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "root Package.swift references nothing under apps/: `git diff --stat origin/main -- Package.swift` prints nothing, and `grep -cE '^ *[.]package[(].*apps/' Package.swift` -> 0 (grep -c exits 1 on a zero count: the printed count is the assertion, never the status). A comment cannot satisfy that grep (round-1 finding 2): over a control file carrying one real .package(...) line whose path starts with apps/ plus a comment naming the same path, it -> 1, while the round-0 `grep -c apps/ Package.swift` -> 1 on the real tree and is counting Package.swift:4, a comment"
  - "the Apple package's path dependency lands on the root package, not on apps/ (round-1 BLOCKING finding 1): run from apps/ios/Packages/ScenicApp, `swift package --scratch-path ../../../../.artifacts/T-0141/spm dump-package` emits the fileSystem dependency as nameForTargetDependencyResolutionOnly ScenicDrive at the checkout root (a directory that has a Package.swift), and `swift package --scratch-path ../../../../.artifacts/T-0141/spm resolve` -> `Working copy of https://github.com/maplibre/maplibre-gl-native-distribution resolved at 6.31.0`, exit 0. RED at the reviewed `path: ../../..`: dump-package emits identity apps, resolve prints `error: the package manifest at <checkout>/apps/Package.swift cannot be accessed`, exit 1. Manifest resolution only - nothing here was compiled"
  - "`bash ops/lib/check-line-cap` -> `P-SRC-02: 48 Swift files tracked (Sources=17, Tests=23, apps/ios=8), none over 300 lines`, exit 0. RED by the NAME of an emptied root (round-1 finding 6): `git rm --cached $(git ls-files 'apps/ios/**/*.swift')` then the same command -> `P-SRC-02: root(s) matching no tracked .swift file: apps/ios`, exit 1; before this round that identical state printed `apps/ios=0` and exited 0"
  - "one type per file under apps/ios/: `git ls-files 'apps/ios/**/*.swift' | xargs -n1 grep -cE '^(public )?(struct|enum|class|final class|actor) ' | sort | uniq -c` -> `1 0` (Package.swift, a manifest) and `7 1` (every source file), i.e. no file declares two"
  - "`bash ops/check-pins --source-only` -> `PINS ok=8 skipped=11 pending=1 expired=0 failed=0 tier=linux source-only`, exit 0; `bash ops/queue-check` -> `QUEUE OK (140 tasks)`, exit 0. Both run bare, never piped (a pipe swallows the exit status)"
  - "`python ops/lib/check-pbxproj-graph.py` -> `pbxproj-graph: 28 assertions, 0 failed`, exit 0. The script now lives under ops/ instead of gitignored .artifacts/ (round-1 finding 7), mode 100644 like every other *.py under ops/. RED by name: re-add NSLocationWhenInUseUsageDescription to apps/ios/ScenicDrive/Info.plist -> `FAIL NSLocationWhenInUseUsageDescription is absent because nothing asks for location  present`, exit 1; on the green tree that same line's detail column now reads `absent` (round-1 finding 10)"
  - "the MapLibre tag pinned in Package.swift exists: `gh api repos/maplibre/maplibre-gl-native-distribution/releases --jq '.[0:5][].tag_name'` -> 6.31.0 6.30.0 6.29.0 6.28.0 6.27.0, and apps/ios/Packages/ScenicApp/Package.swift:45 pins exact 6.31.0"
  - "every SkylineHandoff waypoint has its Nominatim query and returned lat/lon in the Log; the round-1 reviewer re-checked three of the five (ways 23995546, 305925415, 27672021) to 7 decimals"
  - "NOT COMPILED HERE, on the record: no Apple toolchain exists on this box. The Xcode Cloud build is T-0009's proof and needs the human's M0 steps. This task's exit is a tree Xcode Cloud can build, not a build. SPM manifest resolution is not a build"
---
## Brief

M1.5 in the plan: *"Thin app: MapLibre map + Bay Area PMTiles + AttributionFooter + 'Open in Apple Maps' with a
hard-coded Skyline waypoint list; internal TestFlight. You open it on your phone in week 2 and tap into Apple
Maps on Skyline."* Nothing under `apps/ios/` exists except `ci_scripts/ci_post_clone.sh`. Every milestone after
M1 assumes this exists. It has not been started because it was filed as needing a Mac (T-0010, "~2 MacinCloud
hours") - and there is no Mac.

**What needs a Mac and what does not.** The Swift in the Apple package is text; the `project.pbxproj` is text;
Xcode Cloud is the compiler, and it is the plan's only path to a phone anyway. So the package and the shell are
authored HERE, compiled THERE, and the first Xcode Cloud build (T-0009's `device/*` push) is the proof. This
task ends with a tree Xcode Cloud can build, not with a build - and says so.

### Assumptions, stated rather than asked

1. M0's human steps (Apple Developer Program, App Store Connect record, Xcode Cloud connected with
   cloud-managed signing) may not be done. This task does not depend on them; T-0009 does.
2. There is no PMTiles/R2 basemap yet (`services/tiles/` does not exist). The skeleton loads MapLibre's
   public demo style (`https://demotiles.maplibre.org/style.json`, no key, Natural Earth data) as a STATED
   placeholder, and `AttributionFooter` takes its text as a required parameter so the placeholder's
   attribution is truthful. The plan's `© OpenStreetMap contributors · Protomaps` string arrives with the real
   basemap; P-ATTR-01's wording is pinned then, its VISIBILITY is pinned now.
3. Bundle identifier `com.phineasfritsch.scenicdrive` is a placeholder until App Store Connect names one.

### Layout (the plan's, subset)

```
apps/ios/Packages/ScenicApp/Package.swift        iOS 18.4; depends on the root package by path (../../..)
                                                 [corrected 2026-09-18 round 1: ../../../.., four levels]
  Sources/DesignSystem/                           tokens from the plan's table, both appearances; AttributionFooter
  Sources/MapAdapter/                             the ONLY importer of MapLibre; a UIViewRepresentable over MLNMapView
  Sources/FeatureScenicHome/                      one screen: map, footer, "Open in Apple Maps" -> Handoff
apps/ios/ScenicDrive/                             app shell: ScenicDriveApp.swift, Info.plist essentials
apps/ios/ScenicDrive.xcodeproj/project.pbxproj    THIN: Xcode 26 buildable folders (PBXFileSystemSynchronizedRootGroup),
                                                  one app target, local package reference, iOS 18.4, TARGETED_DEVICE_FAMILY=1
apps/ios/ScenicDrive.xcodeproj/xcshareddata/xcschemes/ScenicDrive.xcscheme
```

Feature targets import only DesignSystem, ScenicKit, Handoff and their own protocols. MapLibre is pinned to an
EXACT version whose tag is verified to exist (`gh api repos/maplibre/maplibre-gl-native-distribution/releases`).
The Skyline waypoints are REAL coordinates each verified against Nominatim, query and result recorded here;
≤ 9 of them (`AppleMapsDirections.maxWaypoints`), 5 decimals (`coordinateDecimals`).

### Folds T-0010, which stays in backlog until this merges

T-0010 (the thin xcodeproj shell) is the same tree; it moves to done/ when this task's PR merges, by the
reviewer, with a note pointing here. Both serial-only files it named are declared `exclusive:` above and
locked.

### Also in scope, because it becomes true the moment these files exist

T-0037: `ops/lib/check-line-cap` globs only `Sources/**/*.swift` and `Tests/**/*.swift`, so P-SRC-02 would
silently exempt every file this task adds. The globs gain `apps/ios/**/*.swift`; the population is stated.

### Acceptance shape

* root `swift build` on Linux never sees the package (root `Package.swift` references nothing under `apps/`);
* `bash ops/lib/check-line-cap` covers the new files - the count rises, every file ≤ 300, one type per file;
* `bash ops/check-pins --source-only` green; `bash ops/queue-check` green;
* a script proves the pbxproj's object graph is closed (every referenced ID is defined, every target has a
  build configuration list, the package product dependency names match the package's products);
* the MapLibre tag exists; every waypoint's Nominatim result is recorded;
* NOT COMPILED HERE, on the record. The Xcode Cloud build is T-0009's, and needs M0.

## Log
- 2026-09-18T01:40:00Z claimed by agent/claude-fable-5-1; worktree `.worktrees/T-0141`, branch `task/T-0141`, off
  `af88ac2` (PR #36 merged). `ops/new-task` allocated **T-9902 for the fifth time** ([[T-0138]]); renamed by hand.
  Authored by two opus agents on disjoint paths and verified by one fable agent before anything is committed -
  the fleet's model rule from this session.
- 2026-09-18T02:50:00Z **The hourly panel (grounded by a fable pass) found this task's own declaration wrong before
  a line of it was committed:** `exclusive: []` while writing `project.pbxproj` and a `Package.swift`, both
  serial-only in CLAUDE.md; `pins_affected` naming P-ATTR-01, a pin that does not exist in PINS.yaml;
  `acceptance: []` under a title claiming M1.5. Corrected: locks declared and acquired, P-ATTR-01 dropped
  (the attribution VISIBILITY pin belongs with the real basemap, when P-ATTR-01 is written), the Brief's
  prose acceptance moved into `acceptance:`, and T-0010 named as folded rather than duplicated. The panel's
  one-commit change - Info.plist asks for location and nothing uses it - is applied when the authors' tree is
  committed, not while they are writing it.
- 2026-09-18T15:45:37Z acquired lock(s) pbxproj, package-swift for agent/claude-fable-5-1
- 2026-09-18T03:20:00Z **Authored, verified, corrected, committed.** The two authors' own entries follow verbatim, then the fable verifier's note, then what was done about it.

  **Author A (package):**
  - 2026-09-18 Apple package authored (opus, half 1 of 2: `apps/ios/Packages/ScenicApp/**` only). 7 files, 585 lines,
    all LF, no BOM, largest 114 — cap 300. `grep -rn "^import MapLibre" apps/ios` returns exactly one hit,
    `MapAdapter/MapView.swift:2`. Root `Package.swift` untouched and still references nothing under `apps/`.
    NOT COMPILED HERE: no Apple toolchain, no Xcode. Xcode Cloud is the compiler; T-0009 is the proof.
  * MapLibre pinned `exact: "6.31.0"`. Verified, not recalled:
    `gh api repos/maplibre/maplibre-gl-native-distribution/releases --jq ".[0:5][].tag_name"` → 6.31.0 6.30.0
    6.29.0 6.28.0 6.27.0.
  * Route (loop: `source: nil` = current location, back to SF), 5 waypoints vs `maxWaypoints` 9, 5 decimals per
    `coordinateDecimals`, each a Nominatim result recorded beside it in `SkylineHandoff.swift`:
    SF rel 111968 37.7879363/-122.4075201 → 37.78794,-122.40752 · I-280 `Junipero Serra Freeway, San Mateo County`
    way 23995546 → 37.70526,-122.47165 · `Cañada Road, Woodside` way 276909112 → 37.44197,-122.26667 ·
    CA-92 `Half Moon Bay Road, San Mateo County` way 27672021 → 37.50745,-122.34299 · `Skyline Boulevard, Woodside`
    way 305925415 → 37.38776,-122.26638 · `Sky Londa` rel 9966012 → 37.37227,-122.26133.
    Two queries returned `[]` and nothing was written from them, incl. the task's own example
    `Skyline Boulevard Highway 92 California`. `Page Mill Road, Palo Alto` (way 385245835, 37.4193960/-122.1452121)
    verified but rejected: that is Page Mill's east end in the flats, off the ridge. Sky Londa taken instead.
  * **Deviation, deliberate:** `platforms: [.iOS("18.4")]`, not `.iOS(.v18)`. The claim that SPM expresses
    major.minor only is false — root `Package.swift:10` already declares `.iOS("18.4")` — and `.v18` would not
    resolve, since SPM requires a package's deployment target ≥ its path dependency's 18.4. Reasoning is in the
    manifest.
  * **Deviation, needs a ruling:** `FeatureScenicHome` depends on `MapAdapter`. CLAUDE.md's feature-import list
    excludes it; the task's deliverable requires `MapView` full-screen on that same screen. Flagged on the target.
  * Attribution is `© MapLibre · Natural Earth`, NOT the plan's OSM/Protomaps line: the demo tiles' TileJSON
    `attribution` is `" "` (empty) and the demotiles README says the polygons are Natural Earth. Crediting OSM and
    Protomaps here would pass a grep for the final wording over a basemap containing neither. P-ATTR-01's wording
    lands with the real PMTiles; `AttributionFooter(text:)` has no default so the credit cannot go stale silently.
  * No test targets: an XCTest bundle here could never be seen red, which CLAUDE.md counts as untested.

  **Author B (shell, pbxproj, line-cap):**
  - 2026-09-18 app-shell half (apps/ios/ScenicDrive/**, apps/ios/ScenicDrive.xcodeproj/**, ops/lib/check-line-cap).
    NOT COMPILED HERE, on the record: no Xcode and no Apple Swift on this box. Xcode Cloud (T-0009) is the first
    compiler this tree meets; what follows is text that parses, not a build.
    * ScenicDriveApp.swift (17) - @main App, single import FeatureScenicHome, body `ScenicHomeScreen()`; checked
      against the other agent's `public struct ScenicHomeScreen: View` / `public init() {}`. Shell imports no
      DesignSystem and no MapAdapter.
    * Info.plist (43) - CFBundleDisplayName "Scenic Drive", UILaunchScreen {}, NSLocationWhenInUseUsageDescription
      122 chars, UIBackgroundModes ABSENT. CFBundleIdentifier is $(PRODUCT_BUNDLE_IDENTIFIER); the placeholder
      literal com.phineasfritsch.scenicdrive sits once per build config in the pbxproj so the two cannot drift.
    * project.pbxproj (278) - objectVersion 77; 19 objects; one PBXProject, one PBXNativeTarget (application);
      PBXFileSystemSynchronizedRootGroup for ScenicDrive/ plus a BuildFileExceptionSet excluding Info.plist, or
      the buildable folder copies it as a resource and collides with INFOPLIST_FILE; XCLocalSwiftPackageReference
      relativePath = Packages/ScenicApp; XCSwiftPackageProductDependency productName = FeatureScenicHome. Object
      IDs are md5("ScenicDrive:"+label).hexdigest().upper()[:24], all 19 distinct - regenerate any one with
      python -c "import hashlib;print(hashlib.md5(b'ScenicDrive:target').hexdigest().upper()[:24])".
    * ScenicDrive.xcscheme (80) - shared; Xcode Cloud has no other entry point.
    * ops/lib/check-line-cap (66) - T-0037 closed: globs gain apps/ios/**/*.swift, message names every root.
      RED FIRST: a staged 301-line apps/ios/ScenicDrive/OverCap.swift -> "P-SRC-02: file(s) over the 300-line
      cap: apps/ios/ScenicDrive/OverCap.swift (301 lines)", exit 1, while the two old globs matched it 0 times.
      Deleted -> "P-SRC-02: 37 Swift files tracked (Sources=15, Tests=21, apps/ios=1), none over 300 lines",
      exit 0. apps/ios=1 is my half only; 7 further .swift existed unstaged, so the committed count is 44.
      Residual hole in the header: <root>/**/*.swift still misses a file directly at <root>/X.swift.
    * .artifacts/T-0141/pbxproj-graph.py (257, gitignored) - 29 assertions, 0 failed. RED FIRST too: it read
      TargetAttributes' nested `<id> = {` as an object definition and every target assertion came back None;
      fixed to accept definitions only at depth 0 of `objects = { }`. ops/check-pins/ops/test NOT run by me.

  **Verifier (fable, read-only):**
  - 2026-09-18 verifier pass over both halves (read-only, 14 tool uses, no compiler). Status: only apps/ios/** (A/A/A/A +
    untracked Packages/) and M ops/lib/check-line-cap (mode 100755 kept); root Package.swift diff empty; HEAD 54052cc, nothing committed.
  - Gates, run bare: `bash ops/lib/check-line-cap` -> "P-SRC-02: 37 Swift files tracked (Sources=15, Tests=21, apps/ios=1),
    none over 300 lines" exit 0; `bash ops/check-pins --source-only` -> "PINS ok=6 skipped=10 pending=1 expired=0 failed=0"
    exit 0 (P-SRC-02 ok; pending=1 is the pre-existing T-0012); `bash ops/queue-check` -> "QUEUE OK (132 tasks)" exit 0.
  - Names agree: products DesignSystem/MapAdapter/FeatureScenicHome vs pbxproj productName FeatureScenicHome, relativePath
    Packages/ScenicApp; shell imports FeatureScenicHome; ScenicHomeScreen is public with public init(); root package name
    "ScenicDrive" matches the by-path dependency; Coordinate/AppleMapsDirections signatures exist as called.
  - 8 new .swift files: one type each, max 114 lines, LF, no BOM. `import MapLibre` exactly once (MapAdapter/MapView.swift:2).
  - pbxproj: B's graph 29/0 failed; independent regex count 19 defined = 19 referenced, no dangling IDs, scheme -> target.
  - MapLibre: `gh api .../releases` re-run -> 6.31.0 first; Package.swift:43 exact "6.31.0". Nominatim re-queried (UA
    scenic-drive-T-0141-verify): Cañada Road way 276909112 and Sky Londa rel 9966012 match A's lat/lon to all 7 decimals.
  - AttributionFooter: init(text:) required, id "attribution.footer", accessibilityHidden(false) explicit.
  - NOT solid on one item: MapAdapter/MapView.swift:1 `import CoreLocation` (for CLLocationCoordinate2D at :45). The verify
    checklist forbids any CoreLocation import under apps/ios; A did not disclose it. Task file and CLAUDE.md never ban it
    in MapAdapter, so this is a reviewer ruling (record an exemption or drop the import), not a rewrite.
  - Nits: check-line-cap:17 comment "36 of 50" (real post-commit count 44); B's log says "T-0037 closed" but T-0037 is
    still in queue/claimed/; B's "7 files under Sources/" is 6 + Package.swift.

  **Rulings on the verifier's four problems.** (1) `import CoreLocation` in `MapAdapter/MapView.swift` is
  CORRECT and stays: `MLNMapView.setCenter` takes `CLLocationCoordinate2D`, MapAdapter is the Apple-only
  adapter the plan names as the sole MapLibre importer, and CLAUDE.md's CoreLocation ban is on the ROOT
  package, which is Linux-only. The verifier's check was my prompt's over-reach, not the plan's rule; Author A
  should still have listed the import as a deviation and did not. (2) `check-line-cap:17` "36 of 50" -> 36 of
  44, the real population after this commit. (3) Author B wrote "T-0037 closed"; it is ADDRESSED - its Log
  says so and it moves to done/ when this PR merges. (4) "7 .swift files under Sources/" was 6 plus
  `Package.swift`; the count of 8 under apps/ios is right.

  **Two deviations Author A flagged, ruled.** `.iOS("18.4")` (string form) is right and my prompt's
  `.iOS(.v18)` was wrong - the root package already uses the string form and a lower deployment target than
  the dependency would not resolve. `FeatureScenicHome` depending on `MapAdapter` contradicts CLAUDE.md's
  literal feature-target import list (DesignSystem, ScenicKit, PlaceStore, own protocols) while every screen
  in the plan renders the map: the list is incomplete, not the dependency wrong. Added to [[T-0147]]'s scope
  (reconcile CLAUDE.md's shape with the tree) rather than routed through a one-conformance protocol here.

  **The panel's one-commit change, applied:** `Info.plist` no longer asks for location. Nothing under
  `apps/ios/` uses it; the only `CLLocationCoordinate2D` is MapLibre bridging. The key returns with the
  first feature that reads the user's position, and the plan's `NSLocationWhenInUseUsageDescription >= 30
  chars` pin (P-PRIV-01) with it.

  **On the record: commit `1215d89` is not what its message says.** I committed the corrected task file with
  `git add queue/ && git commit`, and the index already held Author B's four files and the `check-line-cap`
  change, staged by B minutes earlier. The commit's message names only the queue edits; its diff carries
  B's half. It is pushed and stays - history is not rewritten here - and this entry is where the diff is
  described. Author A's half, untracked at that moment, lands with this commit.

- 2026-09-18T03:40:00Z A number I changed without measuring, put back on the measurement: I "corrected" the line-cap comment from 36 of 44 to 37 of 45 by adding one to a count I had not re-run; `bash ops/lib/check-line-cap` prints `44 Swift files tracked (Sources=15, Tests=21, apps/ios=8)`, so 36 before this task and 44 after was right the first time. Reverted. The pbxproj graph script asserts the location key ABSENT now (28 assertions, 0 failed).
- 2026-09-18 review round 1 by agent/rv1-pr88 (PR #88, head 32355c5, own worktree `.worktrees/rv1-pr88`, removed). **FAIL — one blocking defect: the Apple package cannot resolve.** `Packages/ScenicApp/Package.swift:37` declares `.package(name: "ScenicDrive", path: "../../..")`, but the manifest sits four components below the root, so the path lands on `<repo>/apps`, which has no `Package.swift`. Proven by the toolchain on this box (Swift 6.3.3 Windows; SPM resolution needs no Mac), each run under its own `--scratch-path`: `swift package dump-package` emits the dependency as `"identity": "apps", "path": "<repo>\apps"`, and `swift package resolve` -> `error: the package manifest at '<repo>\apps\Package.swift' cannot be accessed`, exit 1. Required: `"../../../.."`. The comment at :36 ("Three levels up"), the Brief's "(../../..)" and the PR body's "depends on the root package by path" all carry the same off-by-one. Nothing caught it: `pbxproj-graph.py` checks the xcodeproj's `relativePath` and the product names, never the manifest's own path dependency; the fable verifier checked the dependency's NAME; CI runs only `core` and `pins-source-only`, neither of which sees `apps/ios/`.
  Everything else measured green at 32355c5 and is not disputed: line-cap `44 Swift files tracked (Sources=15, Tests=21, apps/ios=8)` exit 0; `check-pins --source-only` `ok=6 skipped=10 pending=1 expired=0 failed=0` exit 0; `queue-check` `QUEUE OK (132 tasks)` exit 0; `pbxproj-graph.py` 28 assertions 0 failed; MapLibre 6.31.0 first in the releases list; three waypoints (not two) re-queried on Nominatim — ways 23995546, 305925415, 27672021 — agreeing to 7 decimals; the 280→Cañada→92→Skyline shape matches the plan's line 53; `import MapLibre` exactly once; no Apple framework import in the root package; no sentence anywhere claims this was compiled. The 301-line red was reproduced by name (`apps/ios/ScenicDrive/OverCap.swift (301 lines)`, exit 1), and four fresh mutations — objectVersion, product rename, `relativePath`, a dangled scheme blueprint — each went red by name. The Log's account of `1215d89` is true to `git show --stat`; the T-0037 "addressed, not closed" ruling and both `queue/LOCKS` entries are correct.
  Ten non-blocking findings recorded with the review, the recurring shape being a name or comment claiming more than the assertion under it: acceptance line 1 quotes `grep -c apps/ Package.swift -> 0` where it prints 1 (a comment satisfies it); `check-line-cap:24` still quotes 36 where the command now prints 44; `AttributionFooter.swift:55` cites an XCUITest that does not exist in a tree with no test targets; `AttributionFooter.swift:5` and `MapView.swift:38` cite P-ATTR-01, which `grep -c P-ATTR-01 pins/PINS.yaml` puts at 0 and which this task's own Log dropped for that reason; `MIN_FILES=5` lets a whole root reach zero green (`apps/ios=0`, exit 0); the graph script is gitignored and does not survive the merge; `FeatureScenicHome`'s `Handoff` dependency is a third unruled import deviation; CLAUDE.md's literal attribution string is now false in the tree with no task owning the reconciliation; the location assertion prints "present" on its passing line; and `DesignTokens.swift:27` says 3.6:1 where the formula gives 3.35:1. Nothing was changed anywhere; `.worktrees/T-0141` was read only (status empty, HEAD 32355c5) and every tree was left pristine and re-hashed against HEAD.
- 2026-09-18 round-1 fixes by agent/claude-opus-5, acting for owner agent/claude-fable-5-1 on the owner's
  rulings; the entry above is reviewer agent/rv1-pr88's own and is reproduced verbatim. Worktree
  `.worktrees/T-0141`, branch `task/T-0141`, from 32355c5. First act, because two rulings needed main:
  `git merge origin/main` (51 commits behind, merge-base af88ac2) -> merge commit 76f9e8e, **no conflicts**
  and no queue/ duplicate to resolve - this task's file exists only in `queue/claimed/`, and main's own moves
  (T-0107, T-0108, T-0126, T-0131, T-0139 into done/) came across untouched. Every finding was reproduced at
  this tree before it was touched. **Nothing was compiled**: the only Swift toolchain here is Windows
  6.3.3 and it was used for manifest loading and dependency resolution only.
  * **F1 (blocking), reproduced twice.** `python -c "import os;print(os.path.normpath(os.path.join('apps/ios/Packages/ScenicApp','../../..')))"`
    -> `apps`, and `ls apps/Package.swift` -> `No such file or directory`. With the toolchain, from
    `apps/ios/Packages/ScenicApp` under its own `--scratch-path`: `swift package dump-package` emitted
    `"identity": "apps"`, `"path": "...\.worktrees\T-0141\apps"`, and `swift package resolve` ->
    `error: the package manifest at 'C:\...\.worktrees\T-0141\apps\Package.swift' cannot be accessed
    (... doesn't exist in file system)`, exit 1. FIXED: `path: "../../../.."`, and the comment above it now
    says four levels and why. GREEN, same commands: dump-package emits the dependency at the checkout root
    with `nameForTargetDependencyResolutionOnly: ScenicDrive` (a one-liner over its JSON prints
    `root manifest at dependency path: True | name: ScenicDrive`; at `../../..` the same line prints
    `False ... identity: apps`), and `resolve` exits **0** - further than the ruling expected: it fetched
    maplibre-gl-native-distribution, computed 6.31.0 and downloaded `MapLibre.dynamic.xcframework.zip`.
    That is resolution, not a build. Two honest caveats: SPM derives a by-path dependency's *identity* from
    the directory name, so in this worktree it reads `t-0141` and in a clone it reads `scenic_drive` -
    `name: "ScenicDrive"` is what target dependencies resolve against, and it is unchanged; and `resolve`
    wrote an untracked `apps/ios/Packages/ScenicApp/Package.resolved`, which is serial-only in CLAUDE.md and
    NOT declared by this task, so it was deleted rather than committed. The Brief's spec line is corrected in
    place with a dated bracket rather than silently.
  * **F2, reproduced:** `grep -c apps/ Package.swift` -> 1 (Package.swift:4 is a comment). Acceptance line 1
    now runs `grep -cE '^ *[.]package[(].*apps/' Package.swift` -> 0, written without backslashes so the YAML
    is not escaping-dependent. Demonstrated to be a real detector, not a tautology: over a control file
    holding one genuine `.package(name: "ScenicApp", path: "apps/ios/Packages/ScenicApp"),` line plus a
    comment naming the same path, it prints 1 while the round-0 `grep -c apps/` prints 2. Recorded in the
    acceptance line because it bites: `grep -c` exits 1 when the count is 0, so the count is the
    assertion and the status is not.
  * **F3, reproduced and worse than reported:** at this commit `git ls-files '**/*.swift' | wc -l` -> 48 and
    `git ls-files 'Sources/**/*.swift' 'Tests/**/*.swift' | wc -l` -> 40, so the reviewer's 44/36 had already
    rotted again inside one merge. Both counts removed from the header (`check-line-cap:17` "covers 36 of 44"
    as well as :24's "the same 36 files"); the paragraph now says to compare `git ls-files '**/*.swift' | wc -l`
    with the total the script prints. A comment that carries no number cannot go stale.
  * **F4, reproduced:** `git ls-files | grep -ic xcuitest` -> 0, `git ls-files | grep -icE 'uitests?'` -> 0.
    `AttributionFooter.swift` now says the identifier is reserved, that this package has no test targets, and
    that the XCUITest arrives with the first green Xcode Cloud run.
  * **F5, reproduced:** `grep -c P-ATTR-01 pins/PINS.yaml` -> 0. Both citations now read as the plan's
    P-ATTR-01, not yet filed in PINS.yaml, and say that nothing mechanical enforces either file today. No pin
    was invented.
  * **F6, reproduced:** `git rm --cached $(git ls-files 'apps/ios/**/*.swift')` then `bash ops/lib/check-line-cap`
    -> `P-SRC-02: 40 Swift files tracked (Sources=17, Tests=23, apps/ios=0), none over 300 lines`, exit **0** -
    the T-0037 condition, green. FIXED with a per-root guard that refuses by the NAME of the empty root;
    MIN_FILES=5 kept, since it is what catches the whole population collapsing at once. RED, in this worktree
    with the index mutated the same way: `P-SRC-02: root(s) matching no tracked .swift file: apps/ios` /
    `Population: Sources=17, Tests=23, apps/ios=0 (total 40).`, exit 1. `git reset HEAD -- apps/ios` then GREEN:
    `P-SRC-02: 48 Swift files tracked (Sources=17, Tests=23, apps/ios=8), none over 300 lines`, exit 0.
  * **F7, done:** `.artifacts/T-0141/pbxproj-graph.py` -> `ops/lib/check-pbxproj-graph.py`, mode 100644 (every
    other `*.py` under `ops/` is 100644 and it is invoked as `python <path>`, so P-OPS-01's chmod rule for
    wrappers does not apply). 263 lines, under the cap, one concern, so no split. `ROOT` is unchanged and still
    correct: `ops/lib/../..` is the repo root exactly as `.artifacts/T-0141/../..` was. Acceptance line 6 names
    the new path. Run at this commit: `pbxproj-graph: 28 assertions, 0 failed`, exit 0.
  * **F8, ruled:** `FeatureScenicHome` -> `Handoff` is the same deviation as `MapAdapter` - CLAUDE.md's
    feature-target list is incomplete, not the dependency wrong. `Handoff` is a root-package product this
    screen genuinely needs ("Open in Apple Maps" is `AppleMapsDirections`), and routing it through a
    one-conformance protocol would be machinery with no second implementation. Named on the target in
    Package.swift and added to [[T-0147]]'s scope, where reconciling CLAUDE.md's shape with the tree lives.
  * **F9, ruled the same way and written down:** [[T-0147]] gains a line for the attribution WORDING
    (CLAUDE.md:48's literal `© OpenStreetMap contributors · Protomaps` vs `MapStyle.attributionText`'s
    `© MapLibre · Natural Earth`). The VISIBILITY invariant is not in question. T-0147 also gains `apps/ios/`
    in its `touches:`, and its round-0 `MapAdapter` ruling, which had been recorded in this Log as "added to
    T-0147's scope" while T-0147 existed only on main - so the line had never reached the file. Nothing closed.
  * **F10, reproduced:** on the green tree the passing line read
    `ok NSLocationWhenInUseUsageDescription is absent because nothing asks for location  present`. The detail is
    now computed, not hardcoded. GREEN prints `absent`; RED, with the key re-added to `apps/ios/ScenicDrive/Info.plist`:
    `FAIL NSLocationWhenInUseUsageDescription is absent because nothing asks for location  present`, exit 1.
    Info.plist restored with `git checkout --` and the tree re-hashed clean.
  * **F11, reproduced:** WCAG 2.x relative luminance of `#EA580C` is 0.244984 and of `#FFF7ED` is 0.938960, so
    (0.938960+0.05)/(0.244984+0.05) = **3.3526**, not 3.6. `DesignTokens.swift:27` now says 3.35:1 and shows the
    two luminances. The conclusion is unchanged: clears 3:1 for a 44 pt control, fails 4.5:1 for body copy.
  * **Acceptance block rewritten**, nine lines, every one re-run at this commit and quoting what it really
    printed - including `bash ops/check-pins --source-only` -> `PINS ok=8 skipped=11 pending=1 expired=0
    failed=0 tier=linux source-only` and `bash ops/queue-check` -> `QUEUE OK (140 tasks)` (both moved by the
    merge from ok=6/132; both run bare, never piped). `touches:` becomes
    `[apps/ios/, ops/lib/, pins/PINS.yaml, queue/]`: the hook matches by prefix, so the old
    `ops/lib/check-line-cap` entry could not admit `ops/lib/check-pbxproj-graph.py`. Widened rather than
    bypassed, and said here. `state: claimed` and `reviewer:` untouched.
  * **STILL OPEN, not fixed by this round.** (a) Nothing here was compiled and this PR still cannot prove it
    builds; the first Xcode Cloud run ([[T-0009]]) is the proof, and it needs the human's M0 steps.
    (b) `ops/test` and the full `ops/check-pins` were NOT run: `ops/test` shells `swift test` without a
    `--scratch-path` into the shared `.build`, which CLAUDE.md forbids on a shared box, and nothing in this
    round touches a Linux target. (c) check-line-cap's older residual hole stands, stated in its header: a file
    directly at `Sources/X.swift`, `Tests/X.swift` or `apps/ios/X.swift` is still uncounted, because git's
    `<root>/**` pathspec needs a directory component. (d) The [[T-0010]] and [[T-0037]] transitions to done/
    remain the merger's, not mine. (e) [[T-0147]] carries three reconciliations and is still `backlog`.
    (f) The PR body still describes the round-0 tree; rewriting it is the orchestrator's, and this Log is the
    record either way.

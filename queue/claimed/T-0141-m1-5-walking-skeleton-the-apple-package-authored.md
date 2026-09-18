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
touches: [apps/ios/, ops/lib/check-line-cap, pins/PINS.yaml]
pins_affected: [P-SRC-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "root Package.swift references nothing under apps/: git diff --stat main -- Package.swift is empty and grep -c apps/ Package.swift -> 0"
  - "bash ops/lib/check-line-cap -> the tracked .swift count includes apps/ios/**, every file <= 300 lines; the exact count is printed and recorded here when the tree is committed"
  - "one type per file under apps/ios/: a grep of '^(public )?(struct|enum|class|final class|actor) ' counts <= 1 per file"
  - "bash ops/check-pins --source-only -> PINS ok=N ... failed=0, exit 0; bash ops/queue-check -> QUEUE OK, exit 0"
  - "python .artifacts/T-0141/pbxproj-graph.py (quoted in the Log) -> every referenced 24-hex object id is defined; the target has a two-configuration list; the package product dependency names a product Packages/ScenicApp/Package.swift declares"
  - "the MapLibre tag pinned in Package.swift is listed by gh api repos/maplibre/maplibre-gl-native-distribution/releases (command and output in the Log)"
  - "every SkylineHandoff waypoint has its Nominatim query and returned lat/lon in the Log, and two are re-checked by the reviewer to 3 decimals"
  - "NOT COMPILED HERE, on the record: no Apple toolchain exists on this box. The Xcode Cloud build is T-0009's proof and needs the human's M0 steps. This task's exit is a tree Xcode Cloud can build, not a build."
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

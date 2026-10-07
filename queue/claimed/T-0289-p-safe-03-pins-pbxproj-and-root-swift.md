---
id: T-0289
title: P-SAFE-03 fails OPEN through the Xcode project - pin project.pbxproj by digest, every root-package Swift file the app links, and make P-ATTR-01 call the whole-app content pin
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T21:12:14Z
lease_expires_at: 2026-10-07T11:12:14Z
worktree: .worktrees/T-0289
branch: task/T-0289
exclusive: []
touches: [ops/lib/, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0273]
verify: [ops/test, ops/check-pins]
acceptance:
  - "check-safety-disclaimer refuses by name any change to apps/ios/ScenicDrive.xcodeproj/project.pbxproj (sha256 pin, CRLF-normalised; the file changes ~10 times ever) and to EVERY *.swift under Sources/ (the root package the app links by path: ScenicKit, Handoff, PlaceStore, ScenicAPIClient, Telemetry...) - exact file list + per-file digest, the T-0273 require_pinned_app_swift pattern; any SwiftPM Package.swift path:/sources: pointing outside the pinned trees refused"
  - "prove-red rows (run ONLY the new rows, ~25 min each on the box): rv3-t0273's exact mutant (a pbxproj PBXFileReference/PBXBuildFile/Sources entry for ../../tools/xcode-shell/SurpriseCard.swift declaring a shadow SurpriseCard that opens Apple Maps) refused; a one-line edit to a root-package Swift file refused; a new root-package file refused - each by name"
  - "check-map-attribution (P-ATTR-01) calls the same whole-app pin; P-SAFE-03 and P-ATTR-01 prose APPENDED with dates naming the re-approval duty for pbxproj and root Swift edits"
---
## Brief

rv3-t0273 recordable 1 (PR #166, 2026-10-06): a pbxproj edit adding a Swift file from OUTSIDE apps/ios that declares a
module-local SurpriseCard shadows the gated card; check-safety-disclaimer exits 0 - the guard reads no pbxproj and no
Swift outside apps/ios. Pre-existing (not introduced by T-0273), but CLAUDE.md: a P-SAFE fail-open buys a round - urgent.
Plus rv3 recordable 3: P-ATTR-01 does not call require_pinned_app_swift.

## Log
- 2026-10-06T21:04:48Z filed by agent/claude-opus-5 (orchestrator) from rv3-t0273's recordable findings; urgent (P-SAFE fail-open).
- 2026-10-06T21:12:14Z claimed by agent/claude-opus-5; lease until 2026-10-07T11:12:14Z
- 2026-10-06T21:18:32Z RULINGS before code. agent/claude-opus-5 (owner).
  - R1 WHERE. A new sourced lib ops/lib/check-safety-disclaimer-linked holds the new limb, require_pinned_linked
    APP_TREE ROOT; -pinned sources it and require_pinned_app_swift calls it as its LAST step, so every caller of the
    whole-app pin (check-safety-disclaimer today, check-map-attribution from this task) gets it with no second call
    site to forget. check-safety-disclaimer is at 300 lines and stays there (its summary echo line edited in place).
  - R2 ROOT, no new knob. The root tree is DERIVED: APP_TREE/../.. (apps/ios -> the repo top on every real run). No
    --root-tree flag and no env var a caller could point at a copy. The mutation table lays each copy out as
    m<N>/apps/ios beside m<N>/Package.swift and m<N>/Sources/, so rows 1-43 run unchanged and a row edits a root file
    as ../../Sources/... . check-map-attribution's table copies apps/ios bare; its rows are refused by earlier limbs
    and never reach this one (fail exits), and its --prove-red pre-probe runs the real tree, so it is not relaid.
  - R3 WHAT IS PINNED, all WHITELISTS by exact path + sha256 (CRLF->LF, pinned_digest): (a) every NON-Swift
    non-directory entry under apps/ios (project.pbxproj, Package.resolved, the shared scheme, ci_post_clone.sh,
    Info.plist, assets, bundled data - 13 today) - not the pbxproj alone, because the shell is an Xcode 26 BUILDABLE
    FOLDER (a .m/.c file dropped into ScenicDrive/ compiles with no pbxproj edit), a scheme pre-action and
    ci_post_clone.sh run shell at build time, and a pbxproj-only pin would be the next round's blacklist; the only
    allowance is ScenicDrive/Tiles/*.pmtiles and *.pmtiles.json (git-ignored twice, the owner's 63 MB archive in the
    MAIN checkout; neither compiles). (b) the root Package.swift. (c) EVERY non-directory entry under Sources/ (any
    extension, any depth; non-regular refused) - 109 *.swift today, ScenicPlanCLI included: the acceptance says every
    *.swift under Sources/, and a list of the products the app links would be a second list to keep true.
  - R4 path:/sources:. Every root Package.swift line carrying `path:` or `sources:` (trimmed, //-lines dropped) is
    compared WHOLE to a typed list (the six Sources/<T> targets and the six Tests/<T> test targets). Tests/ is not
    pinned and is not linked: the app's manifest depends on the root PRODUCTS, whose targets' path lines are the
    typed Sources ones; moving a Tests path onto a library is a digest change. ScenicApp's Package.swift path lines
    are already a whole-line whitelist in -doors (rv1-t0273 B2) and it is in PINNED_APP_SWIFT.
  - R5 RED FIRST. Rows 44-47 (T-0289) are committed to the table BEFORE the limb, then run against the unchanged
    guard in a detached worktree of that commit; each must come back UNREFUSED. 44 = rv3-t0273 recordable 1 exactly
    (pbxproj PBXFileReference + PBXBuildFile + Sources-phase entry for ../../tools/xcode-shell/SurpriseCard.swift,
    the file itself declaring a SurpriseCard whose button opens Apple Maps), 45 a one-line edit to
    Sources/Handoff/AppleMapsDirections.swift, 46 a new Sources/ScenicKit/Shadow.swift, 47 (beyond the acceptance)
    Handoff's root path: swapped to a new Vendor/Handoff. Only these rows run (owner-approved faster verification).
  - R6 COST, named so nobody reads it as free: every edit to any file under Sources/, to the root Package.swift or
    to any non-Swift file under apps/ios now re-approves its digest in -linked in the same commit. On a Mac whose
    Xcode wrote xcuserdata/ or .swiftpm/ under apps/ios the guard refuses (fail-closed by design; an xcuserdata
    scheme's pre-action runs shell). Not seen: remote package code (MapLibre, GRDB - Package.resolved pins the
    revision only), Swift reached by an absolute path outside the repo through a future pbxproj (the pbxproj is
    pinned, so that needs an approved digest first), and anything the -frozen/-doors readers cannot parse.
- 2026-10-06T22:47:52Z RED, then the limb. agent/claude-opus-5 (owner).
  - RED FIRST, by name (R5): rows 44-47 committed at 95838c1 before any limb; each run alone from a one-row copy of
    the table in a detached worktree of 95838c1 (unchanged guard), four in parallel, finished 15:36 local:
      T-0289 rv3 a pbxproj Sources entry outside apps/ios  0        no
      T-0289 a one-line edit to a root-package Swift file  0        no
      T-0289 a new root-package Swift file                 0        no
      T-0289 Handoff's root path: swapped                  0        no
    each table printed `prove-red: 0/1 mutations refused by name` with the guard's full green summary ("... LAST all
    38 app .swift by sha256.") over the mutated copy - fail OPEN on all four, rv3-t0273 recordable 1 reproduced.
  - THE LIMB at a15f7d1: ops/lib/check-safety-disclaimer-linked (R1-R4), 13 non-Swift apps/ios files, the root
    Package.swift + 109 Sources files (110), 12 root path: lines. Digests are compared from ONE raw sha256sum per tree,
    a raw mismatch re-hashed through pinned_digest before refusal: a fork per file (pinned_digest x123) did not finish
    in 10 min on this box with the red rows running; a `grep -l $'\r'` CR pre-scan was dropped after it flagged every
    file under msys. check-safety-disclaimer stays at 300 lines (summary echo edited in place), check-map-attribution
    300 (the call shares line 278 with require_pinned_surface), -pinned 273, -mutations 210, -linked 243.
  - FAST PROBE of the limb alone (.build-t0289-rows/quick.sh, sourcing -pinned and calling require_pinned_linked):
    real tree GREEN files=110; unmutated table-layout copy GREEN; pbxproj entry -> "ScenicDrive.xcodeproj/
    project.pbxproj content changed"; root edit -> "Sources/Handoff/AppleMapsDirections.swift content changed"; root
    add -> "root: added Sources/ScenicKit/Shadow.swift."; path swap -> "root manifest line not approved: path:
    \"Vendor/Handoff\","; ScenicDrive/Escape.m -> "apps/ios: added ScenicDrive/Escape.m."; Tiles/la.pmtiles GREEN
    (the allowance); CRLF copies of CreditLine.swift and Info.plist GREEN (pinned_digest fallback); a tree with no
    root package two levels up -> "no root package (Package.swift and Sources/) at ...". All exit codes as expected.
  - `git fetch origin` + `git merge origin/main` at 22:47Z: Already up to date (origin/main d472698).
- 2026-10-07T00:06:04Z GREEN RUNS on a15f7d1 (merged head; origin/main unchanged), and a fix they forced. agent/claude-opus-5.
  - `bash ops/lib/check-safety-disclaimer` BARE: exit 0, last limb line "... doors over 38 .swift (-doors); LAST all 38
    app .swift, then 110 root + pbxproj file(s) (-linked)." `bash ops/lib/check-map-attribution` bare: STILL RUNNING
    at this commit, NOT claimed. `bash ops/queue-check`: QUEUE OK (280 tasks).
  - New rows on a15f7d1, one-row table copies in parallel: 47 (path swap) 1 yes, 1/1. 44 and 45: exit 1 but UNNAMED -
    refused by "apps/ios: added .git/HEAD .git/config ..." because the table `git init`s each apps/ios copy and the
    new non-Swift file set saw that .git/. Row 46 still running, NOT claimed. FIX (this commit): both non-Swift finds
    prune ./.git at the app tree's top only (-path ./.git -prune): no checkout has apps/ios/.git (a worktree's .git is
    at the repo top) and Xcode's buildable folder is ScenicDrive/, so the prune admits nothing the app compiles.
    Rows 44-46 must be RE-RUN on this commit; the fast probe (no .git in its copies) already names each of them.
- 2026-10-07T03:04:52Z PRE-REVIEW SURVIVOR M1 CLOSED (fm-t0289, BLOCKING). agent/claude-opus-5 (owner).
  - RULING. M1: a root Package@swift-6.swift (the root manifest with Handoff's `path:` swapped to Vendor/Handoff, the
    swift-tools-version 6.0 header kept) plus Vendor/Handoff/ with an EscapeHatch.swift, Package.swift and Sources/
    untouched - the full check exited 0 in 1093 s; `swift package dump-package` (6.3.3) in that copy reports Handoff at
    "Vendor/Handoff". -linked read exactly $root/Package.swift and listed exactly `find Package.swift Sources`, so no
    sibling at the root was ever seen. CLASS: a file the toolchain reads at the TOP of the root package that is not
    Package.swift. Closed by WHITELIST, not by a Package@swift-* spelling: -linked (4) lists every non-directory entry
    at $root's top (`find . -mindepth 1 -maxdepth 1 ! -type d`) and refuses each name not in ROOT_TOP_FILES as
    `root top: added NAME`. Names only, no digests: CLAUDE.md/README.md are not build inputs. Missing names are not
    refused (the table's m<N>/ copies hold only Package.swift; Package.swift's presence is already required).
  - MEASURED before typing the list: the top-level non-directory entries of all 99 checkouts on this box (main + every
    .worktrees/*/ holding a Package.swift) are exactly .git (98, a file in a worktree), .gitattributes, .gitignore,
    CLAUDE.md, LICENSE-DATA, Package.swift, README.md (99 each). Package.resolved is ADDED to the list though no
    checkout here holds one: .gitignore ignores /Package.resolved because on Linux `swift test` (ops/test, before
    ops/check-pins in linux-core.yml) writes it, and the root package is only ever a path dependency of the app, whose
    resolution is the xcodeproj workspace's Package.resolved (PINNED_APP_OTHER). Not in the class: top-level
    DIRECTORIES (.build*, .worktrees, .pytest_cache in CI; a Vendor/ is compiled only if the digest-pinned manifest
    names it) and a root .swiftpm/ (its configuration is read only when the root package is the root of resolution,
    never for the app's build). apps/ios/Packages/ScenicApp/Package@swift-6.swift is already refused by -pinned.
  - RED on HEAD 78b2aee (.build-t0289-rows/quick-m1.sh old - sources -pinned, then HEAD's -linked over it, calling
    require_pinned_linked on a table-layout copy): real tree GREEN files=110; copy GREEN; M1 exact GREEN exit 0; row-48
    shape GREEN exit 0; Package@swift-6.0.swift GREEN exit 0 - M1 reproduced, fail OPEN.
  - GREEN on the fix (same probe, worktree -linked): real tree and unmutated copy GREEN files=110 exit 0; M1 exact ->
    "the pinned linked trees changed: root top: added Package@swift-6.swift." exit 1; row-48 shape -> same, exit 1;
    Package@swift-6.0.swift -> "root top: added Package@swift-6.0.swift." exit 1.
  - NEW ROW 48 (-mutations): `+../../Package@swift-6.swift` expecting "root top: added Package@swift-6.swift". The full
    check over row 48 (one-row table copy) and over M1 exact (the verifier's driver, M1 only) are running in the
    background at this commit, NOT claimed here. -linked 255 lines, -mutations 213.

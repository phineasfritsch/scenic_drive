// swift-tools-version: 6.0
//
// APPLE-ONLY PACKAGE. This manifest is a SERIAL-ONLY resource for the agent fleet (CLAUDE.md).
//
// It is deliberately NOT referenced by the root `Package.swift`: the root package is Linux-only and
// `swift build` on Linux must never see SwiftUI, UIKit or MapLibre. The arrow points one way only -
// this package depends on the root package by path, never the reverse.
//
// NOT COMPILED HERE. There is no Swift compiler for Apple targets and no Xcode on the authoring box.
// Xcode Cloud is the compiler; the first `device/*` push (T-0009) is the proof this builds. Anything
// in this tree that claims to have been compiled is claiming something that did not happen.
import PackageDescription

let package = Package(
    name: "ScenicApp",
    // 18.4, NOT `.iOS(.v18)`.
    //
    // The task text said to write `.iOS(.v18)` on the grounds that SPM expresses major.minor only.
    // That is false twice over, and the root manifest in this same repository is the counterexample:
    // it already declares `.iOS("18.4")`, because `SupportedPlatform.iOS(_ versionString: String)`
    // exists precisely so a manifest can name a patch-level deployment target.
    //
    // It also would not have resolved. SPM requires a package's deployment target to be at least that
    // of every package it depends on, and this package depends on the root by path. Declaring 18.0
    // here against a root that requires 18.4 is the error "ScenicApp ... 18.0 ... depends on
    // ScenicDrive ... 18.4", i.e. a package that cannot resolve at all - a real break traded for a
    // comment stating something untrue. So: 18.4, matching the root and the plan.
    platforms: [.iOS("18.4")],
    products: [
        .library(name: "DesignSystem", targets: ["DesignSystem"]),
        .library(name: "MapAdapter", targets: ["MapAdapter"]),
        // Entitlements rides in the product the app already links (T-0271): the shell gets the paywall and Settings
        // with no project.pbxproj edit. It is a target of this PRODUCT, not a dependency of the FeatureScenicHome
        // TARGET - the home never imports it; the shell composes the two.
        // FeatureSurpriseMe rides the same product (T-0273): the shell composes the Surprise card into the home's slot.
        // FeaturePlanSheet and PlanAdapter ride it too (T-0294 R1): the shell composes the plan sheet over the home
        // and hands it the live planner, still with no project.pbxproj edit.
        .library(name: "FeatureScenicHome", targets: ["FeatureScenicHome", "Entitlements", "FeatureSurpriseMe", "FeaturePlanSheet", "PlanAdapter"]),
    ],
    dependencies: [
        // The root package: ScenicKit (Coordinate and the scoring core) and Handoff
        // (AppleMapsDirections). Four levels up from apps/ios/Packages/ScenicApp: the manifest's
        // own directory is four components below the repo root, so three dots-dots land on
        // <repo>/apps, which has no Package.swift and makes `swift package resolve` exit 1.
        .package(name: "ScenicDrive", path: "../../../.."),
        // EXACT, not `from:` and not a range. The tag was verified to exist before it was written:
        //   gh api repos/maplibre/maplibre-gl-native-distribution/releases --jq ".[0:5][].tag_name"
        //   -> 6.31.0  6.30.0  6.29.0  6.28.0  6.27.0
        // A binary map renderer that floats to a new minor between a TestFlight build and the next
        // one is a style that renders differently on the phone than it did on the box that shipped it.
        .package(url: "https://github.com/maplibre/maplibre-gl-native-distribution", exact: "6.31.0"),
    ],
    targets: [
        // Tokens and the shared chrome. No dependencies at all, on purpose: everything may import
        // DesignSystem, so DesignSystem importing anything would make that edge bidirectional.
        .target(
            name: "DesignSystem",
            path: "Sources/DesignSystem",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // THE ONLY IMPORTER OF MapLibre IN THE WHOLE TREE (CLAUDE.md). Its dependency list is one
        // entry and stays one entry; if a second package appears here the invariant is gone. It does
        // not depend on ScenicKit either, so it speaks in Doubles and bridges to
        // CLLocationCoordinate2D at its own boundary rather than teaching ScenicKit about CoreLocation.
        .target(
            name: "MapAdapter",
            dependencies: [
                .product(name: "MapLibre", package: "maplibre-gl-native-distribution"),
            ],
            path: "Sources/MapAdapter",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The one screen of the walking skeleton.
        //
        // DEVIATION ON THE RECORD, for the reviewer to rule on: CLAUDE.md says feature targets import
        // only DesignSystem, ScenicKit, PlaceStore and their own protocols, and MapAdapter is not on
        // that list. The task's own "not negotiable" rules repeat the list and then its deliverable
        // section requires `FeatureScenicHome` to render `MapAdapter.MapView` full-screen; those two
        // cannot both hold. Taken literally the screen would need a protocol it owns plus a generic
        // parameter, which is machinery the skeleton has no second implementation for. The direct
        // dependency is what is written, and it is flagged here rather than quietly taken.
        // `Handoff` below is the SAME deviation and was missed at round 0: it is a root-package product
        // and is not on CLAUDE.md's feature-import list either. Ruled the same way - the list is
        // incomplete, not the dependency wrong - and both are written into [[T-0147]]'s scope, which
        // owns reconciling CLAUDE.md's shape with the tree.
        .target(
            name: "FeatureScenicHome",
            dependencies: [
                "DesignSystem",
                "MapAdapter",
                .product(name: "ScenicKit", package: "ScenicDrive"),
                .product(name: "Handoff", package: "ScenicDrive"),
            ],
            path: "Sources/FeatureScenicHome",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The paywall, Settings and Legal & Attribution (T-0271, plan M6). StoreKit and SwiftUI are system frameworks;
        // DesignSystem is its only package dependency, and no feature target may depend on it
        // (ops/lib/check-store-links.py refuses `import Entitlements` anywhere but the app shell).
        .target(
            name: "Entitlements",
            dependencies: ["DesignSystem"],
            path: "Sources/Entitlements",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The Surprise card (T-0273): the bundled corpus through PlaceStore, Surprise.pick over an offline reach. A
        // feature target - DesignSystem, ScenicKit and PlaceStore only; it never imports FeatureScenicHome and never
        // opens a URL: Apple Maps is the home's gated opener, handed in by the shell (P-SAFE-03).
        .target(
            name: "FeatureSurpriseMe",
            dependencies: [
                "DesignSystem",
                .product(name: "ScenicKit", package: "ScenicDrive"),
                .product(name: "PlaceStore", package: "ScenicDrive"),
            ],
            path: "Sources/FeatureSurpriseMe",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The plan sheet (T-0294): search, extra minutes, Plan, the preview and the failure copy. A feature target -
        // DesignSystem, ScenicKit and PlaceStore only; it plans through ScenicKit's RoutePlanning and never imports
        // ScenicAPIClient, PlanAdapter or another feature.
        .target(
            name: "FeaturePlanSheet",
            dependencies: [
                "DesignSystem",
                .product(name: "ScenicKit", package: "ScenicDrive"),
                .product(name: "PlaceStore", package: "ScenicDrive"),
            ],
            path: "Sources/FeaturePlanSheet",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // THE ONLY IMPORTER OF ScenicAPIClient UNDER apps/ios (T-0294 R1), as MapAdapter is of MapLibre: it builds
        // the live planner the shell hands the plan sheet.
        .target(
            name: "PlanAdapter",
            dependencies: [
                .product(name: "ScenicKit", package: "ScenicDrive"),
                .product(name: "ScenicAPIClient", package: "ScenicDrive"),
            ],
            path: "Sources/PlanAdapter",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // NO TEST TARGETS HERE, deliberately and temporarily.
        //
        // Every test in this package is an XCTest/Swift Testing bundle that needs an Apple toolchain
        // and a simulator to run. Neither exists on the authoring box, so a test target added now
        // would be a suite nobody has ever seen go red - which CLAUDE.md counts as untested. They
        // arrive with the first green Xcode Cloud run, where they can actually fail.
    ]
)

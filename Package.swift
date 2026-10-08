// swift-tools-version: 6.0
//
// ROOT PACKAGE — Linux-only targets. Nothing here may import CoreLocation, MapKit, UIKit,
// SwiftUI, MapLibre or Ferrostar. Apple-only code lives in apps/ios/Packages/ScenicApp.
// This file is a SERIAL-ONLY resource for the agent fleet (see CLAUDE.md).
import PackageDescription

// GRDB, for PlaceStore - on every host EXCEPT Windows (T-0175 R2). The Windows dev toolchain ships no
// sqlite3.h/.lib, and SwiftPM there cannot even CHECK OUT GRDB (its tree holds symlinks; measured: "unable to
// create symlink Tests/CustomSQLite/GRDB: Permission denied"), which a `.when(platforms:)` condition does not
// prevent - SwiftPM fetches every declared package. So on Windows the package is not declared at all, every
// PlaceStore file is `#if canImport(GRDB)`, and PlaceStoreTests prints one XCTSkip saying why. Linux CI
// (linux-core installs libsqlite3-dev) and Apple hosts build and run it. Pinned EXACT: the device's corpus
// reader is not a place for a minor bump to arrive unannounced; 7.11.1's manifest is swift-tools 6.1.
#if os(Windows)
let grdbPackage: [Package.Dependency] = []
let grdbProduct: [Target.Dependency] = []
#else
let grdbPackage: [Package.Dependency] = [.package(url: "https://github.com/groue/GRDB.swift.git", exact: "7.11.1")]
let grdbProduct: [Target.Dependency] = [.product(name: "GRDB", package: "GRDB.swift")]
#endif

let package = Package(
    name: "ScenicDrive",
    platforms: [.iOS("18.4"), .macOS(.v14)],
    products: [
        .library(name: "ScenicKit", targets: ["ScenicKit"]),
        .library(name: "Handoff", targets: ["Handoff"]),
        // `ops/plan <O> <D> <B>`, the plan's M3 exit. An executable so that the CLI half is the SAME
        // bisection and the SAME scoring the app runs (T-0182, ruling R1): a python re-implementation
        // would be a second bisection, and the one that would drift is the one holding the ceiling.
        .executable(name: "scenic-plan", targets: ["ScenicPlanCLI"]),
        .library(name: "PlaceStore", targets: ["PlaceStore"]),
        .library(name: "ScenicAPIClient", targets: ["ScenicAPIClient"]),
        .library(name: "Telemetry", targets: ["Telemetry"]),
    ],
    dependencies: grdbPackage,
    targets: [
        .target(
            name: "ScenicKit",
            path: "Sources/ScenicKit",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        .testTarget(
            name: "ScenicKitTests",
            dependencies: ["ScenicKit"],
            path: "Tests/ScenicKitTests",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // Handoff depends on ScenicKit for Coordinate ONLY. It must never gain a dependency in the other
        // direction: ScenicKit is the scoring and routing core and has no business knowing that a URL to a
        // third-party maps app exists.
        .target(
            name: "Handoff",
            dependencies: ["ScenicKit"],
            path: "Sources/Handoff",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The CLI. Linux-only like everything else here: Foundation, FoundationNetworking behind a
        // `canImport` for URLSession's Linux home, ScenicKit for the engine and Handoff for the URL.
        // It holds no routing logic of its own - argument parsing, one HTTP transport, and printing.
        .executableTarget(
            name: "ScenicPlanCLI",
            dependencies: ["ScenicKit", "Handoff"],
            path: "Sources/ScenicPlanCLI",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The CLI's own tests. They exist because T-0182's pre-review pass found that the one line in this
        // tool that converts the minutes a user types into the seconds the ceiling is computed from could
        // be changed to `* 3600` - a 25-HOUR ceiling - with all 315 tests green: no test target named
        // ScenicPlanCLI, so nothing could bind to it. A test target on an EXECUTABLE target is legal from
        // SwiftPM 5.5 and is the smaller of the two fixes; the other was moving the CLI's types into a
        // library, which would have made the tested symbol a different symbol from the shipped one.
        .testTarget(
            name: "ScenicPlanCLITests",
            dependencies: ["ScenicPlanCLI", "ScenicKit", "Handoff"],
            path: "Tests/ScenicPlanCLITests",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        .testTarget(
            name: "HandoffTests",
            dependencies: ["Handoff", "ScenicKit"],
            path: "Tests/HandoffTests",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The device's reader for corpus.sqlite, on GRDB over the SYSTEM sqlite (see grdbPackage above).
        .target(
            name: "PlaceStore",
            dependencies: grdbProduct,
            path: "Sources/PlaceStore",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        .testTarget(
            name: "PlaceStoreTests",
            dependencies: ["PlaceStore"] + grdbProduct,
            path: "Tests/PlaceStoreTests",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The app's client for the Worker's POST /plan (T-0251). Foundation + URLSession (FoundationNetworking
        // behind `canImport` on Linux) and ScenicKit for Coordinate - nothing else. It sends ONE coordinate at
        // 2 dp and refuses anything else on the device; every Worker failure arrives as a PlanError. PlaceStore for the
        // corpus download's CorpusFetcher seam (T-0305 R2): URLSessionCorpusFetcher lives beside the plan transport.
        .target(
            name: "ScenicAPIClient",
            dependencies: ["ScenicKit", "PlaceStore"],
            path: "Sources/ScenicAPIClient",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        .testTarget(
            name: "ScenicAPIClientTests",
            dependencies: ["ScenicAPIClient", "ScenicKit", "PlaceStore"],
            path: "Tests/ScenicAPIClientTests",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // The plan's closed enum of fourteen telemetry events (T-0265). Foundation only, and no dependency on
        // ScenicKit: it never sees a Coordinate, only the H3 resolution-5 cell its own port of uber/h3 makes.
        .target(
            name: "Telemetry",
            path: "Sources/Telemetry",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        // Fixtures/ holds uber/h3's own rand05centers.txt, read from source by path (T-0265 R5), not a resource.
        .testTarget(
            name: "TelemetryTests",
            dependencies: ["Telemetry"],
            path: "Tests/TelemetryTests",
            exclude: ["Fixtures"],
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
    ]
)

// swift-tools-version: 6.0
//
// ROOT PACKAGE — Linux-only targets. Nothing here may import CoreLocation, MapKit, UIKit,
// SwiftUI, MapLibre or Ferrostar. Apple-only code lives in apps/ios/Packages/ScenicApp.
// This file is a SERIAL-ONLY resource for the agent fleet (see CLAUDE.md).
import PackageDescription

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
    ],
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
        .testTarget(
            name: "HandoffTests",
            dependencies: ["Handoff", "ScenicKit"],
            path: "Tests/HandoffTests",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
    ]
)

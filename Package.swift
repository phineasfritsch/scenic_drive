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
        .testTarget(
            name: "HandoffTests",
            dependencies: ["Handoff", "ScenicKit"],
            path: "Tests/HandoffTests",
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
    ]
)

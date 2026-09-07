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
    ]
)

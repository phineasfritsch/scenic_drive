import Entitlements
import FeatureScenicHome
import SwiftUI

/// The app shell. It owns the scene and composes the features; it draws nothing of its own.
///
/// The shell links exactly one package product, `FeatureScenicHome`, whose target list also carries `Entitlements`
/// (T-0271): the app gets the paywall and Settings with no project.pbxproj edit. It imports those two modules and
/// nothing else - not `MapAdapter` (MapLibre's only importer, reached through `FeatureScenicHome`), not
/// `DesignSystem`, nothing from the root Linux package: a shell that reaches past its features is how the layering
/// in CLAUDE.md dies quietly. The home never imports Entitlements; it hands the shell a settings action, and the
/// shell presents Settings, which opens the paywall. `LaunchScreen.atLaunch` is home in every release build.
@main
struct ScenicDriveApp: App {
    @State private var isShowingSettings = LaunchScreen.atLaunch != .home

    var body: some Scene {
        WindowGroup {
            ScenicHomeScreen(onSettings: { isShowingSettings = true })
                .sheet(isPresented: $isShowingSettings) {
                    SettingsScreen(opensPaywall: LaunchScreen.atLaunch == .paywall, onDone: { isShowingSettings = false })
                }
        }
    }
}

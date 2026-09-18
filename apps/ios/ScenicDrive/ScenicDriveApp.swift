import FeatureScenicHome
import SwiftUI

/// The app shell. It owns the scene and nothing else.
///
/// The shell imports exactly one package product, `FeatureScenicHome`. It does not import
/// `MapAdapter` (MapLibre's only importer, reached through `FeatureScenicHome`), `DesignSystem`
/// or anything from the root Linux package: a shell that reaches past its feature is how the
/// layering in CLAUDE.md dies quietly.
@main
struct ScenicDriveApp: App {
    var body: some Scene {
        WindowGroup {
            ScenicHomeScreen()
        }
    }
}

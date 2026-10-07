import Entitlements
import FeaturePlanSheet
import FeatureScenicHome
import FeatureSurpriseMe
import PlanAdapter
import SwiftUI

/// The app shell. It owns the scene and composes the features; it draws nothing of its own.
///
/// The shell links exactly one package product, `FeatureScenicHome`, whose target list also carries `Entitlements`
/// (T-0271), FeatureSurpriseMe (T-0273), and FeaturePlanSheet with PlanAdapter (T-0294): no project.pbxproj edit.
/// It imports those modules and
/// nothing else - not `MapAdapter` (MapLibre's only importer, reached through `FeatureScenicHome`), not
/// `DesignSystem`, nothing from the root Linux package: a shell that reaches past its features is how the layering
/// in CLAUDE.md dies quietly. The home never imports Entitlements; it hands the shell a settings action, and the
/// shell presents Settings, which opens the paywall. `LaunchScreen.atLaunch` is home in every release build.
///
/// T-0305: `init()` runs PlanAdapter's `LiveCorpus.launch` before any body, so a verified corpus download is activated
/// before the Surprise card or the plan sheet opens a PlaceStore; the places download sheet is presented full height.
@main
struct ScenicDriveApp: App {
    @State private var isShowingSettings = LaunchScreen.atLaunch != .home
    @State private var isPlanning = false
    @State private var corpus: LiveCorpus
    @State private var isShowingCorpusDownload: Bool

    init() {
        let corpus = LiveCorpus.launch(wifiOnlyKey: SettingsScreen.corpusWifiOnlyKey)
        _corpus = State(initialValue: corpus)
        _isShowingCorpusDownload = State(initialValue: LaunchScreen.atLaunch == .home && corpus.offersDownload)
    }

    var body: some Scene {
        WindowGroup {
            ScenicHomeScreen(onSettings: { isShowingSettings = true }, surprise: { open, failure in AnyView(SurpriseCard(failure: failure, onOpenInMaps: open)) })
                .sheet(isPresented: $isShowingSettings) {
                    SettingsScreen(opensPaywall: LaunchScreen.atLaunch == .paywall, onDone: { isShowingSettings = false })
                }
                .overlay(alignment: .topLeading) {
                    PlanDriveButton(action: { isPlanning = true })
                        .sheet(isPresented: $isPlanning) {
                            PlanSheetScreen(planner: LivePlanner.make(), onClose: { isPlanning = false })
                        }
                }
                .sheet(isPresented: $isShowingCorpusDownload) {
                    CorpusDownloadSheet(status: corpus.statusText, fraction: corpus.fraction, isWorking: corpus.isWorking,
                                        onDownload: { corpus.start() }, onLater: { isShowingCorpusDownload = false })
                }
        }
    }
}

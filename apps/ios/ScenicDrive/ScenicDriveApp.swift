import Entitlements
import FeaturePlanSheet
import FeatureScenicHome
import FeatureSurpriseMe
import NavAdapter
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
///
/// T-0324 R1/R4: the plan preview's door hands the shell a plan, and the window shows the drive - NavAdapter's
/// DriveHost composed with FeatureScenicHome's DriveScreen - in place of the home until the drive is ended. T-0328 R2:
/// the shell hands DriveHost its reroute sender - the rehearsal's in a DEBUG drive shot, else PlanAdapter's.
///
/// T-0356 R7: the shell hands Settings PlanAdapter's LiveAccountDeletion - the one module seeing both.
///
/// T-0368 R1, R6: the shell reads feature_surprise once from the kept /config answer (no request) for the home, again
/// when the plan sheet closes, and hands the plan sheet the same reader.
///
/// T-0366 R4: the shell builds the home's PostDriveOpenModel from NavAdapter's LiveOpenFix and PlanAdapter's
/// LivePostDriveAnswers, wraps the home's moments with its marker, and calls `opened()` on every foreground open.
@main
struct ScenicDriveApp: App {
    @State private var isShowingSettings = LaunchScreen.atLaunch != .home
    @State private var isPlanning = PlanRehearsal.opensSheet
    @State private var corpus: LiveCorpus
    @State private var isShowingCorpusDownload: Bool
    @State private var drive = DriveRehearsal.atLaunch
    @State private var surpriseGate = LivePlanner.surpriseGate()
    @State private var nextOpen = PostDriveOpenModel(fix: LiveOpenFix(), answers: LivePostDriveAnswers())
    @Environment(\.scenePhase) private var scenePhase

    init() {
        let corpus = LiveCorpus.launch(wifiOnlyKey: SettingsScreen.corpusWifiOnlyKey)
        _corpus = State(initialValue: corpus)
        _isShowingCorpusDownload = State(initialValue: LaunchScreen.atLaunch == .home && corpus.offersDownload && VehicleSetting.isChosen)
    }

    var body: some Scene {
        WindowGroup {
            if let drive, let host = DriveHost(preview: drive, sender: DriveRehearsal.rerouter ?? LivePlanner.rerouter(for: drive), content: { display in DriveScreen(preview: drive, display: display, onEnd: { self.drive = nil }) }) {
                host.environment(\.postDriveAnswers, LivePostDriveAnswers())
                    .environment(\.driveMoments, LiveMoments())
            } else {
                home
            }
        }
    }

    private var home: some View {
        GeometryReader { proxy in
        ScenicHomeScreen(onSettings: { isShowingSettings = true }, surpriseGate: surpriseGate, surprise: { open, failure in AnyView(SurpriseCard(failure: failure, onOpenInMaps: open)) })
            .frame(width: proxy.size.width, height: proxy.size.height, alignment: .top)
        }
            .sheet(isPresented: $isShowingSettings) {
                SettingsScreen(opensPaywall: LaunchScreen.atLaunch == .paywall, vehicle: VehicleSetting.name, deleteAccount: { await LiveAccountDeletion.run() }, onDone: { isShowingSettings = false })
            }
            .safeAreaInset(edge: .top, alignment: .leading, spacing: 0) {
                PlanDriveButton(action: { isPlanning = true })
                    .dynamicTypeSize(...HomeTypeSize.cap)
                    .sheet(isPresented: $isPlanning, onDismiss: { surpriseGate = LivePlanner.surpriseGate() }) {
                        PlanSheetScreen(planner: LivePlanner.make(), tripPlanner: LiveTripPlanner.make(), dayLinks: TripDayLinks.urls, loopPlanner: LiveLoopPlanner.make(), loopLink: LoopLinks.url, surpriseGate: { LivePlanner.surpriseGate() }, onDrive: { isPlanning = false; drive = $0 }, previewMap: { AnyView(PlanPreviewMap(preview: $0)) }, onClose: { isPlanning = false })
                    }
            }
            .sheet(isPresented: $isShowingCorpusDownload) {
                CorpusDownloadSheet(status: corpus.statusText, fraction: corpus.fraction, isWorking: corpus.isWorking,
                                    onDownload: { corpus.start() }, onLater: { isShowingCorpusDownload = false })
            }
            .environment(\.surpriseLedger, LiveSurpriseLedger.make())
            .environment(\.surpriseMoments, LiveMoments())
            .environment(\.homeMoments, nextOpen.marking(LiveMoments()))
            .environment(nextOpen)
            .onChange(of: scenePhase, initial: true) { if $1 == .active { nextOpen.opened() } }
            .environment(\.planMoments, LiveMoments())
            .environment(\.paywallShown, { LiveMoments.paywallShown() })
            .environment(\.paywallConverted, { LiveMoments.paywallConverted() })
    }
}

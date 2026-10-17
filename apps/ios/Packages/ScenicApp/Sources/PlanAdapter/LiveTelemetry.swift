import Foundation
import ScenicKit
import Telemetry

/// The app's telemetry (T-0355): Telemetry's `TelemetryClient` over URLSession, from the same https base URL as
/// LivePlanner (none - nothing is sent). Its x-scenic-device id is StoredInstallID's, read as each post is built
/// (T-0367), so a deleted account's id is never sent again in the launch (T-0356 R3). Each case PlanAdapter emits
/// is constructed on exactly ONE line here (R6, ops/lib/check-telemetry-emit-sites.py); `record` hands the event to a Task, so no
/// user action ever awaits telemetry, and the client drops whatever fails (R3).
public enum LiveTelemetry {
    private static let client: TelemetryClient? = build()

    static func build() -> TelemetryClient? {
        guard let base = LiveBaseURL.url else { return nil }
        return TelemetryClient(base: base, device: { StoredInstallID().installID() },
                               transport: URLSessionTelemetryTransport())
    }

    private static func record(_ event: TelemetryEvent) {
        guard let client else { return }
        Task { await client.record(event) }
    }

    /// The one location telemetry carries (R4): the H3 resolution-5 cell of the plan's origin, made here.
    static func planRequested(_ feature: PlanFeature, budgetMinutes: Int, origin: Coordinate) {
        guard let cell = H3Cell.containing(latitudeDegrees: origin.latitude, longitudeDegrees: origin.longitude) else {
            return
        }
        record(TelemetryEvent.planRequested(feature: feature, budgetMinutes: budgetMinutes, origin: cell))
    }

    static func planResult(_ kind: PlanResultKind) {
        record(TelemetryEvent.planResult(kind))
    }

    static func surpriseShown() {
        record(TelemetryEvent.surpriseShown)
    }

    /// T-0358 R6: the post-drive answer - prettier or not; a skip never reaches here (PostDriveQuestion.send).
    static func postDriveAnswer(prettier: Bool) {
        record(TelemetryEvent.postDriveAnswer(prettier: prettier))
    }

    /// T-0361: the cases LiveMoments and LiveCorpus hand here, one emit line each (R2-R8).
    static func previewShown() {
        record(TelemetryEvent.previewShown)
    }

    static func handoffTapped(_ app: HandoffApp) {
        record(TelemetryEvent.handoffTapped(app))
    }

    static func driveStarted() {
        record(TelemetryEvent.driveStarted)
    }

    /// The fraction is floored to a whole percent here (CompletionPercent): no finer share of a route is sent.
    static func driveCompleted(fraction: Double, deviations: Int) {
        record(TelemetryEvent.driveCompleted(CompletionPercent(fraction: fraction), deviations: deviations))
    }

    static func driveAbandoned(fraction: Double) {
        record(TelemetryEvent.driveAbandoned(CompletionPercent(fraction: fraction)))
    }

    static func surpriseNotThis(_ reason: SurpriseNotThisReason) {
        record(TelemetryEvent.surpriseNotThis(reason))
    }

    static func surpriseTakeMeThere() {
        record(TelemetryEvent.surpriseTakeMeThere)
    }

    static func corpusActivated(version: Int) {
        record(TelemetryEvent.corpusActivated(version: version))
    }

    static func paywall(_ step: PaywallStep) {
        record(TelemetryEvent.paywall(step))
    }
}

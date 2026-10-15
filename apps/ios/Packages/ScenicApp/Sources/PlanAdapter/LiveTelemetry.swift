import Foundation
import ScenicKit
import Telemetry

/// The app's telemetry (T-0355): Telemetry's `TelemetryClient` over URLSession, from the same https base URL as
/// LivePlanner (none - nothing is sent), held by InstallBoundTelemetry so the install id is read at each record and
/// a deleted account's id is never sent again in the launch (T-0356 rv1). Each case PlanAdapter emits is constructed
/// on exactly ONE line here (R6, ops/lib/check-telemetry-emit-sites.py); `record` hands the event to a Task, so no
/// user action ever awaits telemetry, and the client drops whatever fails (R3).
public enum LiveTelemetry {
    private static let client: InstallBoundTelemetry? = build()

    static func build() -> InstallBoundTelemetry? {
        guard let text = UserDefaults.standard.string(forKey: LivePlanner.baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return nil }
        return InstallBoundTelemetry(base: base)
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
}

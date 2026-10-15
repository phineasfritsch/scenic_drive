import Foundation
import ScenicKit
import Telemetry

/// The app's telemetry (T-0355): Telemetry's `TelemetryClient` over URLSession, built once per launch from the same
/// https base URL as LivePlanner (none - nothing is sent). Each case PlanAdapter emits is constructed on exactly ONE
/// line here (R6, ops/lib/check-telemetry-emit-sites.py); `record` hands the event to a Task, so no user action ever
/// awaits telemetry, and the client drops whatever fails (R3).
public enum LiveTelemetry {
    private static let client: TelemetryClient? = build()

    static func build() -> TelemetryClient? {
        guard let text = UserDefaults.standard.string(forKey: LivePlanner.baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return nil }
        return TelemetryClient(base: base, device: StoredInstallID().installID(),
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
}

import Foundation
import ScenicAPIClient
import ScenicKit

/// The road-trip planner the shell hands the plan sheet (T-0313 R4): TripClient over the same base URL, transport and
/// install id LivePlanner uses, or an unreachable planner when no https base is configured. PlanAdapter stays the only
/// target that imports ScenicAPIClient.
public enum LiveTripPlanner {
    public static func make() -> any TripPlanning {
        guard let text = UserDefaults.standard.string(forKey: LivePlanner.baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return UnreachableTripPlanner() }
        return TelemetryTripPlanner(inner: ClientTripPlanner(client: TripClient(base: base, transport: URLSessionPlanTransport(),
                                                    installID: StoredInstallID(),
                                                    accountToken: StoreKitAccountToken(),
                                                    session: LiveSession.store)))
    }
}

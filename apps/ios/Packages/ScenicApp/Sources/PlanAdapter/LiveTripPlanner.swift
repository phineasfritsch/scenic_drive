import Foundation
import ScenicAPIClient
import ScenicKit

/// The road-trip planner the shell hands the plan sheet (T-0313 R4): TripClient over the same base URL, transport and
/// install id LivePlanner uses, or an unreachable planner when no https base is configured. PlanAdapter stays the only
/// target that imports ScenicAPIClient.
public enum LiveTripPlanner {
    public static func make() -> any TripPlanning {
        guard let base = LiveBaseURL.url else { return UnreachableTripPlanner() }
        let client = ClientTripPlanner(client: TripClient(base: base, transport: URLSessionPlanTransport(),
                                                    installID: StoredInstallID(),
                                                    accountToken: StoreKitAccountToken(),
                                                    session: LiveSession.store))
        // T-0364 R3: the /config cache and our build, so the form hears a pause, an update or its flag first.
        return TelemetryTripPlanner(inner: ConfiguredTripPlanner(planner: client, cache: LivePlanner.cache(base), appBuild: LivePlanner.appBuild))
    }
}

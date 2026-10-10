import Foundation
import ScenicAPIClient
import ScenicKit

/// THE ONLY IMPORTER OF ScenicAPIClient UNDER apps/ios (T-0294 R1), as MapAdapter is of MapLibre: the app's live
/// planner, built once by the shell and handed to the plan sheet as a `RoutePlanning`.
///
/// No deployed Worker URL is in the tree yet (R7), so the base URL is read from UserDefaults `plan.base.url` (a
/// `-plan.base.url https://...` launch argument sets it). Without an https one the planner answers routingOffline
/// and sends nothing.
public enum LivePlanner {
    public static let baseURLKey = "plan.base.url"

    public static func make() -> any RoutePlanning {
        guard let text = UserDefaults.standard.string(forKey: baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return UnreachablePlanner() }
        return TelemetryRoutePlanner(inner: ClientPlanner(client: client(base)))
    }

    /// The drive's reroute sender (T-0328 R2): PlanRerouter on the same client, continuing `preview`'s plan; the sender
    /// that asks nothing (RerouteUnavailable - the drive rejoins) without an https base or a plan token.
    public static func rerouter(for preview: PlanPreview) -> any RerouteSending {
        guard let text = UserDefaults.standard.string(forKey: baseURLKey), let base = URL(string: text),
              base.scheme == "https", let continuation = preview.continuation else { return RerouteUnavailable() }
        return PlanRerouter(client: client(base), place: continuation.place, budgetMinutes: continuation.budgetMinutes)
    }

    private static func client(_ base: URL) -> PlanClient {
        PlanClient(base: base, transport: URLSessionPlanTransport(), installID: StoredInstallID(),
                   accountToken: StoreKitAccountToken(), session: LiveSession.store)
    }
}

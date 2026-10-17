import Foundation
import ScenicAPIClient
import ScenicKit

/// The loop planner the shell hands the plan sheet (T-0314 R3): LoopClient over the same base URL, transport and
/// install id LivePlanner uses, or an unreachable planner when no https base is configured. PlanAdapter stays the only
/// target that imports ScenicAPIClient.
public enum LiveLoopPlanner {
    public static func make() -> any LoopPlanning {
        guard let base = LiveBaseURL.url else { return UnreachableLoopPlanner() }
        let client = ClientLoopPlanner(client: LoopClient(base: base, transport: URLSessionPlanTransport(),
                                                    installID: StoredInstallID(),
                                                    accountToken: StoreKitAccountToken(),
                                                    session: LiveSession.store))
        // T-0364 R3: the /config cache and our build, so the form hears a pause, an update or its flag first.
        return TelemetryLoopPlanner(inner: ConfiguredLoopPlanner(planner: client, cache: LivePlanner.cache(base), appBuild: LivePlanner.appBuild))
    }
}

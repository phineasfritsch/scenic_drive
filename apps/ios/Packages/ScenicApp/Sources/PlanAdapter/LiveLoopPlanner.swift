import Foundation
import ScenicAPIClient
import ScenicKit

/// The loop planner the shell hands the plan sheet (T-0314 R3): LoopClient over the same base URL, transport and
/// install id LivePlanner uses, or an unreachable planner when no https base is configured. PlanAdapter stays the only
/// target that imports ScenicAPIClient.
public enum LiveLoopPlanner {
    public static func make() -> any LoopPlanning {
        guard let text = UserDefaults.standard.string(forKey: LivePlanner.baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return UnreachableLoopPlanner() }
        return ClientLoopPlanner(client: LoopClient(base: base, transport: URLSessionPlanTransport(),
                                                    installID: StoredInstallID()))
    }
}

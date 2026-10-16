import Foundation
import ScenicKit

/// The app's live planner (T-0357 R7): plans are the ClientPlanner's, and its degrade is ConfigDegrade.of the cache's
/// refreshed /config answer against our own build - asked by the plan sheet before the user taps Plan.
public struct ConfiguredPlanner: RoutePlanning {
    public let planner: ClientPlanner
    let cache: ConfigCache
    let appBuild: Int?

    public init(planner: ClientPlanner, cache: ConfigCache, appBuild: Int?) {
        self.planner = planner
        self.cache = cache
        self.appBuild = appBuild
    }

    public func plan(_ ticket: PlanTicket) async -> PlanOutcome {
        await planner.plan(ticket)
    }

    public func degrade() async -> ConfigDegrade {
        ConfigDegrade.of(await cache.refresh(), appBuild: appBuild)
    }
}

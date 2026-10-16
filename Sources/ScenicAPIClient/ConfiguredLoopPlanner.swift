import Foundation
import ScenicKit

/// The app's live loop planner (T-0364 R3): loops are the ClientLoopPlanner's, and its degrade is ConfigDegrade.of the
/// cache's refreshed /config answer against our own build on the loop screen - asked by the loop form before the tap.
public struct ConfiguredLoopPlanner: LoopPlanning {
    public let planner: ClientLoopPlanner
    let cache: ConfigCache
    let appBuild: Int?

    public init(planner: ClientLoopPlanner, cache: ConfigCache, appBuild: Int?) {
        self.planner = planner
        self.cache = cache
        self.appBuild = appBuild
    }

    public func plan(_ ticket: LoopTicket) async -> LoopOutcome {
        await planner.plan(ticket)
    }

    public func degrade() async -> ConfigDegrade {
        ConfigDegrade.of(await cache.refresh(), appBuild: appBuild, on: .loop)
    }
}

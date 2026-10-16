import Foundation
import ScenicKit

/// The app's live road-trip planner (T-0364 R3): trips are the ClientTripPlanner's, and its degrade is ConfigDegrade.of
/// the cache's refreshed /config answer against our own build on the trip screen - asked by the trip form before the tap.
public struct ConfiguredTripPlanner: TripPlanning {
    public let planner: ClientTripPlanner
    let cache: ConfigCache
    let appBuild: Int?

    public init(planner: ClientTripPlanner, cache: ConfigCache, appBuild: Int?) {
        self.planner = planner
        self.cache = cache
        self.appBuild = appBuild
    }

    public func plan(_ ticket: TripTicket) async -> TripOutcome {
        await planner.plan(ticket)
    }

    public func degrade() async -> ConfigDegrade {
        ConfigDegrade.of(await cache.refresh(), appBuild: appBuild, on: .trip)
    }
}

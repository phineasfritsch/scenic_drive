import FerrostarCore
import FerrostarCoreFFI
import Foundation

/// The custom RouteProvider (T-0321 R5): the route is the one already planned, built from DriveSession's line and
/// legs. It never touches the network; a reroute is DriveController's, through RerouteSending.
struct PlannedRouteProvider: CustomRouteProvider {
    let route: Route

    func getRoutes(userLocation: UserLocation, waypoints: [Waypoint]) async throws -> [Route] {
        [route]
    }
}

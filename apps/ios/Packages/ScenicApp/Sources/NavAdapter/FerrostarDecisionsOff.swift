import FerrostarCore
import FerrostarCoreFFI
import Foundation

/// Ferrostar's delegate, deciding nothing (T-0321 R2): deviation tracking is `.none`, and were a deviation ever
/// reported the answer is `.doNothing` - off-route and reroute are DriveController's, never Ferrostar's.
final class FerrostarDecisionsOff: FerrostarCoreDelegate {
    func core(_ core: FerrostarCore, didStartWith route: Route) {}

    func core(_ core: FerrostarCore, correctiveActionForDeviation deviation: DeviationKind,
              remainingWaypoints waypoints: [Waypoint]) -> CorrectiveAction {
        .doNothing
    }

    func core(_ core: FerrostarCore, loadedAlternateRoutes routes: [Route]) {}
}

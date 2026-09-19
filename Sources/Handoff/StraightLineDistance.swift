import Foundation
import ScenicKit

/// How far the drive is in a straight line: great-circle hops from point to point, in driving order.
///
/// ## What this number is, and what it is not
///
/// It is not the driving distance and it is not a duration. Nobody has driven this route and nothing
/// in this repository has measured one, so the screen has no minutes and no miles of road. What it can
/// say honestly is how far apart the pins are, because the pins are verified coordinates and the
/// arithmetic is `ScenicKit.Geo` - a spherical great circle, accurate to about 0.3%, which is far
/// finer than the floor below. The roads between those points are longer than the line through them,
/// always, so the figure understates the drive and can never overstate it.
///
/// ## Where the chain starts
///
/// At the FIRST PIN, not at the user. `AppleMapsDirections(source: nil, …)` means "wherever you are",
/// which is the whole reason this app never asks for a location permission - so the leg from the user
/// to pin 1 is unknown here and is not in the number. The chain ends at the destination, which is the
/// end of the loop.
///
/// ## The floor
///
/// `wholeKilometers(through:)` rounds `.down`, never to nearest. A floored figure can only understate
/// the line, and the one direction a number on this screen may be wrong in is the modest one: "112 km"
/// for 112.9 km of line is a drive that is slightly longer than advertised, while a rounded "113 km"
/// would be a kilometre nobody measured.
public enum StraightLineDistance {
    /// Metres along the chain, summed over consecutive pairs. Fewer than two points is no chain and
    /// therefore no distance - zero, not a crash and not an optional nobody unwraps.
    public static func meters(through points: [Coordinate]) -> Double {
        guard points.count > 1 else { return 0 }
        return zip(points, points.dropFirst()).reduce(0) { total, leg in
            total + Geo.distanceMeters(leg.0, leg.1)
        }
    }

    /// The chain in whole kilometres, floored. See the type note for why it is floored.
    public static func wholeKilometers(through points: [Coordinate]) -> Int {
        Int((meters(through: points) / 1_000).rounded(.down))
    }

    /// The shipped drive as a chain: the seven pins in driving order, then the destination.
    ///
    /// Read from `SkylineRoute`, never re-typed: the pins have one home and their provenance lives
    /// beside them there. Order is the route, so this array is not sorted or deduplicated for the same
    /// reason `SkylineRoute.waypoints` is not.
    public static let skylineRoutePoints: [Coordinate] = SkylineRoute.waypoints + [SkylineRoute.destination]

    /// The number the home screen shows: `skylineRoutePoints`, floored to whole kilometres.
    public static var skylineRouteWholeKilometers: Int { wholeKilometers(through: skylineRoutePoints) }
}

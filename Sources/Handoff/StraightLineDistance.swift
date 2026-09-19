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

    /// The chain in whole miles, floored, from the SAME metres the kilometre figure floors.
    ///
    /// ONE COMPUTATION, TWO RENDERINGS. The miles are not converted from the whole kilometres - that
    /// would floor twice and lose up to a mile - and they are not measured over a second chain. Both
    /// figures are `meters(through:)` divided by a constant and rounded `.down`, for the same reason
    /// the kilometre figure is floored: the one direction a number on this screen may be wrong in is
    /// the modest one.
    ///
    /// 1_609.344 m is the international mile, exactly, by definition.
    public static func wholeMiles(through points: [Coordinate]) -> Int {
        Int((meters(through: points) / 1_609.344).rounded(.down))
    }

    /// The shipped drive as a chain: the seven pins in driving order, then the destination.
    ///
    /// Read from `SkylineRoute`, never re-typed: the pins have one home and their provenance lives
    /// beside them there. Order is the route, so this array is not sorted or deduplicated for the same
    /// reason `SkylineRoute.waypoints` is not.
    public static let skylineRoutePoints: [Coordinate] = SkylineRoute.waypoints + [SkylineRoute.destination]

    /// The number the home screen shows: `skylineRoutePoints`, floored to whole kilometres.
    public static var skylineRouteWholeKilometers: Int { wholeKilometers(through: skylineRoutePoints) }

    /// The LA drive as a chain: the nine pins in driving order, then Westwood.
    ///
    /// A SECOND pair beside the Skyline pair rather than a rewrite of it. The Skyline chain, its
    /// floored literal and `StraightLineDistanceTests` are load-bearing on a drive that ships today;
    /// re-spelling them as `chain(for:)` would re-measure a number under a suite that was not asked
    /// to re-measure it. Both pairs read their pins from the route types, so there is still exactly
    /// one home per coordinate.
    public static let santaMonicaMountainsRoutePoints: [Coordinate] =
        SantaMonicaMountainsRoute.waypoints + [SantaMonicaMountainsRoute.destination]

    /// The LA drive in whole kilometres, floored, the way the Skyline figure is.
    public static var santaMonicaMountainsRouteWholeKilometers: Int {
        wholeKilometers(through: santaMonicaMountainsRoutePoints)
    }

    /// The figure for whichever drive the screen is showing.
    ///
    /// The one place a `HandoffDrive` becomes a distance, so the number under the road list and the
    /// number that travels into the clipboard cannot come from different drives.
    public static func wholeKilometers(for drive: HandoffDrive) -> Int {
        switch drive {
        case .skyline: return skylineRouteWholeKilometers
        case .santaMonicaMountains: return santaMonicaMountainsRouteWholeKilometers
        }
    }

    /// THE NUMBER THE HOME SCREEN RENDERS, in the unit a US driver thinks in.
    ///
    /// Over `drive.chain`, which is the pins-then-destination array both kilometre accessors measure,
    /// so the miles on the screen and the kilometres the suites pin are the same line through the same
    /// pins - checked, not asserted: `StraightLineDistanceTests` and `SantaMonicaMountainsChainTests`
    /// pin both figures side by side over the same metres.
    public static func wholeMiles(for drive: HandoffDrive) -> Int {
        wholeMiles(through: drive.chain)
    }
}

import Foundation
import ScenicKit

/// Builds a `maps.apple.com/directions` URL that reproduces a planned scenic route as pinned stops.
///
/// This is the whole payload of the free tier and of the walking skeleton: the app plans a pretty way home,
/// then hands the driving to Apple Maps. Turn-by-turn inside the app is the paid feature; this is what
/// everybody else gets, so a URL that quietly navigates somewhere else is the product failing at its most
/// common moment.
///
/// ## Where this format comes from
///
/// Apple's *Adopting unified Maps URLs* documentation, read on 2026-09-08, not from memory - the legacy
/// `?daddr=`/`?saddr=` form is the archived `iPhoneURLScheme_Reference` scheme and is NOT what this builds.
/// The documented `/directions` parameters are `source`, `destination`, `waypoint`, `mode`, `avoid`,
/// `transit-preferences`, `start`, and the `*-place-id` variants. Coordinates are "a comma-separated pair of
/// floating point values". `waypoint` is the only repeatable one: *"You can specify multiple waypoints by
/// repeating the `waypoint` parameter."*
///
/// **Apple documents no maximum waypoint count.** `maxWaypoints` below is therefore OUR limit, chosen for
/// our own reasons and named as ours - calling it Apple's would be inventing a constraint and would make any
/// future decision to raise it look like a spec violation instead of a product choice.
///
/// ## What this deliberately does not do
///
/// `avoid=highways` is a documented parameter and is exactly the wrong tool here. The scenic route is
/// already computed, freeway shoulders included on purpose - CLAUDE.md: motorway and trunk are penalised,
/// not excluded, because most drives over 15 km need a freeway shoulder around a scenic middle. Asking Apple
/// to avoid highways would discard the planned route and re-plan a different one, which is the single
/// failure this type exists to prevent.
public struct AppleMapsDirections: Equatable, Sendable {
    /// Our cap on pinned stops, not Apple's - see the type documentation.
    ///
    /// Nine because the pins mark decision points, and a route needing more than nine of them is one the
    /// handoff cannot faithfully reproduce anyway; at that point the honest move is to say so rather than to
    /// emit a URL that is approximately the drive.
    public static let maxWaypoints = 9

    /// Five decimal places, about 1.1 m at this latitude, which is finer than any road centreline this data
    /// has and far finer than a lane.
    ///
    /// NOT the two-decimal rule from P-PRIV-05. That rule governs what reaches OUR server, where coarse
    /// coordinates are a privacy property we chose. This URL is the user handing their own route to Apple by
    /// tapping a button, and rounding it to ~1 km would put the pins on the wrong roads.
    public static let coordinateDecimals = 5

    public enum Mode: String, Sendable, CaseIterable {
        case driving, walking, transit, cycling
    }

    public var source: Coordinate?
    public var destination: Coordinate
    public var waypoints: [Coordinate]
    public var mode: Mode

    public init(source: Coordinate? = nil,
                destination: Coordinate,
                waypoints: [Coordinate] = [],
                mode: Mode = .driving) {
        self.source = source
        self.destination = destination
        self.waypoints = waypoints
        self.mode = mode
    }

    /// The URL, or a refusal.
    ///
    /// Built by `URLComponents` rather than string concatenation so percent-encoding is the framework's
    /// problem: a hand-rolled builder gets the comma in `lat,lon` wrong in one direction or the other, and
    /// an over-encoded `%2C` is a coordinate Apple Maps reads as a search string.
    public func url() throws -> URL {
        if waypoints.count > Self.maxWaypoints {
            throw HandoffError.tooManyWaypoints(count: waypoints.count, max: Self.maxWaypoints)
        }

        var items: [URLQueryItem] = []
        if let source {
            items.append(URLQueryItem(name: "source", value: try Self.pair(source)))
        }
        items.append(URLQueryItem(name: "destination", value: try Self.pair(destination)))
        // Order is the route. `waypoint` repeats, and Apple reads them in the order given, so the array
        // order must survive to the query string unsorted and undeduplicated.
        for w in waypoints {
            items.append(URLQueryItem(name: "waypoint", value: try Self.pair(w)))
        }
        items.append(URLQueryItem(name: "mode", value: mode.rawValue))

        var c = URLComponents()
        c.scheme = "https"
        c.host = "maps.apple.com"
        c.path = "/directions"
        c.queryItems = items
        guard let url = c.url else {
            // Unreachable with validated coordinates; a nil here would mean a component became invalid
            // after validation, and guessing a URL at that point is worse than failing.
            throw HandoffError.notACoordinate(latitude: destination.latitude,
                                              longitude: destination.longitude)
        }
        return url
    }

    /// `latitude,longitude` at `coordinateDecimals`, or a refusal for anything that is not a position.
    ///
    /// Uses the POSIX locale explicitly. `String(format:)` honours the current locale for `%f`, so on a
    /// device set to German this would produce `34,06890` - a decimal comma inside a comma-separated pair,
    /// which parses as four numbers and navigates somewhere in the Gulf of Guinea. That is a real bug this
    /// project would otherwise ship to exactly the users least able to report it.
    static func pair(_ c: Coordinate) throws -> String {
        guard c.latitude.isFinite, c.longitude.isFinite,
              c.latitude >= -90, c.latitude <= 90,
              c.longitude >= -180, c.longitude <= 180 else {
            throw HandoffError.notACoordinate(latitude: c.latitude, longitude: c.longitude)
        }
        return "\(decimal(c.latitude)),\(decimal(c.longitude))"
    }

    static func decimal(_ v: Double) -> String {
        String(format: "%.\(coordinateDecimals)f", locale: Locale(identifier: "en_US_POSIX"), v)
    }
}

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
    /// See `decimal(_:)` for why the formatting consults no locale. This comment used to describe a
    /// `String(format:locale:)` call that the commit fixing that removed, fifteen lines above a comment
    /// explaining at length why it was gone - a reviewer pointed out that both cannot be true.
    static func pair(_ c: Coordinate) throws -> String {
        guard c.latitude.isFinite, c.longitude.isFinite,
              c.latitude >= -90, c.latitude <= 90,
              c.longitude >= -180, c.longitude <= 180 else {
            throw HandoffError.notACoordinate(latitude: c.latitude, longitude: c.longitude)
        }
        return "\(decimal(c.latitude)),\(decimal(c.longitude))"
    }

    /// `v` at `coordinateDecimals`, with a `.` decimal point, built without consulting any locale.
    ///
    /// The first version was `String(format:locale:)` pinned to `en_US_POSIX`, and a reviewer showed that
    /// defence was worth nothing: mutating the locale to `Locale.current` - the obvious simplification, and
    /// what somebody writes who does not know why the identifier is there - left every test green, because
    /// the tests run on an en_US machine. The bug the doc comment described (a German device producing
    /// `34,06890`, a decimal comma inside a comma-separated pair, which Apple Maps reads as four numbers)
    /// would have shipped with a green suite and a comment explaining why it could not.
    ///
    /// So the dependency is removed rather than defended. Integer arithmetic and `String(Int)` have no
    /// locale to consult, which means there is no longer a line here that a locale change could break -
    /// a property no test has to be clever enough to catch.
    ///
    /// Safe for coordinates because `pair(_:)` has already refused anything outside +/-180.
    static func decimal(_ v: Double) -> String {
        // DERIVED from coordinateDecimals, not a literal beside it.
        //
        // This was `let scale = 100_000` with a comment reading "10^coordinateDecimals, see the assertion
        // below". There was no assertion below - a reviewer grepped Sources, Tests and pins/PINS.yaml and
        // found none. The padding loop read the constant while the scale did not, so the two could disagree:
        // setting `coordinateDecimals = 2` produced `34.6890`, which is not a coarser coordinate but a
        // DIFFERENT one, about 69 km north. A public constant that no longer governs the value it names,
        // with a comment pointing at a check that does not exist, in code added to fix exactly this defect
        // class.
        let scale = (1..<coordinateDecimals).reduce(10) { acc, _ in acc * 10 }
        let scaled = (v * Double(scale)).rounded()
        let negative = scaled < 0
        let magnitude = Int(abs(scaled))
        let whole = magnitude / scale
        let fraction = magnitude % scale

        var digits = String(fraction)
        while digits.count < coordinateDecimals { digits = "0" + digits }
        return (negative ? "-" : "") + String(whole) + "." + digits
    }
}

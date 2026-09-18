import Foundation
import Handoff
import ScenicKit
import UIKit

/// The walking skeleton's one hard-coded drive: San Francisco, down the Peninsula the pretty way,
/// back to San Francisco.
///
/// M1.5 in the plan - *"'Open in Apple Maps' with a hard-coded Skyline waypoint list ... You open it
/// on your phone in week 2 and tap into Apple Maps on Skyline."* There is no planner yet, no routing
/// service and no corpus; this is the handoff proven end to end with a route a human chose, so that
/// when `ScenicKit` starts producing waypoints the only new thing is where the array comes from.
///
/// **Why the source is nil and the destination is San Francisco.** `source: nil` means "wherever you
/// are", which Apple Maps resolves to current location - the app never asks for a location permission
/// to build this URL. The route is therefore a loop: leave from where you stand, run the ridge, come
/// back. That is also why the waypoint order below reads north-to-south while the destination is
/// north; the last waypoint is the turn-around, not the end.
///
/// ## Provenance of every number in this file
///
/// Each coordinate is a Nominatim result, queried on 2026-09-18 with `User-Agent:
/// scenic-drive-T-0141`, and rounded to `AppleMapsDirections.coordinateDecimals` (5) - about 1.1 m,
/// finer than any road centreline here. The query that produced it sits beside it. Nothing in this
/// file was recalled from memory: a plausible-looking coordinate off by a hundredth of a degree puts
/// a pin on the wrong side of a ridge, and the drive it produces is somebody else's.
///
/// Five waypoints, against `AppleMapsDirections.maxWaypoints` of 9 - deliberately under, because each
/// pin is a decision point (which exit, which turn) and padding the list with mid-block points would
/// constrain Apple's routing without making the drive any more faithful.
public enum SkylineHandoff {
    // MARK: - The route, in one place

    /// San Francisco.
    ///
    /// Query: `San Francisco, California`
    /// Result: relation 111968, `37.7879363, -122.4075201` -> 37.78794, -122.40752
    ///
    /// A city centroid, which is what Apple Maps wants for "take me back to the city" - a street
    /// address would be a house nobody lives at.
    public static let destination = Coordinate(latitude: 37.78794, longitude: -122.40752)

    /// In driving order. Order is the route: `AppleMapsDirections` emits repeated `waypoint`
    /// parameters in array order and Apple reads them in that order, so sorting or deduplicating this
    /// array would silently re-plan the drive.
    public static let waypoints: [Coordinate] = [
        // 1. I-280, the Junipero Serra Freeway, at its San Francisco end in Daly City. The southbound
        //    on-ramp for the whole drive.
        //    Query:  Junipero Serra Freeway, San Mateo County, California
        //    Result: way 23995546, 37.7052589, -122.4716458  ->  37.70526, -122.47165
        Coordinate(latitude: 37.70526, longitude: -122.47165),

        // 2. Cañada Road at its southern end in Woodside - the exit off 280, then north along the
        //    reservoir. This point is SOUTH of waypoint 3 on purpose: you come off the freeway here
        //    and drive Cañada Rd northbound up to CA-92.
        //    Query:  Cañada Road, Woodside, California
        //    Result: way 276909112, 37.4419723, -122.2666684  ->  37.44197, -122.26667
        Coordinate(latitude: 37.44197, longitude: -122.26667),

        // 3. CA-92, which OSM names Half Moon Bay Road, between the Cañada Rd junction and the
        //    Skyline crossing at Skylawn. Westbound.
        //    Query:  Half Moon Bay Road, San Mateo County, California
        //    Result: way 27672021, 37.5074497, -122.3429934  ->  37.50745, -122.34299
        Coordinate(latitude: 37.50745, longitude: -122.34299),

        // 4. Skyline Boulevard (CA-35) on the ridge, southbound. The drive this whole file exists for.
        //    Query:  Skyline Boulevard, Woodside, California
        //    Result: way 305925415, 37.3877614, -122.2663767  ->  37.38776, -122.26638
        Coordinate(latitude: 37.38776, longitude: -122.26638),

        // 5. Sky Londa - the CA-35 / CA-84 junction, and the turn-around. Chosen over Page Mill Road:
        //    Nominatim's `Page Mill Road, Palo Alto, California` (way 385245835, 37.4193960,
        //    -122.1452121) is Page Mill's *eastern* end down in the Palo Alto flats, which would take
        //    the route off the ridge and into the valley rather than marking a point on it.
        //    Query:  Sky Londa, California
        //    Result: relation 9966012, 37.3722734, -122.2613336  ->  37.37227, -122.26133
        Coordinate(latitude: 37.37227, longitude: -122.26133),
    ]

    // MARK: - Handoff

    /// The route as a handoff request. `driving`, and no `avoid` - see `AppleMapsDirections`: asking
    /// Apple to avoid highways would throw away the 280 shoulder that gets you to the pretty part.
    public static func directions() -> AppleMapsDirections {
        AppleMapsDirections(source: nil,
                            destination: destination,
                            waypoints: waypoints,
                            mode: .driving)
    }

    /// The `maps.apple.com/directions` URL, or the refusal `Handoff` raises.
    ///
    /// Throwing rather than returning an optional keeps the reason: `HandoffError` distinguishes "too
    /// many waypoints" from "that is not a coordinate", and a screen that shows the user a useful
    /// message needs to know which.
    public static func url() throws -> URL {
        try directions().url()
    }

    /// Hands the drive to Apple Maps.
    ///
    /// `@MainActor` because `UIApplication.shared` is main-actor isolated under Swift 6; the isolation
    /// is declared here so the call site does not have to guess.
    ///
    /// The completion handler is ignored on purpose. `open` reports only whether iOS accepted the
    /// URL, and a `false` from a `https://maps.apple.com` URL means Maps is not installed - a state
    /// with no useful recovery from this button. It is not an error the user caused and not one this
    /// skeleton can fix, so it does not get an alert it cannot act on.
    @MainActor
    public static func open() throws {
        let destinationURL = try url()
        UIApplication.shared.open(destinationURL, options: [:], completionHandler: nil)
    }
}

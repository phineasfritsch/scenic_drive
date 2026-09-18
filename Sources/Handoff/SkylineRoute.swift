import Foundation
import ScenicKit

/// The walking skeleton's one hard-coded drive, as coordinates: San Francisco, down the Peninsula the
/// pretty way over Cañada Road and the Skyline ridge, back to San Francisco.
///
/// M1.5 in the plan - *"'Open in Apple Maps' with a hard-coded Skyline waypoint list"*. There is no
/// planner yet, no routing service and no corpus; this is a route a human chose, so that when
/// `ScenicKit` starts producing waypoints the only new thing is where the array comes from.
///
/// ## Why the literals live in `Handoff` and not in the screen
///
/// They used to live in `FeatureScenicHome.SkylineHandoff`, an Apple-only target with no test bundle
/// and no compiler on the authoring box. That put the one property worth checking - that the pins are
/// close enough together to pin the route down - somewhere nothing could check it. Here they are in a
/// Linux target with a test target next to it, so `SkylineRouteTests` runs on this box and in CI.
/// `FeatureScenicHome` already depends on `Handoff`, so the screen reads them from here; the type
/// holds coordinates and nothing else, and knows nothing about UIKit, Apple Maps or a URL.
///
/// ## Provenance of every coordinate in this file
///
/// Every literal below was verified by a Nominatim **reverse** geocode of the literal itself, on
/// 2026-09-18, from this worktree, with `User-Agent: scenic-drive-T-0151 (…)` and at most one request
/// per 1.2 s. The comment beside each pin quotes what that reverse query returned: the OSM way, the
/// `name` field, and the point Nominatim gave back. Forward geocoding is what put the previous last
/// pin on the wrong road - `Sky Londa, California` returns the CDP's centroid (relation 9966012,
/// `37.3722734, -122.2613336`), which is a place, not a point on a carriageway, and it reverse-geocodes
/// to way 32506261, `La Honda Road`. A pin whose comment names a road the pin is not on is the defect
/// this repository exists to catch, so the direction of the query is now part of the rule: a waypoint
/// is a reverse result or it does not go in.
///
/// Nominatim's `extratags` carried no `ref` for any of these ways, so the route numbers in the
/// comments below (CA-35, CA-84, CA-92, I-280) are the local signing, NOT something a query printed.
/// The `name` strings, the way ids and the returned points are.
///
/// Coordinates are rounded to `AppleMapsDirections.coordinateDecimals` (5) - about 1.1 m, finer than
/// any road centreline here.
///
/// ## Bicycle Sunday
///
/// Cañada Road between Edgewood Road and CA-92 is closed to motor vehicles on Sunday mornings for part
/// of the year - "Bicycle Sunday", run by San Mateo County Parks. Four of the seven pins below are on
/// that stretch, so on a Sunday morning in season Apple Maps will route around the whole corridor and a
/// tester will see a drive that does not match this array. That is the road being closed, not the
/// handoff being wrong. The dates and hours are NOT verified here - no query in this repository
/// returned them, and the county's schedule is the only authority for them; this note exists so the
/// next person to see a Sunday-morning detour checks the calendar before changing a coordinate.
public enum SkylineRoute {
    // MARK: - Where the drive ends

    /// San Francisco.
    ///
    /// Query: `San Francisco, California` (forward - this one is a place, not a point on a road)
    /// Result: relation 111968, `37.7879363, -122.4075201` -> 37.78794, -122.40752
    ///
    /// A city centroid, which is what Apple Maps wants for "take me back to the city". The route is a
    /// loop, so this is the end and not the start; `AppleMapsDirections(source: nil, …)` lets Apple
    /// resolve the start to wherever the user is standing, and the app never asks for a location
    /// permission to build the URL.
    public static let destination = Coordinate(latitude: 37.78794, longitude: -122.40752)

    // MARK: - The pins

    /// In driving order. Order is the route: `AppleMapsDirections` emits repeated `waypoint`
    /// parameters in array order and Apple reads them in that order, so sorting or deduplicating this
    /// array would silently re-plan the drive.
    ///
    /// Seven pins, against `AppleMapsDirections.maxWaypoints` of 9 and the plan's "<=9 pinned
    /// waypoints at decision points". Under the cap on purpose: each pin is a decision point, and
    /// padding the list with mid-block points constrains Apple's routing without making the drive any
    /// more faithful. `SkylineRouteTests` types all seven out again and compares.
    public static let waypoints: [Coordinate] = [
        // 1. I-280, the Junipero Serra Freeway, at its San Francisco end in Daly City. The southbound
        //    on-ramp for the whole drive.
        //    Reverse 37.70526, -122.47165
        //      -> way 23995546, name "Junipero Serra Freeway", type motorway,
        //         "Junipero Serra Freeway, Westlake, Daly City, San Mateo County, California, 94132,
        //          United States", returned 37.7052581, -122.4716462
        Coordinate(latitude: 37.70526, longitude: -122.47165),

        // 2. Cañada Road at its southern end in Woodside - the exit off 280, then NORTH along Crystal
        //    Springs Reservoir. This pin is SOUTH of pins 3, 4 and 5 on purpose: you come off the
        //    freeway here and drive Cañada Rd northbound up to CA-92.
        //    Reverse 37.44197, -122.26667
        //      -> way 276909112, name "Cañada Road", type secondary,
        //         "Cañada Road, Woodside Glens, Woodside, San Mateo County, California, 94062,
        //          United States", returned 37.4419720, -122.2666681
        Coordinate(latitude: 37.44197, longitude: -122.26667),

        // 3. Mid-Cañada, on the reservoir run, NORTH of the Edgewood Road junction.
        //
        //    THE RAT-RUN THIS PIN CLOSES. With pins 2 and 5 alone, Cañada Rd carried no pin across the
        //    gap `SkylineRouteTests.maxSpacingOnTheCanadaLeg` measures when this pin is deleted, and
        //    Edgewood Road sits inside that gap: Apple Maps could leave Cañada at Edgewood, run back
        //    up 280, and rejoin CA-92 at the interchange - a freeway shortcut through the middle of
        //    the scenic leg, arriving at every remaining pin in order, with nothing to notice it by.
        //    A pin north of Edgewood cannot be reached that way.
        //
        //    North of Edgewood, from the queries: Edgewood Road is way 262966568, whose bounding box
        //    tops out at latitude 37.4684281; this pin is at 37.47579.
        //    Reverse 37.47579, -122.30852
        //      -> way 157466880, name "Cañada Road", type secondary,
        //         "Cañada Road, San Mateo County, California, 94002, United States",
        //         returned 37.4757907, -122.3085192, bounding box
        //         ["37.4648211", "37.5050132", "-122.3383518", "-122.2988550"]
        Coordinate(latitude: 37.47579, longitude: -122.30852),

        // 4. The top of Cañada Road, at the CA-92 junction. The turn.
        //
        //    Nominatim returned this way's own north-west bounding-box corner for this query, which is
        //    where Cañada Road ends at CA-92 - the point returned, 37.5062107 / -122.3407294, is the
        //    corner ["37.5058471", "37.5062130", "-122.3407323", "-122.3402096"] to five decimals.
        //    Pinning the Cañada side of the junction rather than the CA-92 side is deliberate: it is
        //    the approach that has to be driven, and pin 5 already stands on CA-92.
        //    Reverse 37.50621, -122.34073
        //      -> way 417324930, name "Cañada Road", type secondary,
        //         "Cañada Road, San Mateo County, California, 94002, United States",
        //         returned 37.5062107, -122.3407294
        Coordinate(latitude: 37.50621, longitude: -122.34073),

        // 5. CA-92, which OSM names Half Moon Bay Road, just west of the Cañada junction, heading for
        //    the Skyline crossing at Skylawn. Westbound.
        //    Reverse 37.50745, -122.34299
        //      -> way 27672021, name "Half Moon Bay Road", type primary,
        //         "Half Moon Bay Road, San Mateo County, California, 94002, United States",
        //         returned 37.5074482, -122.3429911
        Coordinate(latitude: 37.50745, longitude: -122.34299),

        // 6. Skyline Boulevard (CA-35) on the ridge, southbound. The drive this whole file exists for.
        //    Reverse 37.38776, -122.26638
        //      -> way 305925415, name "Skyline Boulevard", type secondary,
        //         "Skyline Boulevard, Sky Londa, Woodside, San Mateo County, California, 94025,
        //          United States", returned 37.3877625, -122.2663781
        Coordinate(latitude: 37.38776, longitude: -122.26638),

        // 7. Skyline Boulevard south of Sky Londa, and the turn-around.
        //
        //    REPLACES the Sky Londa CDP centroid, which was this list's last pin and was not on a
        //    road: relation 9966012 at 37.3722734 / -122.2613336 reverse-geocodes to way 32506261,
        //    "La Honda Road" - CA-84, off the ridge, with a comment naming the CA-35/CA-84 junction.
        //    This pin is on a carriageway named Skyline Boulevard and is south of that centroid
        //    (37.36648 < 37.3722734), so the turn-around is past the junction rather than beside it.
        //    Reverse 37.36648, -122.24765
        //      -> way 258851767, name "Skyline Boulevard", type secondary,
        //         "Skyline Boulevard, San Mateo County, California, 94020, United States",
        //         returned 37.3664803, -122.2476514, bounding box
        //         ["37.3609379", "37.3709510", "-122.2512060", "-122.2469250"]
        Coordinate(latitude: 37.36648, longitude: -122.24765),
    ]
}

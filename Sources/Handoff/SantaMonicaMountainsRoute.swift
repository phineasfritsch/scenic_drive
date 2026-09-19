import Foundation
import ScenicKit

/// The owner's drive, as coordinates: west out of Brentwood on Sunset Boulevard, north up the coast,
/// up Topanga Canyon to the Valley, the freeway baseline back over the Sepulveda Pass, east along the
/// paved end of Mulholland Drive and down Beverly Glen into Westwood.
///
/// M1.5's second hard-coded drive, and the first one the owner can start from a driveway. The Skyline
/// loop (`SkylineRoute`) is 350 miles away and can be read on a desk but not driven; the plan's
/// success criterion is *"the developer drives a route this app made"*, and every human gate is a
/// drive. Same discipline as `SkylineRoute`, same shape: a route a human chose, held as coordinates
/// in a Linux target with a test target beside it.
///
/// ## Provenance of every coordinate in this file
///
/// Every literal below was verified by a Nominatim **reverse** geocode of the literal itself, on
/// 2026-09-19, from this worktree, with
/// `User-Agent: scenic-drive-T-0178 (github.com/phineasfritsch/scenic_drive; owner-contact via repo)`,
/// `format=jsonv2&zoom=17&extratags=1`, at most one request per 1.1 s. The comment beside each pin
/// quotes what that reverse query returned: the OSM way, the `name` field, the class and the point
/// Nominatim gave back. Forward geocoding is what put `SkylineRoute`'s last pin on the wrong road, so
/// the direction of the query is the rule: a waypoint is a reverse result or it does not go in.
/// Overpass was used only to LOCATE geometry - junction nodes and the extent of ways - and no Overpass
/// or forward result became a pin.
///
/// Three candidate points were REFUSED because the reverse result named a side street and not the
/// carriageway claimed: 34.07160,-118.47530 (`Firth Avenue`), 34.06800,-118.47600 (`North Bundy
/// Drive`) and the Sunset/Bundy junction node 123082348 at 34.06032,-118.47594 (`South Bundy Drive`).
/// That is why pin 1 sits mid-block on Sunset rather than on the Bundy junction.
///
/// The route numbers in the comments (CA-1, CA-27, US-101, I-405) are the local signing: Nominatim's
/// `extratags` carried no `ref` for any of these ways. The `name` strings, the way ids, the classes
/// and the returned points are query results.
///
/// ## Mulholland is not continuous from Topanga, and this route does not pretend it is
///
/// The obvious shape - up Topanga Canyon Boulevard, right onto Mulholland, east along the crest - is
/// not drivable. Two Overpass shared-node joins found NO node common to a way named
/// `~"Topanga Canyon Boulevard$"` and any Mulholland-named way, while the same query shape returned
/// the PCH/Topanga node (122761988) and the Sunset/PCH node (6031887097) in the same session. The
/// Mulholland-named ways nearest the crest are the unpaved "Dirt Mulholland" stretch; their `surface`
/// tags are NOT verified here - `out tags;` over that name gateway-timed out (HTTP 504) on two
/// bboxes - so nothing in this file claims them. What is verified is the missing shared node, and
/// that is what pin 7 is chosen against: the drive stays on CA-27 to Ventura Boulevard, takes the
/// freeway baseline east and south, and joins Mulholland Drive on its paved eastern section.
///
/// This is a ~47 km straight line and roughly 70 km of road, not a 25-minute detour off a commute.
/// No screen states a duration (`ScenicHomeScreen`), so nothing claims otherwise.
///
/// Coordinates are rounded to `AppleMapsDirections.coordinateDecimals` (5) - about 1.1 m.
public enum SantaMonicaMountainsRoute {
    // MARK: - Where the drive ends

    /// Westwood Village, where the owner starts and ends.
    ///
    /// A point on a carriageway, not a neighbourhood centroid: `SkylineRoute`'s destination is a city
    /// centroid because "take me back to San Francisco" is a city-sized instruction, while this drive
    /// ends on a street the owner turns onto.
    ///
    /// Reverse 34.06110, -118.44548
    ///   -> way 763033286, name "Westwood Boulevard", highway/secondary,
    ///      "Westwood Boulevard, Westwood Village, Westwood, Los Angeles, Los Angeles County,
    ///       California, 90024, United States", returned 34.0611000, -118.4454761
    public static let destination = Coordinate(latitude: 34.06110, longitude: -118.44548)

    // MARK: - The pins

    /// In driving order. Order is the route: `AppleMapsDirections` emits repeated `waypoint`
    /// parameters in array order and Apple reads them in that order, so sorting or deduplicating this
    /// array would silently re-plan the drive.
    ///
    /// Nine pins, against `AppleMapsDirections.maxWaypoints` of 9 and the plan's "<=9 pinned
    /// waypoints at decision points". At the cap, not padded to it: every one is a junction or a turn
    /// that a cheaper path would otherwise skip, and the reason each exists is written beside it.
    /// `SantaMonicaMountainsRouteTests` types all nine out again and compares.
    public static let waypoints: [Coordinate] = [
        // 1. West Sunset Boulevard in Brentwood. The pin that says the drive is ON Sunset.
        //
        //    THE SHORTCUT THIS PIN CLOSES. Without it, 405 south -> 10 west -> PCH north ->
        //    Chautauqua Boulevard reaches every later pin in order with Sunset Boulevard - the whole
        //    scenic middle - never driven. A pin this far east on Sunset cannot be reached that way.
        //    Reverse 34.05820, -118.47930
        //      -> way 399990528, name "West Sunset Boulevard", highway/secondary,
        //         "West Sunset Boulevard, Brentwood, Los Angeles, Los Angeles County, California,
        //          90049, United States", returned 34.0581961, -118.4792989
        Coordinate(latitude: 34.05820, longitude: -118.47930),

        // 2. West Sunset Boulevard in Pacific Palisades, WEST of the Chautauqua junction.
        //
        //    THE SHORTCUT THIS PIN CLOSES. Pins 1 and 3 alone leave a 7362.5 m gap across the
        //    Palisades, and Chautauqua Boulevard and the San Vicente/Ocean Avenue cuts both sit
        //    inside it - a drive could leave Sunset, drop to the coast early and rejoin at pin 3.
        //    West of Chautauqua, that cut cannot serve as a shortcut between pins 1 and 2.
        //    Reverse 34.04739, -118.52581
        //      -> way 522193485, name "West Sunset Boulevard", highway/secondary,
        //         "West Sunset Boulevard, Pacific Palisades, Los Angeles, Los Angeles County,
        //          California, 90272, United States", returned 34.0473907, -118.5258094
        Coordinate(latitude: 34.04739, longitude: -118.52581),

        // 3. The west end of Sunset, where it meets Pacific Coast Highway (CA-1) at Inceville. The
        //    turn north onto the coast.
        //    Reverse 34.03857, -118.55562
        //      -> way 675941117, name "West Sunset Boulevard", highway/secondary,
        //         "West Sunset Boulevard, Inceville, Los Angeles, Los Angeles County, California,
        //          90272, United States", returned 34.0385699, -118.5556173
        Coordinate(latitude: 34.03857, longitude: -118.55562),

        // 4. Pacific Coast Highway at Topanga Canyon Boulevard (CA-27) - the junction the Brief
        //    names, pinned on the PCH side, which is the approach that has to be driven.
        //
        //    The same choice `SkylineRoute` made at CA-92: pin the approach, not the road you turn
        //    onto, so a second pin is not spent on one junction.
        //    Reverse 34.04011, -118.57930
        //      -> way 675540508, name "Pacific Coast Highway", highway/trunk,
        //         "Pacific Coast Highway, Los Angeles County, California, 90401, United States",
        //         returned 34.0401096, -118.5792999
        Coordinate(latitude: 34.04011, longitude: -118.57930),

        // 5. North Topanga Canyon Boulevard at Topanga village, on the CA-27 carriageway.
        //
        //    THE RESIDENTIAL AND SCHOOL-ZONE CUT-THROUGHS THIS PIN AND PIN 6 EXCLUDE, by name: Tuna
        //    Canyon Road (way 73156338, highway=tertiary, met at 34.04429,-118.58889 in this task's
        //    reverse scan) and Fernwood Pacific Drive, which leave CA-27 below the village and climb
        //    the residential grid; Entrada Road and Topanga School Road, the village streets past
        //    Topanga Elementary; and Old Topanga Canyon Road, which leaves CA-27 just north of the
        //    village and runs to Calabasas - a different way to the Valley entirely. None of them
        //    touches this pin or pin 6, both reverse-verified points on the state highway, so no
        //    route through them reaches these pins. Pins 4 and 6 alone leave a 9733.0 m gap with all
        //    of that inside it.
        //    Reverse 34.09312, -118.60182
        //      -> way 667514947, name "North Topanga Canyon Boulevard", highway/primary,
        //         "North Topanga Canyon Boulevard, Topanga, Los Angeles County, California, 90290,
        //          United States", returned 34.0931194, -118.6018208
        Coordinate(latitude: 34.09312, longitude: -118.60182),

        // 6. Topanga Canyon Boulevard at the crest, above Glenview. This is also the Mulholland
        //    junction the Brief asks to be pinned; see the type note for why the drive continues
        //    north from here instead of turning east onto it.
        //    Reverse 34.12587, -118.60045
        //      -> way 38311861, name "Topanga Canyon Boulevard", highway/primary,
        //         "Topanga Canyon Boulevard, Glenview, Los Angeles County, California, 90290,
        //          United States", returned 34.1258708, -118.6004468
        Coordinate(latitude: 34.12587, longitude: -118.60045),

        // 7. Topanga Canyon Boulevard in Woodland Hills, at the Ventura Boulevard end - the turn onto
        //    the freeway baseline (US-101 east, I-405 south over the Sepulveda Pass).
        //
        //    THE SHORTCUT THIS PIN CLOSES. It is the pin that forbids Dirt Mulholland as a way from
        //    the crest to pin 8: an unpaved crest track is exactly the hard safety gate the product
        //    refuses to route onto, and a path taking it does not reach a pin down in the Valley.
        //    Reverse 34.16801, -118.60576
        //      -> way 401296501, name "Topanga Canyon Boulevard", highway/primary,
        //         "Topanga Canyon Boulevard, Woodland Hills, ... Los Angeles, Los Angeles County,
        //          California, 91364, United States", returned 34.1680101, -118.6057640
        Coordinate(latitude: 34.16801, longitude: -118.60576),

        // 8. Mulholland Drive east of the 405, above Sherman Oaks: the PAVED section, signed
        //    `highway=secondary`, and the ridge run this drive exists for.
        //    Reverse 34.13208, -118.45321
        //      -> way 1533792498, name "Mulholland Drive", highway/secondary,
        //         "Mulholland Drive, Sherman Oaks Neighborhood Council District, Los Angeles,
        //          Los Angeles County, California, 91403, United States",
        //         returned 34.1320831, -118.4532098
        Coordinate(latitude: 34.13208, longitude: -118.45321),

        // 9. North Beverly Glen Boulevard, the descent south off the ridge into Westwood.
        //
        //    THE RESIDENTIAL CUT-THROUGHS THIS PIN EXCLUDES: Roscomare Road, the other way down off
        //    Mulholland here, which runs past Roscomare Road Elementary, and Benedict Canyon Drive
        //    further east. Choosing the descent rather than leaving it to Apple is the whole point of
        //    a decision-point pin.
        //    Reverse 34.12922, -118.44168
        //      -> way 402237654, name "North Beverly Glen Boulevard", highway/secondary,
        //         "North Beverly Glen Boulevard, Los Angeles, Los Angeles County, California,
        //          United States", returned 34.1292206, -118.4416818
        Coordinate(latitude: 34.12922, longitude: -118.44168),
    ]
}

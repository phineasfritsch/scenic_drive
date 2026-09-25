import Foundation
import ScenicKit

/// The engine's drive, as coordinates: Topanga village to Malibu over Saddle Peak and Piuma instead of along
/// PCH - the first route in this repository that the APP made rather than a human (T-0236, from PR #124).
///
/// ## Provenance: one `ops/plan` run, not a geocoder
///
/// `SkylineRoute` and `SantaMonicaMountainsRoute` are routes a human chose, pinned by reverse geocodes. This one
/// is the planner's answer: `ops/plan` over the recorded pair in `Tests/Fixtures/t0182/plan-pair` at +25 min,
/// lambda 7.75, whose run and `maps.apple.com` URL are quoted in T-0182's Log (queue/done/T-0182-*, the
/// `WAYPOINTS 9 of max 9` / `URL` lines): 33.1 km in 37 min 33 s against 17 min 56 s for the fastest route via
/// PCH. The nine pins and the destination below are that URL's, EXACTLY - the planner's decision points, at
/// `AppleMapsDirections.coordinateDecimals`. Beside each pin: the recorded path's nearest vertex, how far it is,
/// and the `osm_way_id` / `road_class` the fixture's `details` carry there. Those are committed data. The road
/// NAMES are the owner's route preview's lookups of those way ids and are not committed anywhere else.
///
/// The drawn line (`apps/ios/ScenicDrive/Routes/saddle-peak.geojson`) is the same recorded path, simplified by
/// `ops/lib/make-route-geojson.py`; `SaddlePeakGeometryTests` binds it to these pins so the line on the map and
/// the URL cannot come apart.
public enum SaddlePeakRoute {
    /// Where the engine's run STARTED - ops/plan's `source`, on Entrada Road in Topanga village (way 13388359,
    /// residential; the recorded path's first vertex is 5.47 m from it).
    ///
    /// NOT A WAYPOINT AND NOT IN THE URL, ruled in T-0236's Log (R1): the cap is full - ops/plan printed
    /// `WAYPOINTS 9 of max 9`, and a tenth pin makes `AppleMapsDirections.url()` throw `tooManyWaypoints` - and
    /// the app sends `source: nil`, "wherever you are", because it asks for no location. Pin 1 is 1.2 km away on
    /// Fernwood Pacific Drive, not on this road. It is kept so `SaddlePeakGeometryTests` can bind the drawn
    /// line's first point to the place the engine actually started.
    public static let origin = Coordinate(latitude: 34.09440, longitude: -118.60130)

    /// Civic Center Way, Malibu - ops/plan's `destination`. The path's last vertex is 6.22 m from it
    /// (way 1296483244, service - the car park entrance the router snapped to).
    public static let destination = Coordinate(latitude: 34.03650, longitude: -118.68700)

    /// In driving order - order is the route (`AppleMapsDirections` emits `waypoint` in array order). Nine,
    /// at `AppleMapsDirections.maxWaypoints`, because the planner placed nine; none is padding.
    public static let waypoints: [Coordinate] = [
        // 1. Fernwood Pacific Drive, climbing out of the canyon - path vertex 98 at 0.7 m, way 691593545, tertiary.
        Coordinate(latitude: 34.08350, longitude: -118.60162),
        // 2. Fernwood Pacific Drive, higher - vertex 168 at 0.4 m, way 1237332026, tertiary.
        Coordinate(latitude: 34.07941, longitude: -118.60288),
        // 3. Tuna Canyon Road at the Saddle Peak Road turn - vertex 350 at 0.5 m, way 13352663, tertiary.
        Coordinate(latitude: 34.06814, longitude: -118.61111),
        // 4. Saddle Peak Road - vertex 487 at 0.6 m, way 791537001, tertiary.
        Coordinate(latitude: 34.07507, longitude: -118.62613),
        // 5. Saddle Peak Road, north along the ridge - vertex 577 at 0.2 m, way 791536999, tertiary.
        Coordinate(latitude: 34.08375, longitude: -118.63666),
        // 6. The Schueren Road turn - vertex 614 at 0.3 m, way 13357693, tertiary.
        Coordinate(latitude: 34.08111, longitude: -118.64574),
        // 7. The Piuma Road turn - vertex 745 at 0.5 m, way 13279193, tertiary.
        Coordinate(latitude: 34.07001, longitude: -118.65343),
        // 8. North Malibu Canyon Road, after Piuma - vertex 1205 at 0.5 m, way 43178451, primary.
        Coordinate(latitude: 34.08025, longitude: -118.70367),
        // 9. South Malibu Canyon Road, the descent to the coast - vertex 1228 at 0.3 m, way 42775111, primary.
        Coordinate(latitude: 34.06937, longitude: -118.70790),
    ]

    /// The bundled line's resource name (`HandoffDrive.routeGeometryResource` forwards here).
    public static let geometryResource = "saddle-peak"
}

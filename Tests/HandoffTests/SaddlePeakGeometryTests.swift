import Foundation
import Handoff
import ScenicKit
import Testing

/// THE LINE ON THE MAP AND THE URL CANNOT DRIFT APART (T-0236, R2).
///
/// The app draws `apps/ios/ScenicDrive/Routes/<routeGeometryResource>.<routeGeometryExtension>` over the map,
/// and the button hands `HandoffDrive.url()` to Apple Maps. Both come from different places - the line from
/// `ops/lib/make-route-geojson.py` over the recorded GraphHopper path, the pins from `SaddlePeakRoute` - so this
/// suite binds them: the file is found through the SAME three shipping symbols the app's `Bundle.main` lookup
/// uses, its ends sit on the drive's origin and destination, and every pin the URL carries lies on the drawn
/// line in driving order. A pin moved off the road, a line re-derived from another path, or a resource name
/// pointing at another file each fail here by name.
///
/// Bounds, from the measurement in T-0236's Log: the raw path's ends are 5.47 m from the origin and 6.22 m
/// from the destination, every pin is at most 0.7 m from a raw vertex, Douglas-Peucker keeps every dropped
/// vertex within 5 m of the kept line, and rounding to 5 decimals moves a position at most ~0.8 m. 10 m
/// covers all of that and is still far inside the ~1.2 km a pin would have to move to reach another road here.
@Suite("SaddlePeakGeometry")
struct SaddlePeakGeometryTests {
    static let endToleranceMeters = 10.0
    static let pinToleranceMeters = 10.0
    /// `make-route-geojson.py` at 5 m over the fixture's 1,393 points, quoted in the Log.
    static let expectedPositions = 483

    struct Collection: Decodable {
        let type: String
        let bbox: [Double]
        let features: [Feature]
    }

    struct Feature: Decodable {
        let type: String
        let properties: Properties
        let geometry: Geometry
    }

    struct Properties: Decodable {
        let name: String
        let source: String
        let tolerance_m: Double
        let source_points: Int
        let points: Int
    }

    struct Geometry: Decodable {
        let type: String
        let coordinates: [[Double]]
    }

    static let appFolder = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        .appendingPathComponent("apps/ios/ScenicDrive")

    /// The file the app would load for `drive`, built from the shipping symbols only.
    static func resourceURL(_ name: String) -> URL {
        appFolder.appendingPathComponent(HandoffDrive.routeGeometrySubdirectory)
            .appendingPathComponent(name)
            .appendingPathExtension(HandoffDrive.routeGeometryExtension)
    }

    static func load(_ drive: HandoffDrive) throws -> (Collection, [Coordinate]) {
        let name = try #require(drive.routeGeometryResource, "\(drive.rawValue) names no route geometry")
        let data = try Data(contentsOf: resourceURL(name))
        let doc = try JSONDecoder().decode(Collection.self, from: data)
        let feature = try #require(doc.features.first, "no feature in \(name)")
        let positions = try feature.geometry.coordinates.map { pair -> Coordinate in
            try #require(pair.count == 2, "not a position: \(pair)")
            return Coordinate(latitude: pair[1], longitude: pair[0])
        }
        return (doc, positions)
    }

    /// Metres from `p` to the segment `a`-`b`, in an equirectangular plane about `p`.
    static func metresToSegment(_ p: Coordinate, _ a: Coordinate, _ b: Coordinate) -> Double {
        let r = Geo.earthRadiusMeters
        let k = cos(p.latitude * .pi / 180)
        func xy(_ c: Coordinate) -> (Double, Double) {
            ((c.longitude - p.longitude) * .pi / 180 * r * k, (c.latitude - p.latitude) * .pi / 180 * r)
        }
        let (ax, ay) = xy(a)
        let (bx, by) = xy(b)
        let dx = bx - ax, dy = by - ay
        let length2 = dx * dx + dy * dy
        let t = length2 == 0 ? 0 : max(0, min(1, -(ax * dx + ay * dy) / length2))
        return ((ax + t * dx) * (ax + t * dx) + (ay + t * dy) * (ay + t * dy)).squareRoot()
    }

    @Test("the drawn line starts at the drive's origin and ends at the destination the URL carries")
    func theLineEndsAreTheDrivesEnds() throws {
        let (_, positions) = try Self.load(.saddlePeak)
        let first = try #require(positions.first)
        let last = try #require(positions.last)
        let start = Geo.distanceMeters(first, SaddlePeakRoute.origin)
        let end = Geo.distanceMeters(last, HandoffDrive.saddlePeak.destination)
        #expect(start <= Self.endToleranceMeters, "the line starts \(start) m from the origin")
        #expect(end <= Self.endToleranceMeters, "the line ends \(end) m from the handoff's destination")
    }

    @Test("every pin the handoff carries lies on the drawn line, in driving order")
    func everyPinIsOnTheLineInOrder() throws {
        let (_, positions) = try Self.load(.saddlePeak)
        try #require(positions.count >= 2)
        var previous = 0
        for (n, pin) in HandoffDrive.saddlePeak.waypoints.enumerated() {
            var best = Double.infinity
            var bestSegment = -1
            for i in 0..<(positions.count - 1) {
                let d = Self.metresToSegment(pin, positions[i], positions[i + 1])
                if d < best { best = d; bestSegment = i }
            }
            #expect(best <= Self.pinToleranceMeters, "pin \(n + 1) is \(best) m from the drawn line")
            #expect(bestSegment >= previous, "pin \(n + 1) meets the line at segment \(bestSegment), before \(previous)")
            previous = bestSegment
        }
    }

    @Test("the bbox is the line's own extent, and the file is the stated derivation")
    func theFileIsTheStatedDerivation() throws {
        let (doc, positions) = try Self.load(.saddlePeak)
        #expect(doc.type == "FeatureCollection")
        #expect(doc.features.count == 1, "got \(doc.features.count) features")
        let feature = try #require(doc.features.first)
        #expect(feature.geometry.type == "LineString")
        #expect(positions.count == Self.expectedPositions, "got \(positions.count) positions")
        #expect(feature.properties.points == positions.count)
        #expect(feature.properties.source_points == 1_393)
        #expect(feature.properties.tolerance_m == 5)
        #expect(feature.properties.source == "Tests/Fixtures/t0182/plan-pair/lambda-7.75.json")
        let lons = positions.map(\.longitude)
        let lats = positions.map(\.latitude)
        let extent = [lons.min(), lats.min(), lons.max(), lats.max()].compactMap { $0 }
        #expect(doc.bbox == extent, "bbox \(doc.bbox) is not the extent \(extent)")
    }

    @Test("every drive that names a line ships its file; the loop and the Peninsula name none")
    func everyNamedLineShips() throws {
        for drive in HandoffDrive.allCases {
            guard let name = drive.routeGeometryResource else { continue }
            let path = Self.resourceURL(name).path
            #expect(FileManager.default.fileExists(atPath: path), "\(drive.rawValue): no file at \(path)")
        }
        #expect(HandoffDrive.allCases.filter { $0.routeGeometryResource != nil } == [.saddlePeak])
    }
}

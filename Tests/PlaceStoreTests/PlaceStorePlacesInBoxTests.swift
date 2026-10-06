#if canImport(GRDB)
import Foundation
import PlaceStore
import XCTest

/// `PlaceStore.places(in:)` over THE committed fallback (T-0273 R1), the read the Surprise card makes. Every
/// expected row and count was read out of apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite (sha256
/// 05c3a19c...7e936d) with the same SQL by Python's sqlite3 before this test was written (.build/t0273/calc.py).
final class PlaceStorePlacesInBoxTests: XCTestCase {
    private func store() throws -> PlaceStore {
        try PlaceStore(path: PlaceStoreFallbackTests.committed.path)
    }

    func testTheSaddlePeakBoxReturnsItsSixPlacesByFullEquality() throws {
        let box = BoundingBox(minLon: -118.70, minLat: 34.05, maxLon: -118.60, maxLat: 34.10)
        XCTAssertEqual(try store().places(in: box), [
            Place(placeID: 710_486_223_536_647_933, osmType: "n", osmID: 7_399_702_863, cls: "town", name: "Topanga",
                  lonE7: -1_186_029_649, latE7: 340_897_000),
            Place(placeID: 2_347_648_572_508_305_698, osmType: "n", osmID: 11_230_094_718, cls: "trailhead",
                  name: "Piuma Traill", lonE7: -1_186_975_797, latE7: 340_734_358),
            Place(placeID: 3_938_057_443_308_025_104, osmType: "n", osmID: 5_645_100_420, cls: "viewpoint",
                  name: "David M. Brown Overlook", lonE7: -1_186_977_201, latE7: 340_739_400),
            Place(placeID: 6_182_464_451_037_593_740, osmType: "n", osmID: 11_834_354_104, cls: "trailhead",
                  name: "Dead Horse Trailhead", lonE7: -1_186_009_545, latE7: 340_945_910),
            Place(placeID: 7_978_713_287_531_671_284, osmType: "n", osmID: 12_073_372_395, cls: "viewpoint",
                  name: "Stunt Road Viewpoint", lonE7: -1_186_454_996, latE7: 340_813_302),
            PlaceStoreFallbackTests.saddlePeak,
        ])
    }

    func testTheWholeWorldBoxReturnsEveryPlaceOnceWithTheMeasuredClassCounts() throws {
        let places = try store().places(in: BoundingBox(minLon: -180, minLat: -90, maxLon: 180, maxLat: 90))
        XCTAssertEqual(places.count, 1334)
        XCTAssertEqual(Set(places.map(\.placeID)).count, 1334)
        XCTAssertEqual(places.map(\.placeID), places.map(\.placeID).sorted())
        XCTAssertEqual(Dictionary(grouping: places, by: \.cls).mapValues(\.count),
                       ["beach": 56, "cafe": 50, "garden": 150, "museum": 150, "park": 400, "peak": 187, "town": 104,
                        "trailhead": 99, "viewpoint": 102, "waterfall": 36])
    }

    func testABoxOverTheOceanReturnsNothing() throws {
        XCTAssertEqual(try store().places(in: BoundingBox(minLon: -125, minLat: 30, maxLon: -124, maxLat: 31)), [])
    }
}
#endif

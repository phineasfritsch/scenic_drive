#if canImport(GRDB)
import GRDB
import PlaceStore
import XCTest

/// The reader over a corpus the shipping builder made, every value by EXACT equality to the measured row.
final class PlaceStoreReadTests: XCTestCase {
    /// The typed literal and the corpus agree. Bumping either side alone turns this red: the corpus side
    /// through services/etl/etl/schema.py (the fixture is built, not committed), this side through the literal.
    func testSchemaVersionLiteralEqualsBuiltCorpus() throws {
        let corpus = try CorpusFixture.build()
        let stored = try DatabaseQueue(path: corpus.path).read { db in
            try String.fetchOne(db, sql: "SELECT value FROM meta WHERE key = 'schema_version'")
        }
        XCTAssertEqual(stored, "\(PlaceStore.schemaVersion)")
        XCTAssertEqual(PlaceStore.schemaVersion, 2)
    }

    func testMetaReadsBuiltCorpus() throws {
        let store = try PlaceStore(path: CorpusFixture.build().path)
        XCTAssertEqual(try store.meta(), CorpusMeta(
            schemaVersion: 2, minAppBuild: 1, region: "fixture", corpusVersion: "20260918T000000Z",
            builtAt: "2026-09-18T00:00:00Z", attribution: "© OpenStreetMap contributors · Protomaps"))
    }

    /// Way 107 bucket 4, the row quoted in the T-0175 Log (python sqlite3 over the same build).
    func testSegmentByIDReadsMeasuredRow() throws {
        let store = try PlaceStore(path: CorpusFixture.build().path)
        XCTAssertEqual(try store.segment(id: 3_003_480_930_389_769_752), Segment(
            segmentID: 3_003_480_930_389_769_752, wayID: 107, bucket: 4, offsetMM: 400_000, lengthMM: 100_000,
            minLonE7: -1_225_899_478, minLatE7: 379_707_600, maxLonE7: -1_225_889_382, maxLatE7: 379_711_245,
            midLonE7: -1_225_893_967, midLatE7: 379_710_216,
            geometry: [0x2A, 0x42, 0xEE, 0xB6, 0x0D, 0xEF, 0xA1, 0x16, 0xD5, 0x55, 0xEE, 0xB6, 0x00, 0xEC, 0xA1, 0x16,
                       0x3B, 0x68, 0xEE, 0xB6, 0x69, 0xE2, 0xA1, 0x16, 0x9A, 0x69, 0xEE, 0xB6, 0xD0, 0xE0, 0xA1, 0x16]))
    }

    func testSegmentByUnknownIDIsNil() throws {
        let store = try PlaceStore(path: CorpusFixture.build().path)
        XCTAssertNil(try store.segment(id: 1))
    }

    /// Box A around way 107's loop: exactly its seven segments, and nothing from ways 101-106 (lat <= 37.9501).
    func testBoundingBoxQuerySelectsWay107() throws {
        let corpus = try CorpusFixture.build()
        let ids = try PlaceStore(path: corpus.path).segmentIDs(
            in: BoundingBox(minLon: -122.595, minLat: 37.965, maxLon: -122.585, maxLat: 37.975))
        XCTAssertEqual(ids, [3_003_480_930_389_769_752, 3_003_482_029_901_397_963, 3_003_483_129_413_026_174,
                             3_003_485_328_436_282_596, 3_003_486_427_947_910_807, 3_003_487_527_459_539_018,
                             3_003_488_626_971_167_229])
        XCTAssertEqual(ids, try Self.e7Oracle(corpus, minLon: -1_225_950_000, minLat: 379_650_000,
                                              maxLon: -1_225_850_000, maxLat: 379_750_000))
    }

    /// Box B on way 101 (lat 37.90): its west edge -122.590 CUTS bucket 3 (lon -122.5909..-122.5897), so an
    /// intersection query returns buckets 0-3 and a containment query would return only 0-2.
    func testBoundingBoxQueryIsIntersectionNotContainment() throws {
        let corpus = try CorpusFixture.build()
        let ids = try PlaceStore(path: corpus.path).segmentIDs(
            in: BoundingBox(minLon: -122.590, minLat: 37.899, maxLon: -122.586, maxLat: 37.901))
        XCTAssertEqual(ids, [3_087_679_705_935_026_592, 3_087_680_805_446_654_803, 3_087_681_904_958_283_014,
                             3_087_683_004_469_911_225])
        XCTAssertEqual(ids, try Self.e7Oracle(corpus, minLon: -1_225_900_000, minLat: 378_990_000,
                                              maxLon: -1_225_860_000, maxLat: 379_010_000))
    }

    /// The recomputation: the same box, typed in e7 integers, over the `segments` TABLE's own columns - not
    /// the R*Tree the shipping query reads.
    static func e7Oracle(_ corpus: URL, minLon: Int, minLat: Int, maxLon: Int, maxLat: Int) throws -> [Int64] {
        try DatabaseQueue(path: corpus.path).read { db in
            try Int64.fetchAll(db, sql: """
                SELECT segment_id FROM segments WHERE max_lon_e7 >= ? AND min_lon_e7 <= ?
                AND max_lat_e7 >= ? AND min_lat_e7 <= ? ORDER BY segment_id
                """, arguments: [minLon, maxLon, minLat, maxLat])
        }
    }
}
#endif

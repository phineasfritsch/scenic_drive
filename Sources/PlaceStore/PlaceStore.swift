#if canImport(GRDB)
import Foundation
import GRDB

/// The device's reader for corpus.sqlite (services/etl/etl/schema.py), on plain SQL through GRDB.
///
/// `init(path:)` is the gate: it opens the file READ-ONLY and refuses it - before any caller reads a row -
/// unless it is a corpus (`application_id` "SCNC"), of the version this reader parses (`meta.schema_version`
/// == `schemaVersion`, the plan's OTA row), and finished (`meta.build_complete` == "1", written last by
/// CorpusWriter.finalize). Nothing here computes a number: geometry is returned as the stored bytes and box
/// queries pass degrees straight into SQL (T-0175 rulings R3, R5).
public final class PlaceStore: Sendable {
    /// The corpus schema this reader parses. P-PROD-05 holds it equal to services/etl/etl/schema.py and
    /// services/api/src/index.ts; PlaceStoreReadTests holds it equal to a corpus the shipping builder made.
    public static let schemaVersion: Int = 2

    /// `PRAGMA application_id` of every corpus: the ASCII bytes "SCNC" big-endian (schema.APPLICATION_ID).
    static let applicationID: Int = 0x5343_4E43

    private let queue: DatabaseQueue

    public init(path: String) throws {
        var configuration = Configuration()
        configuration.readonly = true
        let queue = try DatabaseQueue(path: path, configuration: configuration)
        try queue.read { db in
            let applicationID = try Int.fetchOne(db, sql: "PRAGMA application_id") ?? 0
            guard applicationID == Self.applicationID else {
                throw PlaceStoreError.notACorpus(applicationID: applicationID)
            }
            let version = try Self.metaValue(db, "schema_version")
            guard version == String(Self.schemaVersion) else {
                throw PlaceStoreError.schemaVersionMismatch(found: version, expected: Self.schemaVersion)
            }
            let complete = try Self.metaValue(db, "build_complete")
            guard complete == "1" else {
                throw PlaceStoreError.incompleteBuild(buildComplete: complete)
            }
        }
        self.queue = queue
    }

    public func meta() throws -> CorpusMeta {
        try queue.read { db in
            CorpusMeta(
                schemaVersion: try Self.metaInt(db, "schema_version"),
                minAppBuild: try Self.metaInt(db, "min_app_build"),
                region: try Self.metaValue(db, "region"),
                corpusVersion: try Self.metaValue(db, "corpus_version"),
                builtAt: try Self.metaValue(db, "built_at"),
                attribution: try Self.metaValue(db, "attribution"))
        }
    }

    /// One `segments` row by id, or nil when the corpus has no such segment.
    public func segment(id: Int64) throws -> Segment? {
        try queue.read { db in
            guard let row = try Row.fetchOne(db, sql: """
                SELECT segment_id, way_id, bucket, offset_mm, length_mm, min_lon_e7, min_lat_e7, max_lon_e7,
                       max_lat_e7, mid_lon_e7, mid_lat_e7, geometry
                FROM segments WHERE segment_id = ?
                """, arguments: [id]) else { return nil }
            let geometry: Data = row["geometry"]
            return Segment(
                segmentID: row["segment_id"], wayID: row["way_id"], bucket: row["bucket"],
                offsetMM: row["offset_mm"], lengthMM: row["length_mm"],
                minLonE7: row["min_lon_e7"], minLatE7: row["min_lat_e7"],
                maxLonE7: row["max_lon_e7"], maxLatE7: row["max_lat_e7"],
                midLonE7: row["mid_lon_e7"], midLatE7: row["mid_lat_e7"],
                geometry: [UInt8](geometry))
        }
    }

    /// Ids of every segment whose R*Tree box INTERSECTS `box`, ascending.
    public func segmentIDs(in box: BoundingBox) throws -> [Int64] {
        try queue.read { db in
            try Int64.fetchAll(db, sql: """
                SELECT id FROM segments_rtree
                WHERE max_lon >= ? AND min_lon <= ? AND max_lat >= ? AND min_lat <= ?
                ORDER BY id
                """, arguments: [box.minLon, box.maxLon, box.minLat, box.maxLat])
        }
    }

    private static func metaValue(_ db: Database, _ key: String) throws -> String {
        guard let value = try String.fetchOne(db, sql: "SELECT value FROM meta WHERE key = ?",
                                              arguments: [key]) else {
            throw PlaceStoreError.missingMeta(key: key)
        }
        return value
    }

    private static func metaInt(_ db: Database, _ key: String) throws -> Int {
        let value = try metaValue(db, key)
        guard let number = Int(value) else { throw PlaceStoreError.malformedMeta(key: key, value: value) }
        return number
    }
}
#endif

#if canImport(GRDB)
import Foundation
import PlaceStore
import Testing

/// T-0255's acceptance over a corpus the SHIPPING builder made (ruling R6): every segment's `vertices()` equals,
/// by exact equality, the ETL encoder's own quantisation of the coordinates it packed - recomputed in a separate
/// python process from the same extract by the shipping segmenter and `geom.to_e7`, never by unpacking the BLOB.
@Suite("Segment.vertices over the fixture corpus")
struct SegmentVerticesCorpusTests {
    /// Runs the ETL's segmenter over `extract` and returns {"way bucket": [[lon_e7, lat_e7], ...]}.
    static let oracleScript = """
        import sys
        from etl import geom
        from etl.extractway import load_extract
        from etl.segmenter import Segmenter
        _region, ways = load_extract(sys.argv[1])
        cutter = Segmenter()
        for way in ways:
            for seg in cutter.cut(way.way_id, list(way.coords)):
                print(seg.way_id, seg.bucket, *[v for lat, lon in seg.coords for v in (geom.to_e7(lon), geom.to_e7(lat))])
        """

    static func encoderVertices(extract: URL) throws -> [String: [[Int32]]] {
        let python = ProcessInfo.processInfo.environment["PYTHON"] ?? "python3"
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = [python, "-c", oracleScript, extract.path]
        process.currentDirectoryURL = CorpusFixture.etl
        let pipe = Pipe()
        process.standardOutput = pipe
        try process.run()
        let output = String(decoding: pipe.fileHandleForReading.readDataToEndOfFile(), as: UTF8.self)
        process.waitUntilExit()
        try #require(process.terminationStatus == 0, "the ETL segmenter oracle exited \(process.terminationStatus)")
        var out: [String: [[Int32]]] = [:]
        for line in output.split(separator: "\n") {
            let fields = line.split(separator: " ").map(String.init)
            let numbers = try fields.dropFirst(2).map { try #require(Int32($0), "not an Int32: \($0)") }
            try #require(numbers.count % 2 == 0, "odd e7 count on line: \(line)")
            out["\(fields[0]) \(fields[1])"] = stride(from: 0, to: numbers.count, by: 2).map {
                [numbers[$0], numbers[$0 + 1]]
            }
        }
        return out
    }

    @Test("every fixture segment's vertices() equal the ETL encoder's e7 pairs, all 79, by exact equality")
    func everySegmentEqualsEncoder() throws {
        let store = try PlaceStore(path: CorpusFixture.build().path)
        let oracle = try Self.encoderVertices(extract: CorpusFixture.extract)
        let ids = try store.segmentIDs(in: BoundingBox(minLon: -180, minLat: -90, maxLon: 180, maxLat: 90))
        #expect(ids.count == 79)
        #expect(oracle.count == 79)
        var decoded: [String: [[Int32]]] = [:]
        for id in ids {
            let segment = try #require(try store.segment(id: id))
            decoded["\(segment.wayID) \(segment.bucket)"] = try segment.vertices().map { [$0.lonE7, $0.latE7] }
        }
        #expect(decoded == oracle)
        #expect(decoded["107 4"] == [[-1_225_899_478, 379_711_245], [-1_225_894_443, 379_710_464],
                                    [-1_225_889_733, 379_708_009], [-1_225_889_382, 379_707_600]])
    }
}
#endif

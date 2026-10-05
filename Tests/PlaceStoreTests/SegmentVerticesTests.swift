import PlaceStore
import Testing

/// `Segment.vertices()`, the shipping decoder, over every bound of T-0255 ruling R4. Not GRDB-gated (R5): this
/// table runs on every toolchain. Accepted rows compare the WHOLE vertex list as Int32 literals - never through
/// `SegmentVertex.init`, so a swapped field there is seen - and refused rows compare the whole typed error.
@Suite("Segment.vertices")
struct SegmentVerticesTests {
    static let lonMax: Int32 = 1_800_000_000
    static let latMax: Int32 = 900_000_000

    /// The test's own little-endian encoding: the platform's byte image of `littleEndian`, not shift arithmetic.
    static func blob(_ pairs: [[Int32]]) -> [UInt8] {
        pairs.flatMap { pair in pair.flatMap { value in withUnsafeBytes(of: value.littleEndian) { Array($0) } } }
    }

    static func segment(_ geometry: [UInt8]) -> Segment {
        Segment(segmentID: 1, wayID: 1, bucket: 0, offsetMM: 0, lengthMM: 1, minLonE7: 0, minLatE7: 0,
                maxLonE7: 0, maxLatE7: 0, midLonE7: 0, midLatE7: 0, geometry: geometry)
    }

    static func decoded(_ geometry: [UInt8]) throws -> [[Int32]] {
        try segment(geometry).vertices().map { [$0.lonE7, $0.latE7] }
    }

    static func refusal(_ geometry: [UInt8]) -> SegmentGeometryError? {
        do {
            _ = try segment(geometry).vertices()
            return nil
        } catch let error as SegmentGeometryError {
            return error
        } catch {
            return nil
        }
    }

    @Test("accepts the measured row of way 107 bucket 4, byte for byte, as the ETL wrote it")
    func measuredRow() throws {
        let bytes: [UInt8] = [0x2A, 0x42, 0xEE, 0xB6, 0x0D, 0xEF, 0xA1, 0x16, 0xD5, 0x55, 0xEE, 0xB6, 0x00, 0xEC, 0xA1, 0x16,
                              0x3B, 0x68, 0xEE, 0xB6, 0x69, 0xE2, 0xA1, 0x16, 0x9A, 0x69, 0xEE, 0xB6, 0xD0, 0xE0, 0xA1, 0x16]
        #expect(try Self.decoded(bytes) == [[-1_225_899_478, 379_711_245], [-1_225_894_443, 379_710_464],
                                            [-1_225_889_733, 379_708_009], [-1_225_889_382, 379_707_600]])
    }

    @Test("accepts every byte position and sign: a hand-typed blob with four distinct bytes per int32")
    func handTypedBytes() throws {
        let bytes: [UInt8] = [0x4D, 0x3C, 0x2B, 0x1A, 0x3C, 0x2D, 0x1E, 0x0F,
                              0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x00, 0x00,
                              0x04, 0x03, 0x02, 0x9A, 0xF8, 0xF8, 0xF9, 0xFA]
        #expect(try Self.decoded(bytes) == [[0x1A2B_3C4D, 0x0F1E_2D3C], [-1, 1], [-1_711_144_188, -84_281_096]])
    }

    @Test("accepts every exact bound and the two-vertex minimum, whole result compared")
    func exactBounds() throws {
        let rows: [[[Int32]]] = [
            [[Self.lonMax, Self.latMax], [-Self.lonMax, -Self.latMax]],
            [[-Self.lonMax, Self.latMax], [Self.lonMax, -Self.latMax]],
            [[0, 0], [-1, 1]],
            [[0x1A2B_3C4D, 0x0F1E_2D3C], [-0x1A2B_3C4D, -0x0F1E_2D3C], [0x0102_0304, -0x0506_0708]],
            [[Self.lonMax - 1, Self.latMax - 1], [-Self.lonMax + 1, -Self.latMax + 1], [7, -7], [-9, 9]],
        ]
        for row in rows {
            #expect(try Self.decoded(Self.blob(row)) == row)
        }
    }

    @Test("a blob cut by one whole vertex is a valid shorter polyline (R3): 24 bytes cut to 16 decode as two")
    func wholeVertexTruncation() throws {
        let three = Self.blob([[10, 20], [30, 40], [50, 60]])
        #expect(three.count == 24)
        #expect(try Self.decoded(Array(three.prefix(16))) == [[10, 20], [30, 40]])
    }

    @Test("refuses a byte count that is not whole vertices: 1, 7, 9, 15, 17, 23")
    func partialVertex() {
        let full = Self.blob([[1, 2], [3, 4], [5, 6]])
        for count in [1, 7, 9, 15, 17, 23] {
            #expect(Self.refusal(Array(full.prefix(count))) == .partialVertex(byteCount: count))
        }
    }

    static func outcome(_ geometry: [UInt8]) -> Result<[[Int32]], SegmentGeometryError>? {
        do {
            return .success(try decoded(geometry))
        } catch let error as SegmentGeometryError {
            return .failure(error)
        } catch {
            return nil
        }
    }

    static func cut(_ count: Int) -> Result<[[Int32]], SegmentGeometryError> {
        .failure(.partialVertex(byteCount: count))
    }

    /// rv1-t0255 B1: every count 0..40 - each residue mod 8 five times over - so no modulus, threshold or minimum
    /// other than the shipping one agrees with all 41 rows. Each row is a literal outcome, never recomputed.
    @Test("every byte count 0 through 40, every residue mod 8: the typed error or the whole decoded list")
    func everyByteCount() {
        let full = Self.blob([[11, -12], [21, -22], [31, -32], [41, -42], [51, -52]])
        let rows: [(Int, Result<[[Int32]], SegmentGeometryError>)] = [
            (0, .failure(.tooFewVertices(count: 0))), (1, Self.cut(1)), (2, Self.cut(2)), (3, Self.cut(3)),
            (4, Self.cut(4)), (5, Self.cut(5)), (6, Self.cut(6)), (7, Self.cut(7)),
            (8, .failure(.tooFewVertices(count: 1))), (9, Self.cut(9)), (10, Self.cut(10)), (11, Self.cut(11)),
            (12, Self.cut(12)), (13, Self.cut(13)), (14, Self.cut(14)), (15, Self.cut(15)),
            (16, .success([[11, -12], [21, -22]])), (17, Self.cut(17)), (18, Self.cut(18)), (19, Self.cut(19)),
            (20, Self.cut(20)), (21, Self.cut(21)), (22, Self.cut(22)), (23, Self.cut(23)),
            (24, .success([[11, -12], [21, -22], [31, -32]])), (25, Self.cut(25)), (26, Self.cut(26)),
            (27, Self.cut(27)), (28, Self.cut(28)), (29, Self.cut(29)), (30, Self.cut(30)), (31, Self.cut(31)),
            (32, .success([[11, -12], [21, -22], [31, -32], [41, -42]])), (33, Self.cut(33)), (34, Self.cut(34)),
            (35, Self.cut(35)), (36, Self.cut(36)), (37, Self.cut(37)), (38, Self.cut(38)), (39, Self.cut(39)),
            (40, .success([[11, -12], [21, -22], [31, -32], [41, -42], [51, -52]])),
        ]
        #expect(full.count == 40)
        #expect(rows.map { $0.0 } == Array(0...40))
        for (count, expected) in rows {
            #expect(Self.outcome(Array(full.prefix(count))) == expected, "byte count \(count)")
        }
    }

    @Test("refuses fewer than two vertices: 0 bytes and 8 bytes")
    func tooFewVertices() {
        #expect(Self.refusal([]) == .tooFewVertices(count: 0))
        #expect(Self.refusal(Self.blob([[1, 2]])) == .tooFewVertices(count: 1))
    }

    @Test("refuses a longitude one past either bound, and Int32.min/max, at the vertex that holds it")
    func longitudeOutOfRange() {
        let rows: [([[Int32]], SegmentGeometryError)] = [
            ([[Self.lonMax + 1, 0], [0, 0]], .longitudeOutOfRange(index: 0, lonE7: Self.lonMax + 1)),
            ([[0, 0], [-Self.lonMax - 1, 0]], .longitudeOutOfRange(index: 1, lonE7: -Self.lonMax - 1)),
            ([[0, 0], [0, 0], [Int32.max, 0]], .longitudeOutOfRange(index: 2, lonE7: Int32.max)),
            ([[Int32.min, 0], [0, 0]], .longitudeOutOfRange(index: 0, lonE7: Int32.min)),
        ]
        for (pairs, expected) in rows {
            #expect(Self.refusal(Self.blob(pairs)) == expected)
        }
    }

    @Test("refuses a latitude one past either bound, and Int32.min/max, at the vertex that holds it")
    func latitudeOutOfRange() {
        let rows: [([[Int32]], SegmentGeometryError)] = [
            ([[0, Self.latMax + 1], [0, 0]], .latitudeOutOfRange(index: 0, latE7: Self.latMax + 1)),
            ([[0, 0], [0, -Self.latMax - 1]], .latitudeOutOfRange(index: 1, latE7: -Self.latMax - 1)),
            ([[0, 0], [0, 0], [0, Int32.max]], .latitudeOutOfRange(index: 2, latE7: Int32.max)),
            ([[0, Int32.min], [0, 0]], .latitudeOutOfRange(index: 0, latE7: Int32.min)),
        ]
        for (pairs, expected) in rows {
            #expect(Self.refusal(Self.blob(pairs)) == expected)
        }
    }

    @Test("check order: byte count, then vertex count, then each vertex lon before lat, first offender wins")
    func checkOrder() {
        let bad = Self.lonMax + 1
        #expect(Self.refusal(Self.blob([[bad, 0]]) + [0]) == .partialVertex(byteCount: 9))
        #expect(Self.refusal(Self.blob([[bad, bad]])) == .tooFewVertices(count: 1))
        #expect(Self.refusal(Self.blob([[bad, bad], [0, 0]])) == .longitudeOutOfRange(index: 0, lonE7: bad))
        #expect(Self.refusal(Self.blob([[0, bad], [bad, 0]])) == .latitudeOutOfRange(index: 0, latE7: bad))
    }
}

#if canImport(GRDB)
import Foundation
import GRDB
@testable import PlaceStore
import Testing

/// T-0343 R3: the learned corridor slots in the user store. Every write is checked by FULL equality of the whole
/// table `list()` answers; a second store on the same file is the next launch; every bound the learner restores by
/// is held by the table too, one step either side, and a refused write leaves the table as it was.
@Suite("CorridorRatioStore")
struct CorridorRatioStoreTests {
    static func path() throws -> String {
        try CorpusFixture.scratch().appendingPathComponent("user.sqlite").path
    }

    static let good = CorridorRatioRecord(cell: 617_700_169_958_293_503, hour: 8, ratio: 0.8, samples: 3)
    static let neighbour = CorridorRatioRecord(cell: 617_700_169_958_293_504, hour: 9, ratio: 0.6, samples: 7)

    static func with(hour: Int? = nil, ratio: Double? = nil, samples: Int? = nil) -> CorridorRatioRecord {
        CorridorRatioRecord(cell: good.cell, hour: hour ?? good.hour, ratio: ratio ?? good.ratio,
                            samples: samples ?? good.samples)
    }

    @Test("records round-trip whole, by stored cell then hour; a second store on the file reads the same; a write replaces all")
    func roundTripAcrossLaunches() throws {
        let path = try Self.path()
        let store = try CorridorRatioStore(path: path)
        #expect(try store.list() == [])
        let high = UInt64(Int64.max) + 1
        let first = [CorridorRatioRecord(cell: 1, hour: 167, ratio: 1.0, samples: 1),
                     CorridorRatioRecord(cell: UInt64(Int64.max), hour: 0, ratio: 0.3, samples: Int.max),
                     CorridorRatioRecord(cell: UInt64.max, hour: 5, ratio: 0.55, samples: 2),
                     CorridorRatioRecord(cell: high, hour: 5, ratio: 0.45, samples: 9),
                     CorridorRatioRecord(cell: 1, hour: 3, ratio: 0.7, samples: 4)]
        // Stored as the bit pattern: the two cells above Int64.max sort first, as the negative numbers they are.
        let expected = [first[3], first[2], first[4], first[0], first[1]]
        #expect(try store.replaceAll(with: first) == expected)
        #expect(try CorridorRatioStore(path: path).list() == expected, "the next launch")
        #expect(try store.replaceAll(with: [Self.good]) == [Self.good], "a write replaces the whole table")
        #expect(try CorridorRatioStore(path: path).list() == [Self.good])
        #expect(try store.replaceAll(with: []) == [])
    }

    /// (name, the variant, whether the table takes it) - the same bounds as the learner's restore.
    static let variants: [(String, CorridorRatioRecord, Bool)] = [
        ("hour -1", with(hour: -1), false), ("hour 0", with(hour: 0), true), ("hour 167", with(hour: 167), true),
        ("hour 168", with(hour: 168), false), ("hour Int.min", with(hour: Int.min), false),
        ("hour Int.max", with(hour: Int.max), false),
        ("ratio one ulp below 0.3", with(ratio: 0.3.nextDown), false), ("ratio 0.3", with(ratio: 0.3), true),
        ("ratio 1.0", with(ratio: 1.0), true), ("ratio one ulp above 1.0", with(ratio: 1.0.nextUp), false),
        ("ratio NaN", with(ratio: .nan), false), ("ratio -infinity", with(ratio: -.infinity), false),
        ("ratio +infinity", with(ratio: .infinity), false), ("ratio 0", with(ratio: 0), false),
        ("samples Int.min", with(samples: Int.min), false), ("samples 0", with(samples: 0), false),
        ("samples 1", with(samples: 1), true), ("samples Int.max", with(samples: Int.max), true),
    ]

    @Test("every bound of hour, ratio and samples one step either side; a refused write or a repeated slot keeps the table")
    func boundTable() throws {
        let store = try CorridorRatioStore(path: try Self.path())
        let kept = [Self.neighbour]
        for (name, record, accepted) in Self.variants {
            #expect(try store.replaceAll(with: kept) == kept)
            let written = [Self.neighbour, record]
            if accepted {
                #expect(try store.replaceAll(with: written) == [record, Self.neighbour], "\(name)")
            } else {
                #expect(throws: DatabaseError.self, "\(name)") { try store.replaceAll(with: written) }
                #expect(try store.list() == kept, "\(name): the table is unchanged")
            }
        }
        #expect(try store.replaceAll(with: kept) == kept)
        #expect(throws: DatabaseError.self) { try store.replaceAll(with: [Self.good, Self.with(ratio: 0.5)]) }
        #expect(try store.list() == kept, "a repeated slot keeps the table")
        #expect(Set(Self.variants.map(\.2)) == [true, false])
    }
}
#endif

import Foundation
import Testing
@testable import ScenicKit

/// T-0343 R2: the learner a previous launch kept comes back only whole - every bound of every field, one step either
/// side, alone and beside a good row; the answer compared WHOLE to the slots written out per row.
@Suite("a kept learner restores only when every row is in bounds (T-0343)") struct LearnedSpeedsRestoreTests {
    static let utc = TimeZone(secondsFromGMT: 0)!
    /// The row each variant changes one field of, and a good neighbour in another cell.
    static let good = CorridorSlotRow(cell: 617_700_169_958_293_503, hour: 8, ratio: 0.8, samples: 3)
    static let neighbour = CorridorSlotRow(cell: 617_700_169_958_293_504, hour: 9, ratio: 0.6, samples: 7)

    static func with(hour: Int? = nil, ratio: Double? = nil, samples: Int? = nil) -> CorridorSlotRow {
        CorridorSlotRow(cell: good.cell, hour: hour ?? good.hour, ratio: ratio ?? good.ratio,
                        samples: samples ?? good.samples)
    }

    /// The slots a list of accepted rows must restore to, built without the initializer under test.
    static func slots(_ rows: [CorridorSlotRow]) -> [CorridorSlot: CorridorRatio] {
        Dictionary(uniqueKeysWithValues: rows.map { row in
            (CorridorSlot(cell: CorridorCell(index: row.cell), hour: HourOfWeek(row.hour)!),
             CorridorRatio(ratio: row.ratio, samples: row.samples))
        })
    }

    /// (name, the variant row, whether it is accepted) - every bound of hour, ratio and samples.
    static let variants: [(String, CorridorSlotRow, Bool)] = [
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

    @Test("restore: every bound of hour, ratio and samples, alone and beside a good row; a repeated slot refuses all")
    func restoreBounds() {
        #expect(LearnedCorridorSpeeds(timeZone: Self.utc, restoring: []) == LearnedCorridorSpeeds(timeZone: Self.utc))
        for (name, row, accepted) in Self.variants {
            for context in [[row], [Self.neighbour, row], [row, Self.neighbour]] {
                let restored = LearnedCorridorSpeeds(timeZone: Self.utc, restoring: context)
                #expect(restored?.slots == (accepted ? Self.slots(context) : nil), "\(name), \(context.count) rows")
                #expect(restored.map { $0.timeZone == Self.utc } ?? !accepted, "\(name): the zone")
            }
        }
        // The same cell and hour twice refuses the whole store, whatever the second row says; another hour or
        // another cell is a slot of its own.
        let repeats: [(String, [CorridorSlotRow], [CorridorSlotRow]?)] = [
            ("the same row twice", [Self.good, Self.good], nil),
            ("the same slot, another ratio", [Self.good, Self.with(ratio: 0.5)], nil),
            ("the same slot after a neighbour", [Self.good, Self.neighbour, Self.with(samples: 9)], nil),
            ("the same cell, another hour", [Self.good, Self.with(hour: 9)], [Self.good, Self.with(hour: 9)]),
            ("another cell, the same hour", [Self.good, CorridorSlotRow(cell: 1, hour: 8, ratio: 0.8, samples: 3)],
             [Self.good, CorridorSlotRow(cell: 1, hour: 8, ratio: 0.8, samples: 3)]),
        ]
        for (name, rows, kept) in repeats {
            #expect(LearnedCorridorSpeeds(timeZone: Self.utc, restoring: rows)?.slots == kept.map(Self.slots), "\(name)")
        }
        // Meta: every field meets a refused and an accepted value, so no row of the table is a no-op.
        #expect(Set(Self.variants.map(\.2)) == [true, false])
    }

    @Test("rows answers every slot by cell then hour, and restoring them equals the learner that wrote them")
    func rowsRoundTrip() {
        var speeds = LearnedCorridorSpeeds(timeZone: Self.utc)
        let teach: [(UInt64, Int, Double)] = [(5, 9, 0.5), (3, 167, 0.9), (5, 0, 1.0), (3, 8, 0.4), (5, 9, 0.5)]
        for (cell, hour, ratio) in teach {
            speeds.record(cell: CorridorCell(index: cell), hourOfWeek: HourOfWeek(hour)!, actualSeconds: 100,
                          freeFlowSeconds: 100 * ratio)
        }
        #expect(speeds.rows == [
            CorridorSlotRow(cell: 3, hour: 8, ratio: 0.4, samples: 1),
            CorridorSlotRow(cell: 3, hour: 167, ratio: 0.9, samples: 1),
            CorridorSlotRow(cell: 5, hour: 0, ratio: 1.0, samples: 1),
            CorridorSlotRow(cell: 5, hour: 9, ratio: 0.5, samples: 2),
        ])
        #expect(LearnedCorridorSpeeds(timeZone: Self.utc, restoring: speeds.rows) == speeds)
        #expect(LearnedCorridorSpeeds(timeZone: Self.utc).rows == [])
    }
}

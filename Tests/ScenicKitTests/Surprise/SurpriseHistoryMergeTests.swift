import Foundation
@testable import ScenicKit
import Testing

/// T-0307 acceptance 3 (R5, R7): the no-repeat history is the device's history united with the ledger's 90 days,
/// deduplicated by place id (latest day kept), ordered by day then id; `ledger: nil` (no session) is the device
/// history untouched. Every row compares the WHOLE merged history and the WHOLE pick to a hand-built expectation.
@Suite("SurpriseHistoryMergeTests") struct SurpriseHistoryMergeTests {
    static func day(_ m: Int, _ d: Int) -> CivilDate { CivilDate(year: 2026, month: m, day: d) }

    static func shown(_ id: String, _ category: SurpriseCategory, _ date: CivilDate) -> SurpriseHistory.Shown {
        .init(candidateId: id, category: category, corridor: "pch", date: date)
    }

    static let feedback = [SurpriseFeedback(candidateId: "malibu-03", category: .beach, roundTripMinutes: 60,
                                            date: day(6, 20), reason: .beenThere)]
    /// Out of order, and malibu-00 twice: only `nil` keeps it exactly so.
    static let device = SurpriseHistory(shown: [shown("malibu-00", .park, day(6, 10)),
                                                shown("malibu-01", .trailhead, day(5, 1)),
                                                shown("malibu-00", .park, day(4, 1))], feedback: feedback)

    struct Row: Sendable {
        let name: String
        let device: SurpriseHistory
        let ledger: [SurpriseLedgerPlace]?
        let expected: SurpriseHistory
    }

    static let rows: [Row] = [
        Row(name: "no session", device: device, ledger: nil, expected: device),
        Row(name: "empty ledger", device: device, ledger: [],
            expected: SurpriseHistory(shown: [shown("malibu-01", .trailhead, day(5, 1)),
                                              shown("malibu-00", .park, day(6, 10))], feedback: feedback)),
        Row(name: "ledger overlapping device", device: device,
            ledger: [.init(candidateId: "malibu-00", date: day(6, 15)), .init(candidateId: "malibu-01", date: day(4, 20)),
                     .init(candidateId: "malibu-02", date: day(3, 30)), .init(candidateId: "nowhere-9", date: day(6, 1))],
            expected: SurpriseHistory(shown: [shown("malibu-02", .viewpoint, day(3, 30)),
                                              shown("malibu-01", .trailhead, day(5, 1)),
                                              shown("malibu-00", .park, day(6, 15))], feedback: feedback)),
        Row(name: "ledger only", device: SurpriseHistory(feedback: feedback),
            ledger: [.init(candidateId: "malibu-01", date: day(6, 19)), .init(candidateId: "malibu-00", date: day(6, 19))],
            expected: SurpriseHistory(shown: [shown("malibu-00", .park, day(6, 19)),
                                              shown("malibu-01", .trailhead, day(6, 19))], feedback: feedback)),
    ]

    @Test("The merged history is exactly the expected one, whatever the ledger's order",
          arguments: rows.indices)
    func mergedHistory(_ i: Int) throws {
        let row = Self.rows[i]
        let candidates = try SurpriseFixture.candidates()
        let merged = SurpriseHistoryMerge.merged(device: row.device, ledger: row.ledger, candidates: candidates)
        #expect(merged == row.expected, "\(row.name)")
        let reversed = SurpriseHistoryMerge.merged(device: row.device, ledger: row.ledger.map { Array($0.reversed()) },
                                                   candidates: candidates)
        #expect(reversed == row.expected, "\(row.name) reversed")
    }

    @Test("The pick over the merged history is the pick over the expected history, seed for seed",
          arguments: rows.indices)
    func pickReproducible(_ i: Int) throws {
        let row = Self.rows[i]
        let merged = SurpriseHistoryMerge.merged(device: row.device, ledger: row.ledger,
                                                 candidates: try SurpriseFixture.candidates())
        #expect(try SurpriseFixture.ids(count: 60, history: merged)
                == SurpriseFixture.ids(count: 60, history: row.expected), "\(row.name)")
    }

    @Test("A ledger place shown 89 days ago is never picked; 90 days ago it is picked again")
    func ninetyDays() throws {
        let free = try SurpriseFixture.ids()
        let target = try #require(Dictionary(grouping: free.filter { $0 != "nil" }, by: { $0 })
            .max { ($0.value.count, $1.key) < ($1.value.count, $0.key) }?.key)
        let candidates = try SurpriseFixture.candidates()
        func ids(daysAgo: Int) throws -> [String] {
            let date = CivilDate(year: 2026, month: 3, day: 22 + (90 - daysAgo))   // 2026-06-20 less daysAgo
            let merged = SurpriseHistoryMerge.merged(device: SurpriseHistory(),
                                                     ledger: [.init(candidateId: target, date: date)],
                                                     candidates: candidates)
            return try SurpriseFixture.ids(history: merged)
        }
        #expect(try !ids(daysAgo: 89).contains(target))
        #expect(try ids(daysAgo: 90).contains(target))
    }
}

import Foundation
import Testing
@testable import ScenicKit

/// T-0283: the Surprise card's whole chain over the bundled LA corpus. Every place row of
/// apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite (Tests/Fixtures/surprise/corpus.tsv, written read-only by
/// corpus_measure.py --write) goes through `SurprisePlaceMapping.candidate` and `SurpriseOfflineReach.reach` from
/// Westwood - what SurpriseDeck runs - into `Surprise.pick`, and the picks for seeds 0..99 are compared by full
/// equality to the Python oracle's (corpus_sequences.tsv), which computes the prior, the reach and the time-fit itself.
@Suite("Surprise over the LA corpus")
struct SurpriseCorpusFitTests {
    static let dials = [30, 60, 90, 120]
    static let context = SurpriseContext(userId: "on-device", date: CivilDate(year: 2026, month: 10, day: 6),
                                         departureMinute: 600, utcOffsetMinutes: -420, redFlag: false)

    /// Each corpus row as the card maps it, and its class as the corpus names it.
    static func candidates() throws -> [(SurpriseCandidate, String)] {
        try SurpriseFixture.file("corpus.tsv").map { f in
            let candidate = try #require(SurprisePlaceMapping.candidate(placeID: Int64(f[0])!, cls: f[1], name: f[2],
                                                                        lonE7: Int64(f[3])!, latE7: Int64(f[4])!))
            return (candidate, f[1])
        }
    }

    /// The card's picks for seeds 0..<count at this dial, with each pick's round trip.
    static func picks(dial: Int, count: Int = 100) throws -> [SurprisePick] {
        let candidates = try candidates().map(\.0)
        let reach = SurpriseOfflineReach.reach(from: SurpriseOfflineReach.origin, to: candidates, budgetMinutes: dial)
        return try (0..<UInt64(count)).map { seed in
            try #require(Surprise.pick(candidates: candidates, reach: reach, history: SurpriseHistory(),
                                       context: context, seed: seed))
        }
    }

    @Test("the card's picks for seeds 0..99 at dials 30, 60, 90 and 120 equal the oracle's, by full equality")
    func theCorpusPicksEqualTheOracle() throws {
        #expect(try Self.candidates().count == 1334)
        let oracle = try SurpriseFixture.file("corpus_sequences.tsv")
        for dial in Self.dials {
            let expected = oracle.filter { $0[0] == String(dial) }.map { $0[2] }
            #expect(expected.count == (dial == 30 ? 74 : 100))
            let got = try Self.picks(dial: dial, count: expected.count).map(\.candidateId)
            #expect(got == expected, "dial \(dial)")
        }
    }

    @Test("at a 120-min dial the picks for seeds 0..99 land inside the dial, not at its edge, and mostly scenery")
    func theTwoHourPicksLandInsideTheDial() throws {
        let picks = try Self.picks(dial: 120)
        let fractions = picks.map { Double($0.reason.roundTripMinutes) / 120 }.sorted()
        #expect(picks.filter { $0.reason.roundTripMinutes == 120 }.isEmpty)
        #expect(fractions.filter { $0 >= 0.8 }.count <= 25)
        #expect(fractions[50] >= 0.6 && fractions[50] <= 0.8)
        let classes = Dictionary(try Self.candidates().map { ($0.0.id, $0.1) }, uniquingKeysWith: { a, _ in a })
        let scenic: Set<String> = ["viewpoint", "peak", "waterfall", "beach", "trailhead", "garden"]
        #expect(picks.filter { scenic.contains(classes[$0.candidateId] ?? "") }.count >= 70)
        #expect(picks.filter { classes[$0.candidateId] == "cafe" }.count <= 5)
        #expect(Set(picks.map(\.candidateId)).count >= 90)
    }
}

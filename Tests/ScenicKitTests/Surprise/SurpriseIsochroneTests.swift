import Foundation
import Testing
@testable import ScenicKit

/// T-0263 R6: Surprise.pick driven end-to-end from a decoded /isochrone body. Tests/Fixtures/t0263/la-reach.json is a
/// 180-minute body of six nested boxes over T-0253's candidates (Tests/Fixtures/surprise/candidates.tsv), with a hole
/// in the 30-minute bucket over griffith-09; the ten ojai places lie west of every box. Its histogram was counted
/// independently of ScenicKit, by make-fixture.py's geometry, before this suite first ran.
@Suite("Surprise from an isochrone body")
struct SurpriseIsochroneTests {
    static let ojai = (0...9).map { "ojai-0\($0)" }

    static func laReach() throws -> SurpriseIsochrone {
        try SurpriseIsochrone.decode(try SurpriseReachParityTests.data("la-reach.json"))
    }

    /// The pick for each of 300 consecutive seeds - the whole eligible list (T-0253 R5).
    static func picks(_ reach: SurpriseReach) throws -> [SurprisePick?] {
        let candidates = try SurpriseFixture.candidates()
        return (0..<UInt64(300)).map { seed in
            Surprise.pick(candidates: candidates, reach: reach, history: SurpriseHistory(),
                          context: SurpriseFixture.context(), seed: seed)
        }
    }

    @Test("a candidate outside every isochrone bucket is never picked: the ten ojai places, which T-0253's reach picks")
    func outsideEveryBucketIsNeverPicked() throws {
        let candidates = try SurpriseFixture.candidates()
        let reach = try Self.laReach().reach(for: candidates)
        #expect(candidates.filter { reach.roundTripMinutes[$0.id] == nil }.map(\.id) == Self.ojai)
        let picked = Set(try Self.picks(reach).compactMap { $0?.candidateId })
        #expect(picked.count >= 90)
        #expect(picked.isDisjoint(with: Self.ojai))
        #expect(!Set(try SurpriseFixture.ids()).isDisjoint(with: Self.ojai))
    }

    @Test("the decoded reach is the dial and each smallest bucket's round trip, and those minutes reach SurpriseReason")
    func theBucketMinutesReachTheReason() throws {
        let isochrone = try Self.laReach()
        let candidates = try SurpriseFixture.candidates()
        let reach = isochrone.reach(for: candidates)
        #expect(reach.budgetMinutes == 180)
        let histogram = Dictionary(grouping: candidates.map { reach.roundTripMinutes[$0.id] ?? 0 }, by: { $0 })
            .mapValues(\.count)
        #expect(histogram == [30: 16, 60: 15, 90: 26, 120: 19, 150: 31, 180: 19, 0: 10])
        #expect(["griffith-09", "w-dark-early", "pv-02", "malibu-05", "crest-05"].map { reach.roundTripMinutes[$0] }
                == [90, 30, 180, 150, 90])
        let byId = Dictionary(uniqueKeysWithValues: candidates.map { ($0.id, $0) })
        let picks = try Self.picks(reach).compactMap { $0 }
        #expect(picks.count == 300)
        let wrong = picks.filter { pick in
            pick.reason.roundTripMinutes != byId[pick.candidateId].flatMap { isochrone.roundTripMinutes(at: $0.coordinate) }
        }
        #expect(wrong.map(\.candidateId) == [])
        #expect(Set(picks.map(\.reason.roundTripMinutes)) == [30, 60, 90, 120, 150, 180])
    }

    @Test("a body that is not T-0262's shape does not decode: a MultiPolygon, a one-number position, no round trip")
    func aMalformedBodyDoesNotDecode() throws {
        let good = #"{"minutes":60,"buckets":[{"minutes":15,"round_trip_minutes":30,"polygon":{"type":"Polygon","#
            + #""coordinates":[[[-118.4,34.0],[-118.3,34.0],[-118.3,34.1],[-118.4,34.0]]]}}]}"#
        let ring: [[Double]] = [[-118.4, 34.0], [-118.3, 34.0], [-118.3, 34.1], [-118.4, 34.0]]
        #expect(try SurpriseIsochrone.decode(Data(good.utf8))
                == SurpriseIsochrone(minutes: 60, buckets: [
                    SurpriseIsochroneBucket(minutes: 15, roundTripMinutes: 30,
                                            polygon: SurpriseIsochronePolygon(type: "Polygon", coordinates: [ring])),
                ]))
        let bad = [good.replacingOccurrences(of: #""Polygon""#, with: #""MultiPolygon""#),
                   good.replacingOccurrences(of: "[-118.3,34.1]", with: "[-118.3]"),
                   good.replacingOccurrences(of: #""round_trip_minutes":30,"#, with: "")]
        for body in bad {
            #expect(body != good)
            #expect(throws: PlanFailure.self) { try SurpriseIsochrone.decode(Data(body.utf8)) }
        }
    }
}

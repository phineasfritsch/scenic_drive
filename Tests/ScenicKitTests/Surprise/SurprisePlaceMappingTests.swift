import Foundation
import Testing
@testable import ScenicKit

/// T-0273 R3: a corpus row (PlaceStore's Place, as primitives - ScenicKit never imports PlaceStore) becomes a
/// SurpriseCandidate through `SurprisePlaceMapping.candidate`, the entry point the Surprise card calls. Every
/// expectation is a whole SurpriseCandidate typed from the ruled table, never derived from the module's own table.
@Suite("Surprise place mapping")
struct SurprisePlaceMappingTests {
    /// Saddle Peak's committed row in apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite (T-0270's Log).
    static let saddleID: Int64 = 8_789_912_370_140_821_739
    static let saddleLonE7: Int64 = -1_186_550_579
    static let saddleLatE7: Int64 = 340_780_264

    struct Row: Sendable, CustomStringConvertible {
        let cls: String
        let category: SurpriseCategory
        let dwell: Int
        let opens: Int?
        let closes: Int?
        let hook: String
        var description: String { cls }
    }

    /// The ruled class table (R3), typed here a second time on purpose.
    static let rows: [Row] = [
        Row(cls: "viewpoint", category: .viewpoint, dwell: 20, opens: nil, closes: nil,
            hook: "Pull over for a long view."),
        Row(cls: "peak", category: .viewpoint, dwell: 45, opens: nil, closes: nil,
            hook: "A high point with the basin below."),
        Row(cls: "waterfall", category: .trailhead, dwell: 60, opens: nil, closes: nil,
            hook: "A waterfall, if the season's been wet."),
        Row(cls: "beach", category: .beach, dwell: 60, opens: nil, closes: nil,
            hook: "Sand underfoot and a long horizon."),
        Row(cls: "trailhead", category: .trailhead, dwell: 60, opens: nil, closes: nil,
            hook: "Park the car and walk a while."),
        Row(cls: "museum", category: .museum, dwell: 90, opens: 600, closes: 1020,
            hook: "Something to look at, out of the sun."),
        Row(cls: "cafe", category: .cafe, dwell: 30, opens: 420, closes: 1080,
            hook: "A slow cup somewhere new."),
        Row(cls: "garden", category: .garden, dwell: 60, opens: 540, closes: 1020,
            hook: "Planted paths and some shade."),
        Row(cls: "park", category: .park, dwell: 45, opens: nil, closes: nil,
            hook: "Green space to stretch your legs."),
        Row(cls: "town", category: .town, dwell: 60, opens: nil, closes: nil,
            hook: "A small main street to wander."),
    ]

    /// T-0283 R2: the class prior a mapped place carries as its quality, typed here a second time on purpose.
    static let prior: [String: Int] = ["viewpoint": 75, "peak": 75, "waterfall": 75, "beach": 75,
                                       "trailhead": 75, "garden": 75, "park": 50, "museum": 50,
                                       "town": 50, "cafe": 25]

    static func expected(_ row: Row, id: String = "8789912370140821739", name: String = "Saddle Peak",
                         corridor: String = "340:-1186", latitude: Double = 34.0780264,
                         longitude: Double = -118.6550579) -> SurpriseCandidate {
        SurpriseCandidate(id: id, name: name, hook: row.hook, category: row.category, corridor: corridor, brand: nil,
                          coordinate: Coordinate(latitude: latitude, longitude: longitude),
                          quality: prior[row.cls] ?? -1,
                          approachScore: 0, dwellMinutes: row.dwell, opensMinute: row.opens,
                          closesMinute: row.closes, hoursExempt: row.opens == nil, lit: false, unpaved: false,
                          privateApproach: false)
    }

    @Test("every corpus class maps to its ruled candidate, field for field (R3)", arguments: rows)
    func everyClassMapsToItsRuledCandidate(row: Row) {
        let got = SurprisePlaceMapping.candidate(placeID: Self.saddleID, cls: row.cls, name: "Saddle Peak",
                                                 lonE7: Self.saddleLonE7, latE7: Self.saddleLatE7)
        #expect(got == Self.expected(row))
    }

    @Test("the ten classes are the corpus's ten, in the ruled order, with the ruled labels")
    func theClassesAndLabelsAreTheRuledOnes() {
        #expect(SurprisePlaceClass.allCases.map(\.rawValue) == Self.rows.map(\.cls))
        #expect(SurprisePlaceClass.allCases.map(\.label) == ["Viewpoint", "Peak", "Waterfall", "Beach", "Trailhead",
                                                             "Museum", "Cafe", "Garden", "Park", "Town"])
    }

    @Test("an unnamed row, an empty name and a class outside the ten give no candidate",
          arguments: [("peak", nil), ("peak", ""), ("volcano", "Saddle Peak"), ("Peak", "Saddle Peak"),
                      ("", "Saddle Peak")] as [(String, String?)])
    func aRowWithoutANameOrAClassIsNoCandidate(cls: String, name: String?) {
        #expect(SurprisePlaceMapping.candidate(placeID: Self.saddleID, cls: cls, name: name,
                                               lonE7: Self.saddleLonE7, latE7: Self.saddleLatE7) == nil)
    }

    @Test("the corridor is the truncated 0.1 degree cell, on both sides of each edge",
          arguments: [(340_999_999, -1_186_999_999, "340:-1186"), (341_000_000, -1_186_999_999, "341:-1186"),
                      (340_999_999, -1_187_000_000, "340:-1187"), (341_000_000, -1_187_000_000, "341:-1187")]
          as [(Int64, Int64, String)])
    func theCorridorIsTheTruncatedCell(latE7: Int64, lonE7: Int64, corridor: String) {
        let got = SurprisePlaceMapping.candidate(placeID: 7, cls: "town", name: "Topanga", lonE7: lonE7, latE7: latE7)
        #expect(got == Self.expected(Self.rows[9], id: "7", name: "Topanga", corridor: corridor,
                                     latitude: Double(latE7) / 10_000_000, longitude: Double(lonE7) / 10_000_000))
    }

    @Test("a mapped Saddle Peak inside the offline reach is the pick, by full equality, through Surprise.pick")
    func theMappedCorpusFeedsThePick() throws {
        let saddle = try #require(SurprisePlaceMapping.candidate(placeID: Self.saddleID, cls: "peak",
                                                                 name: "Saddle Peak", lonE7: Self.saddleLonE7,
                                                                 latE7: Self.saddleLatE7))
        let zuma = try #require(SurprisePlaceMapping.candidate(placeID: 161_142_772_170_980_305, cls: "beach",
                                                               name: "Zuma Beach", lonE7: -1_188_273_532,
                                                               latE7: 340_188_704))
        let reach = SurpriseOfflineReach.reach(from: SurpriseOfflineReach.origin, to: [zuma, saddle],
                                               budgetMinutes: SurpriseOfflineReach.budgetMinutes)
        let context = SurpriseContext(userId: "on-device", date: CivilDate(year: 2026, month: 10, day: 6),
                                      departureMinute: 540, utcOffsetMinutes: -420, redFlag: false)
        let pick = Surprise.pick(candidates: [zuma, saddle], reach: reach, history: SurpriseHistory(),
                                 context: context, seed: 0)
        #expect(pick == SurprisePick(candidateId: "8789912370140821739", name: "Saddle Peak",
                                     reason: SurpriseReason(hook: "A high point with the basin below.",
                                                            roundTripMinutes: 73, goldenHourLine: nil)))
    }
}

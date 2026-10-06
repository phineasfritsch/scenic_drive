import Foundation
import Testing
@testable import ScenicKit

/// T-0273 R2: the offline reach the Surprise card hands Surprise.pick until the /isochrone client exists -
/// ceil(2 x straight-line metres x 1.4 / 750 m per minute). The bounds were found by a Python port of the same
/// expression in the same order (bisection, then nextafter), before this suite first ran; the three LA distances
/// come from a Python port of Geo.distanceMeters over the committed corpus rows (the Log's 05:07:47Z entry).
@Suite("Surprise offline reach")
struct SurpriseOfflineReachTests {
    @Test("the ruled constants: road factor 1.4, 750 m a minute, a 120-minute budget, from Westwood")
    func theConstantsAreTheRuledOnes() {
        #expect(SurpriseOfflineReach.roadFactor == 1.4)
        #expect(SurpriseOfflineReach.averageMetersPerMinute == 750)
        #expect(SurpriseOfflineReach.budgetMinutes == 120)
        #expect(SurpriseOfflineReach.origin == Coordinate(latitude: 34.0689, longitude: -118.4452))
        #expect(SurpriseOfflineReach.originName == "Westwood")
    }

    @Test("round-trip minutes at every bound: 0 m, the last double at 1, 60 and 120 minutes and the next one",
          arguments: [(0.0, 0), (267.8571428571429, 1), (267.85714285714295, 2), (16071.428571428572, 60),
                      (16071.428571428574, 61), (32142.857142857145, 120), (32142.85714285715, 121)]
          as [(Double, Int)])
    func roundTripMinutesAtEveryBound(meters: Double, minutes: Int) {
        #expect(SurpriseOfflineReach.roundTripMinutes(meters: meters) == minutes)
    }

    @Test("the reach over three committed LA places and the origin itself, by full equality")
    func theReachByFullEquality() throws {
        let rows: [(Int64, String, String, Int64, Int64)] = [
            (8_789_912_370_140_821_739, "peak", "Saddle Peak", -1_186_550_579, 340_780_264),
            (161_142_772_170_980_305, "beach", "Zuma Beach", -1_188_273_532, 340_188_704),
            (56_338_661_075_490_828, "viewpoint", "Inspiration Point", -1_189_428_330, 341_164_322),
            (1, "town", "Westwood", -1_184_452_000, 340_689_000),
        ]
        let candidates = try rows.map { row in
            try #require(SurprisePlaceMapping.candidate(placeID: row.0, cls: row.1, name: row.2, lonE7: row.3,
                                                        latE7: row.4))
        }
        let reach = SurpriseOfflineReach.reach(from: SurpriseOfflineReach.origin, to: candidates, budgetMinutes: 120)
        #expect(reach == SurpriseReach(budgetMinutes: 120,
                                       roundTripMinutes: ["8789912370140821739": 73, "161142772170980305": 134,
                                                          "56338661075490828": 173, "1": 0]))
    }

    @Test("the reach is measured from the origin handed in, not from Westwood")
    func theReachIsFromTheOriginHandedIn() throws {
        let saddle = try #require(SurprisePlaceMapping.candidate(placeID: 8_789_912_370_140_821_739, cls: "peak",
                                                                 name: "Saddle Peak", lonE7: -1_186_550_579,
                                                                 latE7: 340_780_264))
        #expect(SurpriseOfflineReach.reach(from: saddle.coordinate, to: [saddle], budgetMinutes: 120)
                == SurpriseReach(budgetMinutes: 120, roundTripMinutes: ["8789912370140821739": 0]))
    }

    @Test("the budget handed in is the budget handed out, and no candidate is dropped by the reach itself")
    func theBudgetPassesThrough() throws {
        let far = try #require(SurprisePlaceMapping.candidate(placeID: 56_338_661_075_490_828, cls: "viewpoint",
                                                              name: "Inspiration Point", lonE7: -1_189_428_330,
                                                              latE7: 341_164_322))
        #expect(SurpriseOfflineReach.reach(from: SurpriseOfflineReach.origin, to: [far], budgetMinutes: 45)
                == SurpriseReach(budgetMinutes: 45, roundTripMinutes: ["56338661075490828": 173]))
    }
}

import Foundation
import Testing
@testable import ScenicKit

/// The WHOLE day plan over T-0249 R7's LA -> Big Sur fixture, by exact equality to R8's expectations, which
/// were derived by hand from the generator's cumulative table before the engine existed (the task Log).
@Suite("road trip whole day plans")
struct RoadTripPlanTests {
    static let planA = RoadTripLimits(days: 3, maxDriveSeconds: 14_400, maxMeters: 321_869)
    static let planB = RoadTripLimits(days: 4, maxDriveSeconds: 9_000, maxMeters: 160_934)

    @Test("LA to Big Sur in 3 days at 4 h and 200 mi: the whole day plan")
    func threeDays() throws {
        #expect(try RoadTripFixture.run(Self.planA) == [
            "day 1 v0 Santa Monica -> v9 Gaviota 10543s 219014m "
                + "[Malibu Lagoon, Point Mugu Rock, Carpinteria Bluffs, Stearns Wharf] noLodging",
            "day 2 v9 Gaviota -> v16 Cambria 8881s 192169m "
                + "[Solvang, Pismo Pier, Morro Rock, Moonstone Beach] Cambria Pines Lodge 946m",
            "day 3 v16 Cambria -> v21 Big Sur 9151s 128092m [Elephant Seal Vista, Limekiln Falls] arrive",
        ])
    }

    @Test("LA to Big Sur in 4 days at 2.5 h and 100 mi: the whole day plan, miles binding")
    func fourDays() throws {
        #expect(try RoadTripFixture.run(Self.planB) == [
            "day 1 v0 Santa Monica -> v6 Carpinteria 7263s 137008m "
                + "[Malibu Lagoon, Point Mugu Rock, Ventura Pier, Carpinteria Bluffs] Summerland Inn 14405m",
            "day 2 v6 Carpinteria -> v12 Santa Maria 6276s 156896m "
                + "[Stearns Wharf, Gaviota Overlook, Solvang] noLodging",
            "day 3 v12 Santa Maria -> v18 Ragged Point 8811s 158240m "
                + "[Pismo Pier, Morro Rock, Moonstone Beach, Elephant Seal Vista] noLodging",
            "day 4 v18 Ragged Point -> v21 Big Sur 6225s 87131m [Limekiln Falls] arrive",
        ])
    }

    @Test("LA to Big Sur in 3 days at 2.5 h is too few days, stopped at Lucia")
    func tooFewDays() throws {
        let limits = RoadTripLimits(days: 3, maxDriveSeconds: 9_000, maxMeters: 321_869)
        #expect(try RoadTripFixture.run(limits) == ["tooFewDays days=3 reached=v20"])
    }

    @Test("the +40% budget is a ceiling: fastest 20_411 plans, 20_410 is over budget")
    func budgetCeiling() throws {
        #expect(RoadTrip.budgetSeconds(fastestSeconds: 20_411) == 8_164)
        #expect(RoadTrip.budgetSeconds(fastestSeconds: 20_410) == 8_164)
        #expect(try RoadTripFixture.run(Self.planA, fastest: 20_411).count == 3)
        #expect(try RoadTripFixture.run(Self.planA, fastest: 20_410) == ["overBudget route=28575 ceiling=28574"])
    }

    /// B's day 3 drives 158_240 m and 8_811 s; each limit set to exactly that keeps B, one unit less moves
    /// day 3's boundary back to San Simeon (v17), where San Simeon Motel sits on the vertex.
    static let shortened = [
        "day 1 v0 Santa Monica -> v6 Carpinteria 7263s 137008m "
            + "[Malibu Lagoon, Point Mugu Rock, Ventura Pier, Carpinteria Bluffs] Summerland Inn 14405m",
        "day 2 v6 Carpinteria -> v12 Santa Maria 6276s 156896m [Stearns Wharf, Gaviota Overlook, Solvang] noLodging",
        "day 3 v12 Santa Maria -> v17 San Simeon 7059s 133710m "
            + "[Pismo Pier, Morro Rock, Moonstone Beach, Elephant Seal Vista] San Simeon Motel 0m",
        "day 4 v17 San Simeon -> v21 Big Sur 7977s 111661m [Limekiln Falls] arrive",
    ]

    @Test("a day may drive exactly its max metres, and one metre less moves the boundary")
    func metresInclusive() throws {
        let exact = RoadTripLimits(days: 4, maxDriveSeconds: 9_000, maxMeters: 158_240)
        let less = RoadTripLimits(days: 4, maxDriveSeconds: 9_000, maxMeters: 158_239)
        #expect(try RoadTripFixture.run(exact) == RoadTripFixture.run(Self.planB))
        #expect(try RoadTripFixture.run(less) == Self.shortened)
    }

    @Test("a day may drive exactly its max seconds, and one second less moves the boundary")
    func secondsInclusive() throws {
        let exact = RoadTripLimits(days: 4, maxDriveSeconds: 8_811, maxMeters: 160_934)
        let less = RoadTripLimits(days: 4, maxDriveSeconds: 8_810, maxMeters: 160_934)
        #expect(try RoadTripFixture.run(exact) == RoadTripFixture.run(Self.planB))
        #expect(try RoadTripFixture.run(less) == Self.shortened)
    }
}

import Foundation
import Testing
@testable import ScenicKit

/// T-0249's properties over the shipping entry point `RoadTrip.plan`: limits never exceeded, 2-4 stops a
/// day whenever the corridor offers two, an honest no-lodging outcome, and the forward pass's edge cases.
@Suite("road trip properties")
struct RoadTripPropertyTests {
    /// Every ruled limit set the fixture plans under, from two to six days.
    static let grid: [RoadTripLimits] = [2, 3, 4, 5, 6].flatMap { days in
        [7_200, 9_000, 14_400, 18_000].flatMap { drive in
            [120_000, 160_934, 321_869].map { RoadTripLimits(days: days, maxDriveSeconds: drive, maxMeters: $0) }
        }
    }

    static func plans() throws -> [(RoadTripLimits, [RoadTripDay])] {
        let edges = try RoadTripFixture.edges(), places = try RoadTripFixture.places()
        return grid.compactMap { limits in
            if case let .plan(days) = RoadTrip.plan(edges: edges, places: places,
                                                    fastestSeconds: RoadTripFixture.fastestSeconds,
                                                    limits: limits) { return (limits, days) }
            return nil
        }
    }

    @Test("no day exceeds its max drive or max metres, and the days cover A to B edge for edge")
    func limitsHold() throws {
        let edges = try RoadTripFixture.edges()
        let plans = try Self.plans()
        #expect(plans.count >= 20, "only \(plans.count) of \(Self.grid.count) limit sets planned")
        for (limits, days) in plans {
            #expect(days.count <= limits.days)
            #expect(days.first?.startVertex == 0 && days.last?.endVertex == edges.count)
            for (i, d) in days.enumerated() {
                let span = edges[d.startVertex..<d.endVertex]
                #expect(d.day == i + 1 && d.endVertex > d.startVertex)
                #expect(i == 0 || days[i - 1].endVertex == d.startVertex)
                #expect(d.seconds == span.map(\.seconds).reduce(0, +) && d.meters == span.map(\.meters).reduce(0, +))
                #expect(d.seconds <= limits.maxDriveSeconds && d.meters <= limits.maxMeters, "\(limits) \(d)")
            }
        }
    }

    @Test("every day has 2-4 stops when its corridor offers them, and only what it offers when it does not")
    func twoToFourStops() throws {
        let edges = try RoadTripFixture.edges()
        let vertices = [edges[0].start] + edges.map(\.end)
        let stops = try RoadTripFixture.places().filter { $0.kind == .stop }
        var offeredTwo = 0, offeredFewer = 0
        for (_, days) in try Self.plans() {
            for d in days {
                let owned = (d.startVertex == 0 ? 0 : d.startVertex + 1)...d.endVertex
                let offered = stops.filter { s in
                    let ds = vertices.map { Geo.distanceMeters(s.coordinate, $0) }
                    let near = ds.firstIndex(of: ds.min()!)!
                    return owned.contains(near) && ds[near] <= 5_000
                }.map(\.name)
                if offered.count >= 2 {
                    offeredTwo += 1
                    #expect((2...4).contains(d.stops.count), "\(d)")
                } else {
                    offeredFewer += 1
                    #expect(d.stops == offered, "\(d)")
                }
                #expect(Set(d.stops).isSubset(of: Set(offered)), "\(d)")
            }
        }
        #expect(offeredTwo >= 40 && offeredFewer >= 1, "days offered two: \(offeredTwo), fewer: \(offeredFewer)")
    }

    @Test("a corridor without lodging says no lodging within 15 km at every boundary")
    func noLodgingIsSaid() throws {
        let edges = try RoadTripFixture.edges()
        let stopsOnly = try RoadTripFixture.places().filter { $0.kind == .stop }
        let outcome = RoadTrip.plan(edges: edges, places: stopsOnly, fastestSeconds: RoadTripFixture.fastestSeconds,
                                    limits: RoadTripPlanTests.planB)
        #expect(RoadTripFixture.render(outcome, names: try RoadTripFixture.vertexNames()).map {
            String($0.split(separator: "]").last!)
        } == [" noLodging", " noLodging", " noLodging", " arrive"])
    }

    static let a = Coordinate(latitude: 34.0, longitude: -118.0)
    static func line(_ seconds: [Int]) -> [RoadTripEdge] {
        seconds.map { RoadTripEdge(start: a, end: a, seconds: $0, meters: $0) }
    }

    @Test("an edge spanning two even shares still leaves every day an edge, and no day is invented")
    func everyDayDrives() {
        let three = RoadTrip.plan(edges: Self.line([100, 10, 10]), places: [], fastestSeconds: 1_000,
                                  limits: RoadTripLimits(days: 3, maxDriveSeconds: 500, maxMeters: 500))
        let five = RoadTrip.plan(edges: Self.line([100, 10, 10]), places: [], fastestSeconds: 1_000,
                                 limits: RoadTripLimits(days: 5, maxDriveSeconds: 500, maxMeters: 500))
        for outcome in [three, five] {
            #expect(RoadTripFixture.render(outcome, names: []) == [
                "day 1 v0 ? -> v1 ? 100s 100m [] noLodging", "day 2 v1 ? -> v2 ? 10s 10m [] noLodging",
                "day 3 v2 ? -> v3 ? 10s 10m [] arrive"])
        }
    }

    @Test("an edge longer than a day's limit is too few days at its start vertex")
    func edgeOverLimit() {
        let outcome = RoadTrip.plan(edges: Self.line([100, 500, 100]), places: [], fastestSeconds: 1_000,
                                    limits: RoadTripLimits(days: 5, maxDriveSeconds: 400, maxMeters: 400))
        #expect(outcome == .tooFewDays(days: 5, reachedVertex: 1))
    }

    @Test("zero days is too few days at vertex 0, and no edges is an empty plan")
    func degenerate() {
        let limits = RoadTripLimits(days: 0, maxDriveSeconds: 400, maxMeters: 400)
        #expect(RoadTrip.plan(edges: Self.line([10]), places: [], fastestSeconds: 100, limits: limits)
            == .tooFewDays(days: 0, reachedVertex: 0))
        #expect(RoadTrip.plan(edges: [], places: [], fastestSeconds: 100,
                              limits: RoadTripLimits(days: 2, maxDriveSeconds: 400, maxMeters: 400)) == .plan([]))
    }
}

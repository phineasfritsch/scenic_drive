import Foundation
import Testing
@testable import ScenicKit

/// The time-versus-fun menu over RECORDED alternatives (T-0239 acceptance 2): the committed recorder's
/// `--alternatives on` output for two trips off T-0213's canyon-window graph, GraphHopper 11, free-flow.
///
/// The expected rows are the frontier probe's measured prediction (.artifacts/frontier/SUMMARY.md, quoted in
/// the task Log) re-ranked on fun km per R4, with the extra minutes rounded UP per R5: T1 +12.2 and +17.1
/// (the probe printed the nearest, 17.0, for 1_020_063 ms), T4 +5.5 (probe 5.4, 326_309 ms) and +16.6.
@Suite("route menu over recorded alternatives")
struct RouteMenuTests {

    static func fixture(_ trip: String) -> URL {
        URL(fileURLWithPath: #filePath)        // Tests/ScenicKitTests/Menu/<this file>
            .deletingLastPathComponent()       // Tests/ScenicKitTests/Menu
            .deletingLastPathComponent()       // Tests/ScenicKitTests
            .deletingLastPathComponent()       // Tests
            .appendingPathComponent("Fixtures/t0239/\(trip)")
    }

    /// The endpoints each recording's `recorded` header names; the loader refuses any other trip.
    static let endpoints: [String: (Coordinate, Coordinate)] = [
        "topanga-malibu": (Coordinate(latitude: 34.0944, longitude: -118.6013),
                           Coordinate(latitude: 34.0365, longitude: -118.687)),
        "zuma-agoura": (Coordinate(latitude: 34.017, longitude: -118.823),
                        Coordinate(latitude: 34.144, longitude: -118.76)),
    ]

    static func recorded(_ trip: String) throws -> (fastest: RoutePath, candidates: [RoutePath]) {
        guard let trip = endpoints[trip].map({ (fixture(trip), $0.0, $0.1) }) else {
            throw PlanFailure.malformedResponse("no endpoints for \(trip)")
        }
        return try RecordedAlternatives.load(directory: trip.0, ladder: RouteMenu.ladder, origin: trip.1,
                                             destination: trip.2)
    }

    static func menu(_ trip: String) throws -> RouteMenu {
        let pool = try recorded(trip)
        return RouteMenu(fastest: pool.fastest, candidates: pool.candidates)
    }

    static func tenths(_ meters: Double) -> Double { (meters / 100).rounded() / 10 }

    @Test("Topanga to Malibu: the menu rows to 0.1 min and 0.1 fun km")
    func topangaToMalibu() throws {
        let menu = try Self.menu("topanga-malibu")
        #expect(menu.rows.map(\.extraMinutes) == [0.0, 12.2, 17.1])
        #expect(menu.rows.map { Self.tenths($0.funMeters) } == [6.1, 21.5, 26.2])
        #expect(menu.rows.first?.path.durationMilliseconds == 1_075_693)
    }

    @Test("Zuma to Agoura: the menu rows to 0.1, and Latigo Canyon Road is on it")
    func zumaToAgoura() throws {
        let menu = try Self.menu("zuma-agoura")
        #expect(menu.rows.map(\.extraMinutes) == [0.0, 5.5, 16.6])
        #expect(menu.rows.map { Self.tenths($0.funMeters) } == [10.6, 15.5, 19.7])
        let latigo = try #require(menu.rows.first { $0.roads.contains("Latigo Canyon Road") })
        #expect(latigo.extraMinutes == 16.6)
        #expect(latigo.roads == ["Pacific Coast Highway", "Latigo Canyon Road", "Kanan Dume Road", "Kanan Road",
                               "Agoura Road"])
    }

    @Test("alternative_route over the ladder yields 6 distinct routes per trip at Jaccard 0.9")
    func distinctRoutes() throws {
        for trip in ["topanga-malibu", "zuma-agoura"] {
            let menu = try Self.menu(trip)
            #expect(menu.candidateCount == 25, "\(trip)")
            #expect(menu.distinctCount == 6, "\(trip)")
        }
    }

    /// R4's "the most fun of EVERY quicker row", not the most fun share. T4's Snake row has the higher share
    /// (58%) and Latigo the more fun km (19.7), and on the two recordings nothing slower than Latigo tells the
    /// two readings apart; a recorded T1 route between Snake + 2 km and Latigo + 2 km does - it is no row.
    @Test("a slower route must add 2 fun km over the most fun km of every quicker row, not the highest share")
    func frontierStepsFromTheMostFunKm() throws {
        let t4 = try Self.menu("zuma-agoura").rows
        try #require(t4.count == 3)
        let (snake, latigo) = (t4[1], t4[2])
        #expect(snake.funShare > latigo.funShare && snake.funMeters < latigo.funMeters)
        let t1 = try Self.recorded("topanga-malibu")
        let rows = t1.candidates.map { MenuRow(path: $0, fastestMilliseconds: t1.fastest.durationMilliseconds) }
        let between = try #require(rows.first {
            $0.funMeters >= snake.funMeters + RouteMenu.funStepMeters
                && $0.funMeters < latigo.funMeters + RouteMenu.funStepMeters
        })
        #expect(RouteMenu.frontier(t4 + [between]) == t4)
    }
}

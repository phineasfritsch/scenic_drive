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

    static func menu(_ trip: String) throws -> RouteMenu {
        let recorded = try RecordedAlternatives.load(directory: fixture(trip), ladder: RouteMenu.ladder)
        return RouteMenu(fastest: recorded.fastest, candidates: recorded.candidates)
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
}

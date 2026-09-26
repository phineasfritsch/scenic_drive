import Foundation
import Testing
import ScenicKit
@testable import ScenicPlanCLI

/// `ops/plan --menu`, driven through `MenuArguments.parse` and `MenuCommand.run` - the two calls main.swift
/// makes with what a person types - over the recorded T1 and T4 alternatives (T-0239 acceptance 3).
///
/// THE BUDGET IS A CEILING (CLAUDE.md, P-SAFE-04's property): every row's ETA is at most the fastest ETA
/// plus the extra minutes that row DISPLAYS, and `--max N` prints no row above +N. `--max 20` is the
/// acceptance's literal and on these two trips it cuts nothing (the slowest row is +17.1), so the cut is
/// also shown where it bites: `--max 15` must drop T1's +17.1 row and `--max 10` T4's +16.6 Latigo row.
@Suite("ops/plan --menu")
struct MenuCLITests {

    static func fixture(_ trip: String) -> String {
        URL(fileURLWithPath: #filePath)        // Tests/ScenicPlanCLITests/<this file>
            .deletingLastPathComponent()       // Tests/ScenicPlanCLITests
            .deletingLastPathComponent()       // Tests
            .appendingPathComponent("Fixtures/t0239/\(trip)").path
    }

    static let trips = [
        ("topanga-malibu", "34.0944,-118.6013", "34.0365,-118.6870"),
        ("zuma-agoura", "34.017,-118.823", "34.144,-118.76"),
    ]

    static func arguments(_ trip: (String, String, String), _ extra: [String] = []) throws -> MenuArguments {
        try MenuArguments.parse([trip.1, trip.2] + extra + ["--recorded", fixture(trip.0)])
    }

    /// The `extra=+N.Nmin` figures of the printed ROW lines.
    static func printedExtras(_ lines: [String]) -> [Double] {
        lines.filter { $0.hasPrefix("ROW ") }.compactMap { line in
            guard let field = line.split(separator: " ").first(where: { $0.hasPrefix("extra=+") }) else {
                return nil
            }
            return Double(field.dropFirst("extra=+".count).dropLast("min".count))
        }
    }

    @Test("every menu row keeps ETA within fastest plus its displayed extra minutes")
    func everyRowIsInsideItsOwnCeiling() throws {
        for trip in Self.trips {
            let arguments = try Self.arguments(trip)
            let menu = try MenuCommand.menu(arguments)
            #expect(menu.rows.count >= 3, "\(trip.0)")
            for row in menu.rows {
                let ceiling = menu.fastestMilliseconds + row.extraTenths * 6_000
                #expect(row.path.durationMilliseconds <= ceiling, "\(trip.0) +\(row.extraMinutes)")
            }
            #expect(Self.printedExtras(try MenuCommand.run(arguments)) == menu.rows.map(\.extraMinutes))
        }
    }

    @Test("ops/plan --menu --max 20 prints no row above +20")
    func maxTwentyPrintsNothingAboveTwenty() throws {
        for trip in Self.trips {
            let extras = Self.printedExtras(try MenuCommand.run(try Self.arguments(trip, ["--max", "20"])))
            #expect(!extras.isEmpty, "\(trip.0)")
            #expect(extras.allSatisfy { $0 <= 20 }, "\(trip.0) \(extras)")
        }
    }

    @Test("--max below a row drops that row and keeps every quicker one")
    func maxBelowARowDropsIt() throws {
        let t1 = Self.printedExtras(try MenuCommand.run(try Self.arguments(Self.trips[0], ["--max", "15"])))
        #expect(t1 == [0.0, 12.2])
        let t4Lines = try MenuCommand.run(try Self.arguments(Self.trips[1], ["--max", "10"]))
        #expect(Self.printedExtras(t4Lines) == [0.0, 5.5])
        #expect(!t4Lines.contains { $0.contains("Latigo Canyon Road") })
    }

    @Test("--max above 45 and --router are refused by name")
    func refusals() throws {
        #expect(throws: PlanArguments.Failure.self) { try Self.arguments(Self.trips[0], ["--max", "46"]) }
        #expect(throws: PlanArguments.Failure.self) { try Self.arguments(Self.trips[0], ["--max", "0"]) }
        #expect(throws: PlanArguments.Failure.self) {
            try MenuArguments.parse(["34.0944,-118.6013", "34.0365,-118.6870", "--router",
                                     "http://127.0.0.1:8989"])
        }
        #expect(try Self.arguments(Self.trips[0], ["--max", "45"]).maxMinutes == 45)
    }

    @Test("every row prints an Apple Maps URL with at most 9 waypoints")
    func everyRowHandsOff() throws {
        for trip in Self.trips {
            let lines = try MenuCommand.run(try Self.arguments(trip))
            let rows = lines.filter { $0.hasPrefix("ROW ") }
            let urls = lines.filter { $0.hasPrefix("URL ") }
            #expect(urls.count == rows.count && !rows.isEmpty, "\(trip.0)")
            for url in urls {
                let fields = url.split(separator: " ")
                let count = Int(fields[2].dropFirst("waypoints=".count)) ?? -1
                #expect((1...9).contains(count), "\(url)")
                #expect(fields[3].hasPrefix("https://maps.apple.com/"), "\(url)")
            }
        }
    }

    /// P-SAFE-04 at the boundary. `--max 15` and `--max 10` sit 2.0 and 6.6 minutes under the next row, so a
    /// cap that let 1.9 minutes through passed them. 0.1 below each row's displayed extra must drop that row
    /// and nothing quicker, and exactly at it must keep it (T1's +17.1 row is 1_020_063 ms: 63 ms past 17.0).
    @Test("--max 0.1 below a row's displayed extra drops that row, and --max at it keeps it")
    func maxAtTheBoundary() throws {
        for trip in Self.trips {
            let rows = try MenuCommand.menu(try Self.arguments(trip)).rows.map(\.extraMinutes)
            #expect(rows.count >= 3, "\(trip.0)")
            for (index, extra) in rows.enumerated().dropFirst() {
                let at = ScenicPlan.fixed(extra, 1), below = ScenicPlan.fixed(extra - 0.1, 1)
                let kept = Self.printedExtras(try MenuCommand.run(try Self.arguments(trip, ["--max", at])))
                #expect(kept == Array(rows.prefix(index + 1)), "\(trip.0) --max \(at)")
                let cut = Self.printedExtras(try MenuCommand.run(try Self.arguments(trip, ["--max", below])))
                #expect(cut == Array(rows.prefix(index)), "\(trip.0) --max \(below)")
            }
        }
    }

    /// The counts come from the SHIPPING load (`MenuCommand.menu`'s own ladder), so a rung the CLI stops
    /// reading shows here: 25 recorded paths per trip (fastest.json + 4 alternatives x 6 requests).
    @Test("ops/plan --menu reads every rung: candidates=25 distinct=6 on both trips")
    func headerCountsEveryRung() throws {
        for trip in Self.trips {
            let lines = try MenuCommand.run(try Self.arguments(trip))
            let header = try #require(lines.first { $0.hasPrefix("MENU ") })
            #expect(header.contains(" candidates=25 distinct=6 "), "\(header)")
        }
    }

    @Test("a recording of another trip is refused, not replayed under these endpoints")
    func anotherTripIsRefused() throws {
        let swapped = ("topanga-malibu", Self.trips[1].1, Self.trips[1].2)
        #expect(throws: PlanFailure.self) { try MenuCommand.run(try Self.arguments(swapped)) }
    }

    @Test("a rung whose file carries another rung's recording is refused")
    func anotherRungIsRefused() throws {
        let files = FileManager.default
        let copy = files.temporaryDirectory.appendingPathComponent("t0239-rung-\(UUID().uuidString)")
        try files.copyItem(at: URL(fileURLWithPath: Self.fixture("topanga-malibu")), to: copy)
        defer { try? files.removeItem(at: copy) }
        let trip = Self.trips[0]
        let arguments = try MenuArguments.parse([trip.1, trip.2, "--recorded", copy.path])
        #expect(try MenuCommand.run(arguments).count > 2)
        let eight = copy.appendingPathComponent(RecordedAlternatives.fileName(forLambda: 8))
        try files.removeItem(at: eight)
        try files.copyItem(at: copy.appendingPathComponent(RecordedAlternatives.fileName(forLambda: 4)), to: eight)
        #expect(throws: PlanFailure.self) { try MenuCommand.run(arguments) }
    }

    /// A `lat,lon` text - a trip literal or a URL query value - as a coordinate.
    static func coordinate(_ text: String) -> Coordinate? {
        let pair = text.split(separator: ",").compactMap { Double($0) }
        return pair.count == 2 ? Coordinate(latitude: pair[0], longitude: pair[1]) : nil
    }

    /// The `name` pins (`source`, `destination`, `waypoint`) of a printed `URL <index> waypoints=<n> <url>` line.
    static func pins(_ line: String, _ name: String) -> [Coordinate] {
        let url = line.split(separator: " ").last.map(String.init) ?? ""
        return (URLComponents(string: url)?.queryItems ?? []).filter { $0.name == name }
            .compactMap { coordinate($0.value ?? "") }
    }

    static func stops(_ line: String) -> [Coordinate] { pins(line, "waypoint") }

    static func fiveDecimals(_ c: Coordinate) -> String {
        "\(ScenicPlan.fixed(c.latitude, 5)),\(ScenicPlan.fixed(c.longitude, 5))"
    }

    /// rv1 B1: a URL built from another row's route passed every test above. The Latigo row is found by the
    /// road its printed line names, and its pins are measured against that row's recorded Latigo vertices.
    @Test("each row's Apple Maps URL is its own route's: pairwise distinct, and T4's Latigo URL stops on Latigo Canyon Road")
    func eachRowHandsOffItsOwnRoute() throws {
        for trip in Self.trips {
            let urls = try MenuCommand.run(try Self.arguments(trip)).filter { $0.hasPrefix("URL ") }
                .map { $0.split(separator: " ").last.map(String.init) ?? "" }
            #expect(urls.count >= 3 && Set(urls).count == urls.count, "\(trip.0) \(urls)")
        }
        let arguments = try Self.arguments(Self.trips[1])
        let lines = try MenuCommand.run(arguments)
        let index = try #require(lines.filter { $0.hasPrefix("ROW ") }.firstIndex { $0.contains("Latigo Canyon Road") })
        let path = try MenuCommand.menu(arguments).rows[index].path
        let latigo = (path.details["street_name"] ?? []).filter { $0.value.text == "Latigo Canyon Road" }
            .flatMap { path.coordinates[$0.from...min($0.to, path.coordinates.count - 1)] }
        let url = try #require(lines.first { $0.hasPrefix("URL \(index) ") })
        let nearest = Self.stops(url).flatMap { stop in latigo.map { Geo.distanceMeters(stop, $0) } }.min()
        #expect(latigo.count >= 2 && (nearest ?? .infinity) <= 300, "row \(index): nearest pin \(String(describing: nearest)) m")
    }

    /// rv1 B2: an alternatives file must say `alternative_route` and fastest.json must not. Each refusal is a
    /// `PlanFailure` - exit 3 in main.swift - naming the algorithm it found and the one it expected.
    @Test("a recording whose algorithm is not its file's is refused, naming the algorithm")
    func anotherAlgorithmIsRefused() throws {
        let files = FileManager.default, trip = Self.trips[0]
        let cases = [
            (RecordedAlternatives.fileName(forLambda: 4), "\"algorithm\": \"[^\"]*\"", "\"algorithm\": \"astarbi\"",
             "[astarbi], not of car_scenic lambda-4.json [alternative_route]"),
            (RecordedAlternatives.fastestFileName, "\"model\": \"-\",", "\"model\": \"-\", \"algorithm\": \"alternative_route\",",
             "[alternative_route], not of car_fast - [no alternative_route]"),
        ]
        for (name, pattern, replacement, named) in cases {
            let copy = files.temporaryDirectory.appendingPathComponent("t0239-algorithm-\(UUID().uuidString)")
            try files.copyItem(at: URL(fileURLWithPath: Self.fixture(trip.0)), to: copy)
            defer { try? files.removeItem(at: copy) }
            let arguments = try MenuArguments.parse([trip.1, trip.2, "--recorded", copy.path])
            #expect(try MenuCommand.run(arguments).count > 2)
            let file = copy.appendingPathComponent(name)
            let text = try String(contentsOf: file, encoding: .utf8)
            let edited = text.replacingOccurrences(of: pattern, with: replacement, options: .regularExpression)
            #expect(edited != text, "\(name)")
            try edited.write(to: file, atomically: true, encoding: .utf8)
            do {
                _ = try MenuCommand.run(arguments)
                Issue.record("\(name) with its algorithm changed was replayed")
            } catch let failure as PlanFailure {
                #expect("\(failure)".contains(named), "\(failure)")
            }
        }
    }

    /// rv2 M2/M3: a URL whose source and destination were swapped, or whose waypoints were reversed, passed
    /// every test above. For EVERY row on both trips, parsed from the printed URL: `source` is the trip's
    /// origin literal and `destination` its destination literal (to 5 dp), and each waypoint's nearest vertex
    /// along that row's recorded path strictly increases - the pins are in route order.
    @Test("every row's URL runs from the trip's origin to its destination, its waypoints in route order")
    func everyURLRunsItsRowInOrder() throws {
        for trip in Self.trips {
            let arguments = try Self.arguments(trip)
            let rows = try MenuCommand.menu(arguments).rows
            let urls = try MenuCommand.run(arguments).filter { $0.hasPrefix("URL ") }
            let origin = try #require(Self.coordinate(trip.1)), destination = try #require(Self.coordinate(trip.2))
            #expect(urls.count == rows.count && rows.count >= 3, "\(trip.0)")
            for (index, url) in zip(rows.indices, urls) {
                #expect(Self.pins(url, "source").map(Self.fiveDecimals) == [Self.fiveDecimals(origin)], "\(url)")
                #expect(Self.pins(url, "destination").map(Self.fiveDecimals) == [Self.fiveDecimals(destination)],
                        "\(url)")
                let path = rows[index].path.coordinates
                let along = Self.stops(url).map { stop in
                    path.indices.min { Geo.distanceMeters(stop, path[$0]) < Geo.distanceMeters(stop, path[$1]) } ?? -1
                }
                #expect(along.count >= 2, "\(trip.0) row \(index): \(along.count) waypoints")
                #expect(zip(along, along.dropFirst()).allSatisfy { $0 < $1 }, "\(trip.0) row \(index): \(along)")
            }
        }
    }
}

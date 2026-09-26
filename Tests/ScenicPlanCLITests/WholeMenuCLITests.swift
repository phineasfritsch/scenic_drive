import Foundation
import Testing
import Handoff
import ScenicKit
@testable import ScenicPlanCLI

/// T-0245, from rv4-t0239's B1-B2: the WHOLE output `ops/plan --menu` prints, under every flag T-0239's
/// acceptance runs (none, `--max 20`, `--max 15`, `--max 10`) on both recorded trips, equals a recomputation
/// built here from the recorded rows through the committed builders - `RecordedAlternatives.load`,
/// `RouteMenu` and its `header()`, `MenuRow.line`, `PlanWaypoints.decisionPoints`, `AppleMapsDirections` -
/// compared as ONE string; and ROW n is followed by URL n.
///
/// The oracle does not call `MenuCommand`: the menu is rebuilt from the recording with `RouteMenu.ladder`
/// (not `MenuCommand.menu`), the endpoints are parsed here from the trip literals (not taken from
/// `MenuArguments`), the no-flag cap is the literal 45, and the `ROUTER` and `URL` line formats are typed here
/// from T-0239's quoted output. `MenuRow.line` takes the row number as an argument, so the numbering is also
/// asserted on the printed lines alone. Nothing here names MenuCLITests: `menu.py --prove-vacuity` replaces
/// that file with an empty suite, and this one must still compile.
@Suite("ops/plan --menu whole output")
struct WholeMenuCLITests {

    static func fixture(_ trip: String) -> URL {
        URL(fileURLWithPath: #filePath)        // Tests/ScenicPlanCLITests/<this file>
            .deletingLastPathComponent()       // Tests/ScenicPlanCLITests
            .deletingLastPathComponent()       // Tests
            .appendingPathComponent("Fixtures/t0239/\(trip)")
    }

    static let trips = [
        ("topanga-malibu", "34.0944,-118.6013", "34.0365,-118.6870"),
        ("zuma-agoura", "34.017,-118.823", "34.144,-118.76"),
    ]

    /// The flags T-0239's acceptance runs, each with the cap it means (no flag is the 45-minute cap).
    static let invocations: [([String], Double)] = [
        ([], 45), (["--max", "20"], 20), (["--max", "15"], 15), (["--max", "10"], 10),
    ]

    static func coordinate(_ text: String) throws -> Coordinate {
        let pair = text.split(separator: ",").compactMap { Double($0) }
        guard pair.count == 2 else { throw PlanFailure.malformedResponse("not a lat,lon literal: \(text)") }
        return Coordinate(latitude: pair[0], longitude: pair[1])
    }

    /// The lines `ops/plan --menu` must print for `trip` under `cap`, computed without MenuCommand.
    static func recomputed(_ trip: (String, String, String), cap: Double) throws -> [String] {
        let origin = try coordinate(trip.1), destination = try coordinate(trip.2)
        let recorded = try RecordedAlternatives.load(directory: fixture(trip.0), ladder: RouteMenu.ladder,
                                                     origin: origin, destination: destination)
        let menu = RouteMenu(fastest: recorded.fastest, candidates: recorded.candidates, maxMinutes: cap)
        var lines = ["ROUTER recorded \(trip.0)", menu.header()]
        for (n, row) in menu.rows.enumerated() {
            let pins = PlanWaypoints.decisionPoints(table: row.table, path: row.path)
            let url = try AppleMapsDirections(source: origin, destination: destination, waypoints: pins).url()
            lines.append(row.line(n))
            lines.append("URL \(n) waypoints=\(pins.count) \(url.absoluteString)")
        }
        return lines
    }

    /// rv4 X2 (every row handed off on row 0's pins whenever `--max` is below the cap) printed the right
    /// output without a flag and passed; rv4 X1 (ROW lines numbered index + 1) passed every test before it.
    @Test("ops/plan --menu prints exactly its recomputation from the recorded rows under no flag and --max 20, 15, 10, and ROW n is followed by URL n")
    func wholeOutputUnderEveryFlag() throws {
        for trip in Self.trips {
            for (flags, cap) in Self.invocations {
                let label = "\(trip.0) [\(flags.joined(separator: " "))]"
                let arguments = try MenuArguments.parse([trip.1, trip.2] + flags
                                                        + ["--recorded", Self.fixture(trip.0).path])
                let printed = try MenuCommand.run(arguments)
                let expected = try Self.recomputed(trip, cap: cap)
                #expect(expected.count >= 4 && expected.count % 2 == 0, "\(label): \(expected.count) lines")
                #expect(printed.joined(separator: "\n") == expected.joined(separator: "\n"), "\(label)")
                let numbers = printed.dropFirst(2).map { $0.split(separator: " ").prefix(2).joined(separator: " ") }
                let paired = (0..<(numbers.count / 2)).flatMap { ["ROW \($0)", "URL \($0)"] }
                #expect(numbers.count >= 2 && numbers == paired, "\(label): \(numbers)")
            }
        }
    }
}

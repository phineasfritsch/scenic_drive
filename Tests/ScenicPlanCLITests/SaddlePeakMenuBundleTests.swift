import Foundation
import Testing
import Handoff
import ScenicKit
@testable import ScenicPlanCLI

/// The home sheet's menu (T-0246) is `apps/ios/ScenicDrive/Routes/saddle-peak-menu.json`, written by
/// `ops/lib/make-menu-bundle.py` from `ops/plan --menu`'s stdout. These tests bind that file to the SHIPPING
/// entry point, `MenuCommand.run` - the function main.swift prints - by exact equality of the WHOLE printed
/// output (T-0245's lesson: a URL compared field by field let a wrong one through), and bind the app's reading of
/// it to the same numbers: the chips, the line each chip draws, and the URL each chip hands to Apple Maps.
///
/// The file is decoded with `DriveMenu(data:)`, the decoder the app runs; nothing here re-reads the JSON by hand.
@Suite("the Saddle Peak menu bundle is ops/plan --menu's output (T-0246)")
struct SaddlePeakMenuBundleTests {

    static let root = URL(fileURLWithPath: #filePath)   // Tests/ScenicPlanCLITests/<this file>
        .deletingLastPathComponent()                    // Tests/ScenicPlanCLITests
        .deletingLastPathComponent()                    // Tests
        .deletingLastPathComponent()                    // the repository

    /// Where the app bundle's `Routes` folder comes from, spelled with the names the app looks the file up by.
    static var bundleURL: URL {
        root.appendingPathComponent("apps/ios/ScenicDrive")
            .appendingPathComponent(HandoffDrive.routeGeometrySubdirectory)
            .appendingPathComponent("\(HandoffDrive.saddlePeak.menuResource ?? "none").\(HandoffDrive.menuExtension)")
    }

    /// The trip and the recording, typed once: the command the filer measured and the owner's reference shows.
    static let command = ["--menu", "34.0944,-118.6013", "34.0365,-118.687",
                          "--recorded", "Tests/Fixtures/t0239/topanga-malibu"]

    static func menu() throws -> DriveMenu {
        try DriveMenu(data: try Data(contentsOf: bundleURL))
    }

    /// The shipping CLI's arguments for `command`: main.swift drops `--menu` and hands the rest to
    /// `MenuArguments.parse`; the recording is resolved against the repository, as ops/plan's cwd would.
    static func arguments() throws -> MenuArguments {
        var rest = Array(command.dropFirst())
        let at = try #require(rest.firstIndex(of: "--recorded"))
        rest[at + 1] = root.appendingPathComponent(rest[at + 1]).path
        return try MenuArguments.parse(rest)
    }

    /// Everything `ops/plan --menu` prints for the trip, line for line.
    static func printed() throws -> [String] {
        try MenuCommand.run(try arguments())
    }

    /// One row as the CLI prints its fields, read from the printed lines with no help from the bundle:
    /// `extra|fun_km|roads|url`.
    static func printedRows(_ lines: [String]) -> [String] {
        let rows = lines.filter { $0.hasPrefix("ROW ") }
        let urls = lines.filter { $0.hasPrefix("URL ") }
        return zip(rows, urls).map { row, url in
            let fields = row.components(separatedBy: " roads=")
            let words = fields[0].split(separator: " ")
            let extra = words.first { $0.hasPrefix("extra=+") }.map { $0.dropFirst(7).dropLast(3) } ?? "?"
            let fun = words.first { $0.hasPrefix("fun_km=") }.map { $0.dropFirst(7) } ?? "?"
            return "\(extra)|\(fun)|\(fields.count == 2 ? fields[1] : "?")|\(url.split(separator: " ").last ?? "?")"
        }
    }

    /// The bundle's row in the same shape, formatted by the CLI's own formatter.
    static func bundledRow(_ row: DriveMenuRow) -> String {
        "\(ScenicPlan.fixed(row.extraMinutes, 1))|\(ScenicPlan.fixed(row.funKm, 1))|"
            + "\(row.roads.joined(separator: ", "))|\(row.appleMapsURL)"
    }

    static func coordinate(_ position: [Double]) -> Coordinate {
        Coordinate(latitude: position[1], longitude: position[0])
    }

    /// Metres from `point` to the polyline, in a local equirectangular plane (34 N, a 30 km extent).
    static func metres(from point: Coordinate, to line: [[Double]]) -> Double {
        let k = cos(point.latitude * .pi / 180), r = 6_371_008.8 * .pi / 180
        let plane = line.map { (($0[0] - point.longitude) * r * k, ($0[1] - point.latitude) * r) }
        return zip(plane, plane.dropFirst()).map { a, b in
            let (dx, dy) = (b.0 - a.0, b.1 - a.1)
            let t = max(0, min(1, -(a.0 * dx + a.1 * dy) / max(dx * dx + dy * dy, 1e-12)))
            return hypot(a.0 + t * dx, a.1 + t * dy)
        }.min() ?? .infinity
    }

    @Test("the bundle's printed lines are the shipping ops/plan --menu output, whole and exact")
    func bundlePrintedIsTheWholeCLIOutput() throws {
        let menu = try Self.menu()
        #expect(menu.command == Self.command)
        #expect(menu.printed == (try Self.printed()))
    }

    @Test("every row's extra minutes, good-road km, roads and URL are the CLI's, in the CLI's order")
    func bundleRowsAreTheCLIRows() throws {
        let expected = Self.printedRows(try Self.printed())
        #expect(expected.count == 3)
        #expect(try Self.menu().rows.map(Self.bundledRow) == expected)
    }

    @Test("every row's drawn line starts and ends within 10 m of the trip's origin and destination")
    func everyRowLineStartsAndEndsAtTheTrip() throws {
        let arguments = try Self.arguments()
        for (index, row) in try Self.menu().rows.enumerated() {
            let first = try #require(row.line.first), last = try #require(row.line.last)
            #expect(Geo.distanceMeters(Self.coordinate(first), arguments.origin) <= 10, "row \(index) start")
            #expect(Geo.distanceMeters(Self.coordinate(last), arguments.destination) <= 10, "row \(index) end")
        }
    }

    @Test("every pin of every row's URL lies on that row's drawn line (5 m simplification + rounding)")
    func everyURLPinLiesOnItsRowLine() throws {
        let menu = try Self.menu()
        for (index, row) in menu.rows.enumerated() {
            let pins = try #require(URLComponents(string: row.appleMapsURL)?.queryItems)
                .filter { $0.name == "waypoint" }.compactMap(\.value)
            #expect(pins.count == 9, "row \(index)")
            for pin in pins {
                let parts = pin.split(separator: ",").compactMap { Double($0) }
                let at = Coordinate(latitude: parts[0], longitude: parts[1])
                #expect(Self.metres(from: at, to: row.line) <= menu.toleranceM + 2, "row \(index) pin \(pin)")
            }
        }
    }

    @Test("each chip's minutes are a ceiling over its row's extra and its real ETA (P-SAFE-04)")
    func chipMinutesAreACeiling() throws {
        let menu = try Self.menu()
        let engine = try MenuCommand.menu(try Self.arguments())
        #expect(engine.rows.count == menu.rows.count)
        for (row, real) in zip(menu.rows, engine.rows) {
            #expect(row.extraMinutes <= Double(row.displayedMinutes), "\(row.chipLabel)")
            #expect(real.path.durationMilliseconds <= engine.fastestMilliseconds + row.displayedMinutes * 60_000,
                    "\(row.chipLabel)")
        }
        #expect(menu.rows.map(\.chipLabel) == ["Fastest", "+13 min", "+18 min"])
        #expect(menu.rows.map(\.goodRoadLabel) == ["6.1 km good road", "21.5 km good road", "26.2 km good road"])
    }

    @Test("the handoff for each selected row opens exactly that row's printed URL; the default is Saddle Peak")
    func handoffURLForEachSelectedRowIsTheCLIURL() throws {
        let menu = try Self.menu()
        let printed = try Self.printed().filter { $0.hasPrefix("URL ") }.map { String($0.split(separator: " ").last!) }
        #expect(printed.count == menu.rows.count)
        for (index, url) in printed.enumerated() {
            #expect(try HandoffDrive.saddlePeak.url(row: menu.row(selected: index)).absoluteString == url)
        }
        #expect(menu.defaultRow == 2)
        #expect(menu.row(selected: nil) == menu.rows[2])
        #expect(menu.row(selected: 7) == menu.rows[2])
        #expect(menu.rows.filter { $0.roads.contains("Saddle Peak Road") } == [menu.rows[2]])
        #expect(try HandoffDrive.saddlePeak.url(row: nil) == (try HandoffDrive.saddlePeak.url()))
    }

    @Test("the paste for each selected row is that row's printed URL, then its roads, the line and the timing")
    func clipboardPayloadForEachSelectedRowIsTheCLIURL() throws {
        let menu = try Self.menu()
        let printed = try Self.printed().filter { $0.hasPrefix("URL ") }.map { String($0.split(separator: " ").last!) }
        #expect(printed.count == menu.rows.count)
        let (straightLine, timing) = ("the straight line", HandoffDrive.saddlePeak.timingSentence)
        for (index, url) in printed.enumerated() {
            let roads = menu.rows[index].roadList
            let pasted = HandoffDrive.saddlePeak.clipboardPayload(row: menu.row(selected: index), roadList: roads,
                                                                   straightLine: straightLine, timing: timing)
            #expect(pasted == [url, roads, straightLine, timing].joined(separator: "\n"), "row \(index)")
        }
    }

    @Test("the selected row draws alone with the menu's box; the others are the muted lines")
    func selectedAndMutedGeoJSON() throws {
        let menu = try Self.menu()
        let all = menu.rows.flatMap(\.line)
        #expect(menu.bbox == [all.map { $0[0] }.min()!, all.map { $0[1] }.min()!,
                              all.map { $0[0] }.max()!, all.map { $0[1] }.max()!])
        func lines(_ data: Data) throws -> ([Double], [[[Double]]]) {
            let doc = try #require(try JSONSerialization.jsonObject(with: data) as? [String: Any])
            let features = try #require(doc["features"] as? [[String: Any]])
            let drawn = features.compactMap { ($0["geometry"] as? [String: Any])?["coordinates"] as? [[Double]] }
            return (doc["bbox"] as? [Double] ?? [], drawn)
        }
        for index in menu.rows.indices {
            let (box, selected) = try lines(menu.geoJSON(selected: index))
            #expect(box == menu.bbox)
            #expect(selected == [menu.rows[index].line])
            let (_, muted) = try lines(menu.mutedGeoJSON(selected: index))
            #expect(muted == menu.rows.indices.filter { $0 != index }.map { menu.rows[$0].line })
        }
    }

    @Test("only the Saddle Peak drive names a menu, and it is the committed file")
    func onlySaddlePeakNamesTheCommittedMenu() throws {
        #expect(FileManager.default.fileExists(atPath: Self.bundleURL.path))
        #expect(HandoffDrive.allCases.filter { $0.menuResource != nil } == [.saddlePeak])
    }
}

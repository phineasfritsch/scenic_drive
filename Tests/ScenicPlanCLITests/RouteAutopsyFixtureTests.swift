import Foundation
import Testing
import ScenicKit
@testable import ScenicPlanCLI

/// T-0327: `ops/route-autopsy ... --fixture <dir>` - the playbook's "a bad drive becomes a pinned negative
/// fixture before any weight changes". Driven through `AutopsyCommand.run(AutopsyArguments.parse(...))`.
///
/// The fixture is written into a fresh temporary directory whose path carries a `Tests` component (the CLI
/// refuses any other), and every file in it is checked by exact equality: the copied recordings and terms
/// byte for byte against their sources, `autopsy.txt` against a replay of the tool over the written fixture,
/// and `fixture.json` against the text recomputed here from the printed table.
@Suite("ops/route-autopsy --fixture (T-0327)")
struct RouteAutopsyFixtureTests {

    static func scratch() -> URL {
        FileManager.default.temporaryDirectory
            .appendingPathComponent("t0327-\(UUID().uuidString)")
            .appendingPathComponent("Tests/Fixtures/negative/westwood-malibu-pch")
    }

    static func arguments(fixture: URL?, recorded: Bool = true) -> [String] {
        var typed = ["34.0669,-118.4399", "34.0356,-118.6894", "25"]
        typed += recorded ? ["--recorded", RouteAutopsyGoldenTests.recording.path]
                          : ["--router", "http://127.0.0.1:8989"]
        typed += ["--terms", RouteAutopsyGoldenTests.termsFile.path]
        if let fixture { typed += ["--fixture", fixture.path] }
        return typed
    }

    @Test("--fixture writes the traced recordings, the terms, fixture.json and an autopsy that replays")
    func theFixtureIsWrittenWholeAndReplays() throws {
        let dir = Self.scratch()
        defer { try? FileManager.default.removeItem(at: dir.deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()) }
        let printed = try AutopsyCommand.run(AutopsyArguments.parse(Self.arguments(fixture: dir)))

        let recorded = ["fastest.json", "lambda-0.json", "lambda-4.json", "lambda-2.json", "lambda-3.json",
                        "lambda-3.5.json", "lambda-3.25.json"]
        let written = try FileManager.default.contentsOfDirectory(atPath: dir.path).sorted()
        #expect(written == (recorded + ["autopsy.txt", "fixture.json", "terms.json"]).sorted())
        for name in recorded {
            let source = RouteAutopsyGoldenTests.recording.appendingPathComponent(name)
            #expect(FileManager.default.contents(atPath: dir.appendingPathComponent(name).path)
                == FileManager.default.contents(atPath: source.path), "\(name)")
        }
        #expect(FileManager.default.contents(atPath: dir.appendingPathComponent("terms.json").path)
            == FileManager.default.contents(atPath: RouteAutopsyGoldenTests.termsFile.path))

        // The pinned text is the autopsy of the FIXTURE, replayed by the shipping entry point.
        let replay = try AutopsyCommand.run(AutopsyArguments.parse(
            ["34.0669,-118.4399", "34.0356,-118.6894", "25", "--recorded", dir.path,
             "--terms", dir.appendingPathComponent("terms.json").path]))
        let autopsy = try #require(FileManager.default.contents(atPath: dir.appendingPathComponent("autopsy.txt").path))
        #expect(String(decoding: autopsy, as: UTF8.self) == replay.joined(separator: "\n") + "\n")
        #expect(printed == replay + ["FIXTURE \(dir.path) files=10 verdict=negative"])

        // fixture.json, recomputed from the printed table's way column (consecutive repeats collapsed).
        let header = try #require(replay.firstIndex { $0.hasPrefix("WAY ") })
        var ids: [String] = []
        for line in replay[(header + 1)...] {
            let c = RouteAutopsyGoldenTests.cells(line)
            guard c.count == 9 else { continue }
            if ids.last != c[0] { ids.append(c[0]) }
        }
        #expect(ids.count == 166)
        let expected = "{\n  \"verdict\": \"negative\",\n  \"origin\": \"34.0669,-118.4399\",\n"
            + "  \"destination\": \"34.0356,-118.6894\",\n  \"budgetMinutes\": 25.0,\n"
            + "  \"lambda\": \"3.25\",\n  \"terms\": \"terms.json\",\n"
            + "  \"wayIds\": [" + ids.joined(separator: ", ") + "]\n}\n"
        let fixture = try #require(FileManager.default.contents(atPath: dir.appendingPathComponent("fixture.json").path))
        #expect(String(decoding: fixture, as: UTF8.self) == expected)
    }

    @Test("--fixture refuses outside Tests/, over an existing directory, and without --recorded")
    func theFixtureRefusesWhatItCannotPin() throws {
        let outside = FileManager.default.temporaryDirectory.appendingPathComponent("t0327-\(UUID().uuidString)")
        #expect(throws: AutopsyFixture.Failure.self) {
            try AutopsyCommand.run(AutopsyArguments.parse(Self.arguments(fixture: outside)))
        }
        #expect(!FileManager.default.fileExists(atPath: outside.path))

        let existing = Self.scratch()
        defer { try? FileManager.default.removeItem(at: existing.deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()) }
        try FileManager.default.createDirectory(at: existing, withIntermediateDirectories: true)
        #expect(throws: AutopsyFixture.Failure.self) {
            try AutopsyCommand.run(AutopsyArguments.parse(Self.arguments(fixture: existing)))
        }
        #expect(try FileManager.default.contentsOfDirectory(atPath: existing.path).isEmpty)

        #expect(throws: PlanArguments.Failure.self) {
            try AutopsyArguments.parse(Self.arguments(fixture: Self.scratch(), recorded: false))
        }
    }

    @Test("no arguments is a usage refusal, and the usage names every flag")
    func noArgumentsIsUsage() {
        #expect(throws: PlanArguments.Failure.self) { try AutopsyArguments.parse([]) }
        for flag in ["--recorded", "--router", "--terms", "--fixture", "--max-evaluations"] {
            #expect(AutopsyArguments.usage.contains(flag), "\(flag)")
        }
    }
}

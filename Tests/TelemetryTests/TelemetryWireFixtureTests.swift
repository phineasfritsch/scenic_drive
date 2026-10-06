import Foundation
import Testing
@testable import Telemetry

/// The device half of the Worker's /telemetry contract (T-0279 R10): Tests/Fixtures/t0279/datapoints.jsonl holds,
/// one line per row, the JSONEncoder bytes of `TelemetryEvent.dataPoint` - the shipping encoder - for every row of
/// TelemetryEventEncodingTests, every case of every label enum and the ruled bounds of every number (R3). The
/// Worker's suite reads the same file and must accept every line and write it unchanged. Compared BY BYTES; written
/// only when T0279_RECORD=1 (the initial recording, or a re-recording a reviewer reads in the diff).
@Suite("Telemetry wire fixture") struct TelemetryWireFixtureTests {
    static let origin = TelemetryEventEncodingTests.origin

    /// Every row the Worker must accept: the encoding table, each label of each closed enum, and R3's bounds.
    static var events: [TelemetryEvent] {
        var all = TelemetryEventEncodingTests.rows.map { $0.event }
        all += PlanFeature.allCases.map { .planRequested(feature: $0, budgetMinutes: 30, origin: origin) }
        all += PlanResultKind.allCases.map { .planResult($0) }
        all += HandoffApp.allCases.map { .handoffTapped($0) }
        all += SurpriseNotThisReason.allCases.map { .surpriseNotThis($0) }
        all += PaywallStep.allCases.map { .paywall($0) }
        all += [
            .planRequested(feature: .loop, budgetMinutes: 0, origin: origin),
            .planRequested(feature: .surprise, budgetMinutes: 1440, origin: origin),
            .driveCompleted(CompletionPercent(fraction: 0), deviations: 0),
            .driveCompleted(CompletionPercent(fraction: 1), deviations: 1000),
            .driveAbandoned(CompletionPercent(fraction: 0)),
            .driveAbandoned(CompletionPercent(fraction: 1)),
            .corpusActivated(version: 0),
            .corpusActivated(version: 2_147_483_647),
        ]
        var unique: [TelemetryEvent] = []
        for event in all where !unique.contains(where: { $0.dataPoint == event.dataPoint }) {
            unique.append(event)
        }
        return unique
    }

    static var fixtureURL: URL {
        URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("Fixtures/t0279/datapoints.jsonl")
    }

    /// The fixture's bytes as the shipping encoder produces them: one sorted-keys JSON object per line, LF-ended.
    static func encoded() throws -> Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        var out = Data()
        for event in events {
            out.append(try encoder.encode(event.dataPoint))
            out.append(0x0A)
        }
        return out
    }

    @Test("the shared fixture is the Swift encoder's exact JSON for every row, by bytes")
    func fixtureIsTheEncodersBytes() throws {
        let bytes = try Self.encoded()
        if ProcessInfo.processInfo.environment["T0279_RECORD"] == "1" {
            try FileManager.default.createDirectory(at: Self.fixtureURL.deletingLastPathComponent(),
                                                    withIntermediateDirectories: true)
            try bytes.write(to: Self.fixtureURL)
        }
        let stored = try Data(contentsOf: Self.fixtureURL)
        #expect(stored == bytes)
    }

    @Test("the fixture names all fifteen wire names and holds no row twice")
    func fixtureCoversEveryWireName() throws {
        let points = Self.events.map { $0.dataPoint }
        let names = Set(points.map { $0.blobs[0] })
        let expected = Set(TelemetryEventKind.allCases.filter { $0 != .paywall }.map { $0.rawValue }
            + PaywallStep.allCases.map { "paywall_" + $0.rawValue })
        #expect(names == expected)
        #expect(names.count == 15)
        let lines = String(decoding: try Self.encoded(), as: UTF8.self).split(separator: "\n")
        #expect(lines.count == Set(lines).count)
        #expect(lines.count == 36)
    }
}

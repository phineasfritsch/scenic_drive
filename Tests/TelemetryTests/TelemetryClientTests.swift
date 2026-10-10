import Foundation
import Testing
@testable import Telemetry

/// T-0355 acceptance 1: the device's POST /telemetry through the SHIPPING `TelemetryClient.record`, by exact equality of
/// the whole request (R2), the waiting bound (R3, every side of `capacity`) and the fail-quiet drop (R3).
@Suite("TelemetryClient") struct TelemetryClientTests {
    static let device = UUID(uuidString: "6F9619FF-8B86-D011-B42D-00C04FC964FF")!
    static let base = URL(string: "https://api.example.test")!
    static let telemetryURL = "https://api.example.test/telemetry"

    /// The request recomputed from the committed data point, independently of the client's own body type.
    static func expected(_ events: [TelemetryEvent]) throws -> TelemetryRequest {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let body = try encoder.encode(["events": events.map(\.dataPoint)])
        return TelemetryRequest(url: URL(string: telemetryURL)!, method: "POST",
                                headers: ["content-type": "application/json",
                                          "x-scenic-device": "6f9619ff-8b86-d011-b42d-00c04fc964ff"],
                                body: body)
    }

    static func client(_ transport: ScriptedTelemetryTransport, base: URL = base) -> TelemetryClient {
        TelemetryClient(base: base, device: device, transport: transport)
    }

    @Test func everyEventPostsExactlyItsRequest() async throws {
        for base in [Self.base, URL(string: "https://api.example.test/")!] {
            for row in TelemetryEventEncodingTests.rows {
                let transport = ScriptedTelemetryTransport()
                await Self.client(transport, base: base).record(row.event)
                let sent = await transport.requests
                #expect(sent == [try Self.expected([row.event])], "\(row.event) from \(base)")
            }
        }
        let literal: [(TelemetryEvent, String)] = [
            (.previewShown,
             #"{"events":[{"blobs":["preview_shown","",""],"doubles":[0,0],"indexes":["preview_shown"]}]}"#),
            (.planRequested(feature: .scenic, budgetMinutes: 25, origin: TelemetryEventEncodingTests.origin),
             #"{"events":[{"blobs":["plan_requested","scenic","850dab63fffffff"],"doubles":[25,0],"indexes":["plan_requested"]}]}"#),
        ]
        for (event, bytes) in literal {
            let transport = ScriptedTelemetryTransport()
            await Self.client(transport).record(event)
            let sent = await transport.requests
            #expect(sent.map { String(decoding: $0.body, as: UTF8.self) } == [bytes])
        }
    }

    /// One event in flight, then `waiting` more recorded behind it: the next post carries exactly the first
    /// min(waiting, capacity) of them in order and the rest are dropped. Rows sit on every side of the bound.
    @Test(arguments: [0, 1, TelemetryClient.capacity - 1, TelemetryClient.capacity, TelemetryClient.capacity + 1,
                      TelemetryClient.capacity + 7])
    func waitingBoundTable(waiting: Int) async throws {
        let transport = ScriptedTelemetryTransport(holdFirst: true)
        let client = Self.client(transport)
        let first = TelemetryEvent.driveStarted
        let inFlight = Task { await client.record(first) }
        while await !transport.isHolding { await Task.yield() }
        let behind = (0..<waiting).map { TelemetryEvent.driveCompleted(CompletionPercent(fraction: Double($0) / 100),
                                                                      deviations: $0) }
        for event in behind { await client.record(event) }
        await transport.release()
        await inFlight.value
        let kept = Array(behind.prefix(TelemetryClient.capacity))
        let expected = try [Self.expected([first])] + (kept.isEmpty ? [] : [Self.expected(kept)])
        let sent = await transport.requests
        #expect(sent == expected, "waiting \(waiting)")
        #expect(sent.count == (waiting == 0 ? 1 : 2))
    }

    /// Whatever the first post's outcome, its batch is gone: the next record posts only the next event. Every
    /// outcome is crossed with two event variants, and no row's expectation ignores its variant.
    @Test func everyOutcomeDropsTheBatch() async throws {
        let outcomes: [ScriptedTelemetryTransport.Outcome] = [.fails, .status(200), .status(400), .status(429),
                                                              .status(503)]
        let variants: [(TelemetryEvent, TelemetryEvent)] = [
            (.previewShown, .surpriseShown),
            (.planRequested(feature: .loop, budgetMinutes: 90, origin: TelemetryEventEncodingTests.otherOrigin),
             .planResult(.quotaExceeded)),
        ]
        #expect(try Self.expected([variants[0].1]) != Self.expected([variants[1].1]))
        for outcome in outcomes {
            for (firstEvent, next) in variants {
                let transport = ScriptedTelemetryTransport(outcomes: [outcome])
                let client = Self.client(transport)
                await client.record(firstEvent)
                await client.record(next)
                let sent = await transport.requests
                #expect(sent == [try Self.expected([firstEvent]), try Self.expected([next])], "\(outcome) \(next)")
            }
        }
    }

    /// The waiting bound is the Worker's per-request cap, read from the Worker's own source.
    @Test func capacityIsTheWorkersCap() throws {
        let source = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().appendingPathComponent("services/api/src/telemetryPoint.ts")
        let text = try String(contentsOf: source, encoding: .utf8)
        let prefix = "export const MAX_TELEMETRY_EVENTS_PER_REQUEST = "
        let line = try #require(text.split(separator: "\n").first { $0.hasPrefix(prefix) })
        #expect(line == Substring(prefix + "\(TelemetryClient.capacity);"))
    }

    @Test func recordedOnlyAfterTheFirstPostReturns() async throws {
        let transport = ScriptedTelemetryTransport()
        let client = Self.client(transport)
        #expect(await transport.requests.isEmpty)
        await client.record(.surpriseShown)
        #expect(await transport.requests == [try Self.expected([.surpriseShown])])
    }
}

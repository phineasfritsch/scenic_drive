import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0314 R3/R6/R7 through the live planner: the disclaimer gate counted at the transport (P-SAFE-03), the answer
/// reaching the sheet as exactly its preview after the DEVICE's retrace check, and a loop that fails that check (or a
/// spent day) reaching the sheet as its failure.
@Suite("LoopSheetGateTests")
struct LoopSheetGateTests {
    static let pier = PlanPlace(id: 7, name: "Santa Monica Pier",
                                coordinate: Coordinate(latitude: 34.01862, longitude: -118.49153))

    static func ready(accepted: Bool) -> LoopSheet {
        var sheet = LoopSheet(disclaimerAccepted: accepted)
        sheet.search("pier")
        sheet.choose(pier)
        return sheet
    }

    static func drive(_ sheet: inout LoopSheet, _ transport: CountingPlanTransport) async {
        guard let ticket = sheet.startPlanning() else { return }
        let planner = ClientLoopPlanner(client: LoopClient(base: LoopWire.base, transport: transport,
                                                           installID: PlanWire.install))
        sheet.finish(ticket, with: await planner.plan(ticket))
    }

    static func failure(after body: String, status: Int = 200) async -> LoopFailure? {
        let transport = CountingPlanTransport(reply: LoopWire.reply(status, body))
        var sheet = Self.ready(accepted: true)
        await Self.drive(&sheet, transport)
        guard case .failed(_, let failure) = sheet.state else { return nil }
        return failure
    }

    @Test("P-SAFE-03: no loop request is made before the disclaimer is accepted")
    func noRequestBeforeAcceptance() async {
        let transport = CountingPlanTransport(reply: LoopWire.reply(200, LoopWire.squareBody))
        var sheet = Self.ready(accepted: false)
        await Self.drive(&sheet, transport)
        await Self.drive(&sheet, transport)
        #expect(await transport.count == 0)
        #expect(sheet.state == .chosen(Self.pier))
        sheet.setDisclaimerAccepted(true)
        await Self.drive(&sheet, transport)
        #expect(await transport.count == 1)
    }

    @Test("a clean loop reaches the sheet as exactly its preview, with the device's retrace fraction")
    func previewReachesSheet() async throws {
        let transport = CountingPlanTransport(reply: LoopWire.reply(200, LoopWire.squareBody))
        var sheet = Self.ready(accepted: true)
        sheet.setMinutes(75)
        await Self.drive(&sheet, transport)
        #expect(await transport.requests == [LoopClientRequestTests.request(
            #"{"minutes":75,"start":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#)])
        let measured = try #require(RetraceDetector.retraceFraction(LoopWire.square))
        #expect(measured != 0.02)
        #expect(measured <= RetraceDetector.maxRetraceFraction)
        guard case .preview(let ticket, let shown) = sheet.state else {
            Issue.record("the sheet is \(sheet.state), not a preview")
            return
        }
        #expect(shown == LoopPreview(path: LoopWire.square, waypoints: LoopWire.pins, durationSeconds: 2_700,
                                     distanceMeters: 10_000, retraceFraction: measured, etaIsEstimate: true))
        #expect(ticket.start == Coordinate(latitude: 34.02, longitude: -118.49))
        #expect(ticket.minutes == 75 && ticket.serial == 1)
    }

    @Test("a loop the device finds retraced is not shown: noCleanLoop")
    func retracedLoopIsNotShown() async {
        #expect(RetraceDetector.retraceFraction(LoopWire.outAndBack).map { $0 > RetraceDetector.maxRetraceFraction }
                == true)
        #expect(await Self.failure(after: LoopWire.outAndBackBody) == .noCleanLoop)
        #expect(await Self.failure(after: LoopWire.onePointBody) == .noCleanLoop)
    }

    /// rv1-t0314 B1: the bound itself, through the seam `outcome(of:)` delegates to (and `plan(_:)` runs), each
    /// expected outcome built whole. No route fixture lands on 0.15, so the fraction is given, not measured.
    static let bounds: [(String, Double?, Bool)] = [
        ("exactly 0.15", RetraceDetector.maxRetraceFraction, true),
        ("just under 0.15", RetraceDetector.maxRetraceFraction.nextDown, true),
        ("just over 0.15", RetraceDetector.maxRetraceFraction.nextUp, false),
        ("0.3", 0.3, false),
        ("NaN", Double.nan, false),
        ("unmeasurable", nil, false),
    ]

    @Test("the device's retrace limit is 0.15 inclusive at every bound", arguments: bounds.map(\.0))
    func retraceBound(_ label: String) throws {
        let row = try #require(Self.bounds.first { $0.0 == label })
        let response = LoopWire.response()
        let expected: LoopOutcome = row.2
            ? .preview(LoopPreview(path: LoopWire.square, waypoints: LoopWire.pins, durationSeconds: 2_700,
                                   distanceMeters: 10_000, retraceFraction: try #require(row.1),
                                   etaIsEstimate: true))
            : .failure(.noCleanLoop)
        #expect(RetraceDetector.maxRetraceFraction == 0.15)
        #expect(ClientLoopPlanner.outcome(of: response, fraction: row.1) == expected, "\(label)")
    }

    @Test("the planner decides on the device's own measured fraction")
    func plannerDelegatesToSeam() {
        for route in [LoopWire.square, LoopWire.outAndBack, [LoopWire.start]] {
            let response = LoopWire.response(route: route)
            #expect(ClientLoopPlanner.outcome(of: response)
                    == ClientLoopPlanner.outcome(of: response, fraction: RetraceDetector.retraceFraction(route)))
        }
    }

    @Test("a 200 saying eta_is_estimate false reaches the sheet as a preview without the badge")
    func estimateFalseReachesSheet() async throws {
        let transport = CountingPlanTransport(reply: LoopWire.reply(200, LoopWire.falseEstimateBody))
        var sheet = Self.ready(accepted: true)
        await Self.drive(&sheet, transport)
        let measured = try #require(RetraceDetector.retraceFraction(LoopWire.square))
        guard case .preview(_, let shown) = sheet.state else {
            Issue.record("the sheet is \(sheet.state), not a preview")
            return
        }
        #expect(shown == LoopPreview(path: LoopWire.square, waypoints: LoopWire.pins, durationSeconds: 2_700,
                                     distanceMeters: 10_000, retraceFraction: measured, etaIsEstimate: false))
        #expect(await transport.count == 1)
    }

    @Test("a spent day and a refused loop reach the sheet as their failures")
    func failuresReachSheet() async {
        #expect(await Self.failure(after: #"{"error":"quota_exhausted","resets_at":"2026-10-09T00:00:00Z"}"#,
                                   status: 429) == .quotaExhausted)
        #expect(await Self.failure(after: #"{"error":"no_clean_loop"}"#, status: 422) == .noCleanLoop)
    }
}

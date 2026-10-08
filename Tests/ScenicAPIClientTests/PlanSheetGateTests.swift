import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0294 acceptance 3-4, through the shipping path the plan sheet's view runs: `startPlanning()` is the gate, its
/// ticket goes to `ClientPlanner.plan`, which calls `PlanClient.plan` over the counting transport, and `finish`
/// lands the outcome. Requests are counted on the wire, not inferred.
@Suite("PlanSheetGateTests")
struct PlanSheetGateTests {
    static let santaMonica = PlanPlace(id: 7, name: "Santa Monica Pier",
                                       coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let topanga = PlanPlace(id: 42, name: "Topanga Lookout",
                                   coordinate: Coordinate(latitude: 34.09312, longitude: -118.60071))

    /// Exactly the view's sequence (PlanSheetScreen.planDrive): no ticket, no call.
    static func drive(_ sheet: inout PlanSheet, _ planner: ClientPlanner) async {
        guard let ticket = sheet.startPlanning() else { return }
        sheet.finish(ticket, with: await planner.plan(ticket))
    }

    static func ready(accepted: Bool, budget: Int = 30) -> PlanSheet {
        var sheet = PlanSheet(disclaimerAccepted: accepted)
        sheet.search("santa", for: .start)
        sheet.choose(santaMonica)
        sheet.search("topanga", for: .destination)
        sheet.choose(topanga)
        sheet.setBudget(budget)
        return sheet
    }

    static func planner(_ transport: CountingPlanTransport, install: Bool = true) -> ClientPlanner {
        ClientPlanner(client: PlanClient(base: PlanWire.base, transport: transport,
                                         installID: install ? PlanWire.install : nil,
                                         accountToken: nil))
    }

    @Test("P-SAFE-03: from first launch no plan request is made before the disclaimer is accepted")
    func noRequestBeforeAcceptance() async throws {
        let transport = CountingPlanTransport(reply: try PlanWire.recordedReply("200-plan"))
        var sheet = Self.ready(accepted: false)
        await Self.drive(&sheet, Self.planner(transport))
        await Self.drive(&sheet, Self.planner(transport))
        #expect(await transport.count == 0)
        #expect(sheet.state == .chosen(Self.topanga))
        sheet.setDisclaimerAccepted(true)
        await Self.drive(&sheet, Self.planner(transport))
        #expect(await transport.count == 1)
        guard case .preview = sheet.state else {
            Issue.record("after acceptance the sheet is \(sheet.state), not a preview")
            return
        }
    }

    @Test("P-SAFE-03: after a failure or a preview, no request once acceptance is withdrawn, through the planner")
    func noRequestOnReplanAfterWithdrawal() async throws {
        let quota = CountingPlanTransport(reply: try PlanWire.recordedReply("429-quota-exhausted"))
        var failed = Self.ready(accepted: true)
        await Self.drive(&failed, Self.planner(quota))
        #expect(await quota.count == 1)
        let failedState = failed.state
        guard case .failed(_, .quotaExhausted) = failedState else {
            Issue.record("429 left the sheet at \(failedState)")
            return
        }
        failed.setDisclaimerAccepted(false)
        await Self.drive(&failed, Self.planner(quota))
        #expect(await quota.count == 1)
        #expect(failed.state == failedState)
        let ok = CountingPlanTransport(reply: try PlanWire.recordedReply("200-plan"))
        var shown = Self.ready(accepted: true)
        await Self.drive(&shown, Self.planner(ok))
        #expect(await ok.count == 1)
        let shownState = shown.state
        shown.setDisclaimerAccepted(false)
        await Self.drive(&shown, Self.planner(ok))
        #expect(await ok.count == 1)
        #expect(shown.state == shownState)
        shown.setDisclaimerAccepted(true)
        await Self.drive(&shown, Self.planner(ok))
        #expect(await ok.count == 2)
    }

    @Test("P-PRIV-06: a typed start leaves as ONE coordinate at 2 dp, the body equal to its recomputation")
    func typedStartBodyWhole() async throws {
        let transport = CountingPlanTransport(reply: try PlanWire.recordedReply("200-plan"))
        var sheet = Self.ready(accepted: true, budget: 45)
        await Self.drive(&sheet, Self.planner(transport))
        let requests = await transport.requests
        #expect(requests.count == 1)
        let sent = try JSONSerialization.jsonObject(with: try #require(requests.first).body) as? NSDictionary
        let expected: NSDictionary = ["origin": ["lat": 34.01, "lon": -118.5], "destination": ["place": "42"],
                                      "budget_minutes": 45, "vehicle": "standard"]
        #expect(sent == expected)
    }

    @Test("a 200 reaches the sheet as the preview of exactly that response")
    func previewWhole() async throws {
        let reply = try PlanWire.recordedReply("200-plan-hazards")
        var sheet = Self.ready(accepted: true)
        await Self.drive(&sheet, Self.planner(CountingPlanTransport(reply: reply)))
        let direct = try await PlanClient(base: PlanWire.base, transport: CountingPlanTransport(reply: reply),
                                          installID: PlanWire.install, accountToken: nil)
            .plan(from: Coordinate(latitude: 34.01, longitude: -118.5), to: 42, budgetMinutes: 30)
        let expected = PlanPreview(route: direct.route, etaSeconds: direct.etaSeconds,
                                   fastestEtaSeconds: direct.fastestEtaSeconds, etaIsEstimate: direct.etaIsEstimate,
                                   hazards: direct.hazards.map {
                                       PlanHazardRun(kind: $0.kind, value: $0.value, fromIndex: $0.fromIndex,
                                                     toIndex: $0.toIndex)
                                   }, waypoints: direct.waypoints, lambda: direct.lambda)
        #expect(!expected.hazards.isEmpty)
        #expect(expected.hazards.map { [$0.fromIndex, $0.toIndex] } == direct.hazards.map { [$0.fromIndex, $0.toIndex] })
        guard case .preview(_, let shown) = sheet.state else {
            Issue.record("the sheet is \(sheet.state), not a preview")
            return
        }
        #expect(shown == expected)
    }

    /// Typed whole, so the compiler checks each pair without inferring the array.
    static let errorRows: [(PlanError, PlanSheetFailure)] = [
        (PlanError.quotaExhausted(resetsAt: Date(timeIntervalSince1970: 0)), PlanSheetFailure.quotaExhausted),
        (PlanError.planningPaused, PlanSheetFailure.planningPaused),
        (PlanError.routingOffline, PlanSheetFailure.routingOffline),
        (PlanError.noRoute, PlanSheetFailure.noRoute),
        (PlanError.regionUnsupported, PlanSheetFailure.regionUnsupported),
        (PlanError.attestUnsupported, PlanSheetFailure.attestUnsupported),
        (PlanError.offlineDuringDrive, PlanSheetFailure.offlineDuringDrive),
        (PlanError.noScenicAlternative, PlanSheetFailure.noScenicAlternative),
        (PlanError.unknownPlace, PlanSheetFailure.unknownPlace),
        (PlanError.planRefused(reason: "ceiling_breached"), PlanSheetFailure.planRefused),
        (PlanError.invalidRequest(detail: "x"), PlanSheetFailure.invalidRequest),
        (PlanError.refusedOnDevice(PlanRefusal.noInstallID), PlanSheetFailure.refusedOnDevice),
        (PlanError.unexpectedResponse(status: 418), PlanSheetFailure.unexpectedResponse),
    ]

    @Test("every PlanError reaches the sheet as its own PlanSheetFailure", arguments: errorRows)
    func errorMapsOneForOne(error: PlanError, failure: PlanSheetFailure) {
        #expect(error.failure == failure)
    }

    @Test("the failure table covers every PlanSheetFailure exactly once")
    func failureTableCount() {
        #expect(PlanSheetFailure.allCases.count == 13)
        #expect(Self.errorRows.map(\.1) == PlanSheetFailure.allCases)
    }

    @Test("Worker failures and a dead network reach the sheet as failed, through the planner")
    func failuresThroughPlanner() async throws {
        let quota = CountingPlanTransport(reply: try PlanWire.recordedReply("429-quota-exhausted"))
        var sheet = Self.ready(accepted: true)
        await Self.drive(&sheet, Self.planner(quota))
        guard case .failed(_, .quotaExhausted) = sheet.state else {
            Issue.record("429 left the sheet at \(sheet.state)")
            return
        }
        await Self.drive(&sheet, Self.planner(CountingPlanTransport.offline()))
        guard case .failed(_, .routingOffline) = sheet.state else {
            Issue.record("no reply left the sheet at \(sheet.state)")
            return
        }
        let silent = CountingPlanTransport(reply: try PlanWire.recordedReply("200-plan"))
        await Self.drive(&sheet, Self.planner(silent, install: false))
        #expect(await silent.count == 0)
        guard case .failed(_, .refusedOnDevice) = sheet.state else {
            Issue.record("no install id left the sheet at \(sheet.state)")
            return
        }
    }
}

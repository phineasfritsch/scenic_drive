import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0313 R4/R5 through the live planner: the disclaimer gate counted at the transport (P-SAFE-03), and the answer
/// reaching the sheet as exactly the itinerary of that response.
@Suite("TripSheetGateTests")
struct TripSheetGateTests {
    static let pier = PlanPlace(id: 7, name: "Santa Monica Pier",
                                coordinate: Coordinate(latitude: 34.01862, longitude: -118.49153))
    static let bigSur = PlanPlace(id: 42, name: "Big Sur", coordinate: Coordinate(latitude: 36.27, longitude: -121.81))

    static func ready(accepted: Bool) -> TripSheet {
        var sheet = TripSheet(disclaimerAccepted: accepted)
        sheet.search("pier", for: .start)
        sheet.choose(pier)
        sheet.search("big", for: .destination)
        sheet.choose(bigSur)
        return sheet
    }

    static func drive(_ sheet: inout TripSheet, _ transport: CountingPlanTransport) async {
        guard let ticket = sheet.startPlanning() else { return }
        let planner = ClientTripPlanner(client: TripClient(base: TripWire.base, transport: transport,
                                                           installID: PlanWire.install, accountToken: nil, session: nil))
        sheet.finish(ticket, with: await planner.plan(ticket))
    }

    @Test("P-SAFE-03: no trip request is made before the disclaimer is accepted")
    func noRequestBeforeAcceptance() async {
        let transport = CountingPlanTransport(reply: TripWire.reply(200, TripWire.previewBody))
        var sheet = Self.ready(accepted: false)
        await Self.drive(&sheet, transport)
        await Self.drive(&sheet, transport)
        #expect(await transport.count == 0)
        #expect(sheet.state == .chosen(Self.bigSur))
        sheet.setDisclaimerAccepted(true)
        await Self.drive(&sheet, transport)
        #expect(await transport.count == 1)
    }

    @Test("a preview reaches the sheet as exactly its itinerary: no path, so no per-day handoff")
    func previewItinerary() async {
        let transport = CountingPlanTransport(reply: TripWire.reply(200, TripWire.previewBody))
        var sheet = Self.ready(accepted: true)
        await Self.drive(&sheet, transport)
        let itinerary = TripItinerary(isFull: false, etaSeconds: 30_000, fastestEtaSeconds: 24_000,
                                      etaIsEstimate: true, days: [
                                          TripItineraryDay(day: 1, driveSeconds: 15_000, distanceMeters: 200_000,
                                                           overnight: true, path: nil),
                                          TripItineraryDay(day: 2, driveSeconds: 15_000, distanceMeters: 280_000,
                                                           overnight: false, path: nil)])
        guard case .itinerary(let ticket, let shown) = sheet.state else {
            Issue.record("the sheet is \(sheet.state), not an itinerary")
            return
        }
        #expect(shown == itinerary)
        #expect(ticket.origin == Coordinate(latitude: 34.02, longitude: -118.49))
    }

    @Test("a full answer carries each day's leg as its path")
    func fullItinerary() {
        #expect(ClientTripPlanner.itinerary(of: TripWire.full) == TripItinerary(
            isFull: true, etaSeconds: 31_000, fastestEtaSeconds: 24_000, etaIsEstimate: true, days: [
                TripItineraryDay(day: 1, driveSeconds: 31_000, distanceMeters: 480_000, overnight: false,
                                 path: TripWire.fullLeg)]))
    }

    @Test("a refused trip reaches the sheet as its failure")
    func failureReachesSheet() async {
        let transport = CountingPlanTransport(reply: TripWire.reply(422, #"{"error":"too_few_days"}"#))
        var sheet = Self.ready(accepted: true)
        await Self.drive(&sheet, transport)
        guard case .failed(_, let failure) = sheet.state else {
            Issue.record("the sheet is \(sheet.state), not failed")
            return
        }
        #expect(failure == .tooFewDays)
    }

    @Test("a dull trip reaches the sheet as nothingPretty from one request")
    func dullTripReachesSheet() async {
        let body = #"{"error":"nothing_pretty","days":5,"extra_budget_pct":40}"#
        let transport = CountingPlanTransport(reply: TripWire.reply(422, body))
        var sheet = Self.ready(accepted: true)
        await Self.drive(&sheet, transport)
        guard case .failed(_, let failure) = sheet.state else {
            Issue.record("the sheet is \(sheet.state), not failed")
            return
        }
        #expect(failure == .nothingPretty)
        #expect(await transport.count == 1)
    }
}

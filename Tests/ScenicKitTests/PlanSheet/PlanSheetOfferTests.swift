@testable import ScenicKit
import Testing

/// T-0334 A5: a nothing_pretty answer's offers become plans through THE GATE. `finish(.offered)` keeps the offer in
/// state; `takeMoreTime()` / `takeBackRoads()` each issue ONE ticket - compared whole - naming the minutes the
/// driver tapped, and nothing at all with the disclaimer withdrawn, with that offer absent, or from any other state.
@Suite("PlanSheetOfferTests")
struct PlanSheetOfferTests {
    static let full = PlanOffer(budgetMinutes: 25, moreTimeMinutes: 65, backRoadsEtaSeconds: 3578.87,
                                backRoadsBudgetMinutes: 32)
    static let bare = PlanOffer(budgetMinutes: 180, moreTimeMinutes: nil, backRoadsEtaSeconds: 3578.87,
                                backRoadsBudgetMinutes: nil)
    static let origin = PlanSheet.twoDecimals(PlanSheetTests.santaMonica.coordinate)

    /// Ready, budget 25, one plan in flight answered with `offer`: the state the card is drawn from.
    static func offered(_ offer: PlanOffer, accepted: Bool = true) -> (PlanSheet, PlanTicket) {
        var sheet = PlanSheetTests.ready(accepted: true)
        sheet.setBudget(25)
        let first = sheet.startPlanning()!
        sheet.finish(first, with: .offered(offer))
        sheet.setDisclaimerAccepted(accepted)
        return (sheet, first)
    }

    @Test("finish(.offered) holds the ticket and the offer, whole")
    func finishHoldsTheOffer() {
        let (sheet, first) = Self.offered(Self.full)
        #expect(sheet.state == .offered(first, Self.full))
        #expect(first == PlanTicket(serial: 1, origin: Self.origin, place: 42, budgetMinutes: 25))
    }

    @Test("+40 is one fresh plan at budget + 40, through the gate")
    func moreTimeIsOnePlan() {
        var (sheet, _) = Self.offered(Self.full)
        let ticket = sheet.takeMoreTime()
        let expected = PlanTicket(serial: 2, origin: Self.origin, place: 42, budgetMinutes: 65, allBackRoads: false)
        #expect(ticket == expected)
        #expect(sheet.state == .planning(expected))
        #expect(sheet.budgetMinutes == 65)
    }

    @Test("all back roads is one fresh plan naming the minutes that cover its ETA, through the gate")
    func backRoadsIsOnePlan() {
        var (sheet, _) = Self.offered(Self.full)
        let ticket = sheet.takeBackRoads()
        let expected = PlanTicket(serial: 2, origin: Self.origin, place: 42, budgetMinutes: 32, allBackRoads: true)
        #expect(ticket == expected)
        #expect(sheet.state == .planning(expected))
        #expect(sheet.budgetMinutes == 32)
    }

    @Test("P-SAFE-03: neither offer issues a ticket once the disclaimer is withdrawn; nothing changes")
    func gateHoldsForOffers() {
        var (sheet, first) = Self.offered(Self.full, accepted: false)
        #expect(sheet.takeMoreTime() == nil)
        #expect(sheet.takeBackRoads() == nil)
        #expect(sheet.state == .offered(first, Self.full))
        #expect(sheet.budgetMinutes == 25)
    }

    @Test("an offer the answer did not make issues nothing; nothing changes")
    func absentOfferIssuesNothing() {
        var (sheet, first) = Self.offered(Self.bare)
        #expect(sheet.takeMoreTime() == nil)
        #expect(sheet.takeBackRoads() == nil)
        #expect(sheet.state == .offered(first, Self.bare))
        #expect(sheet.budgetMinutes == 25)
    }

    @Test("from every state that is not .offered, neither offer issues a ticket",
          arguments: ["idle", "searching", "chosen", "planning", "preview", "failed"])
    func onlyFromOffered(_ path: String) {
        var sheet = PlanSheetTests.ready(accepted: true)
        sheet.setBudget(25)
        switch path {
        case "idle": sheet = PlanSheet(disclaimerAccepted: true)
        case "searching": sheet.search("x", for: .destination)
        case "chosen": break
        default:
            let ticket = sheet.startPlanning()!
            if path == "preview" { sheet.finish(ticket, with: .preview(PlanSheetTests.preview)) }
            if path == "failed" { sheet.finish(ticket, with: .failure(.nothingPretty)) }
        }
        let before = sheet
        #expect(sheet.takeMoreTime() == nil, "\(path)")
        #expect(sheet.takeBackRoads() == nil, "\(path)")
        #expect(sheet == before, "\(path)")
    }
}

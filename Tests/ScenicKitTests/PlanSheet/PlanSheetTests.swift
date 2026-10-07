@testable import ScenicKit
import Testing

/// T-0294 acceptance 2-4: the plan sheet's state machine (R2), its gate (R3) and its origin (R4), through the
/// shipping symbols the view calls - `search`, `choose`, `setBudget`, `startPlanning`, `finish`.
@Suite("PlanSheetTests")
struct PlanSheetTests {
    static let topanga = PlanPlace(id: 42, name: "Topanga Lookout",
                                   coordinate: Coordinate(latitude: 34.09312, longitude: -118.60071))
    static let santaMonica = PlanPlace(id: 7, name: "Santa Monica Pier",
                                       coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let preview = PlanPreview(route: [Coordinate(latitude: 34.01, longitude: -118.5)], etaSeconds: 3120,
                                     fastestEtaSeconds: 2280, etaIsEstimate: true, hazards: [])

    /// A sheet with both ends chosen, the way the view gets there: search a field, pick a result.
    static func ready(accepted: Bool) -> PlanSheet {
        var sheet = PlanSheet(disclaimerAccepted: accepted)
        sheet.search("santa", for: .start)
        sheet.choose(santaMonica)
        sheet.search("topanga", for: .destination)
        sheet.choose(topanga)
        return sheet
    }

    @Test("first launch: no ticket until the disclaimer is accepted, then one")
    func gateBeforeAcceptance() {
        var sheet = Self.ready(accepted: false)
        #expect(sheet.state == .chosen(Self.topanga))
        let issued1 = sheet.startPlanning()
        #expect(issued1 == nil)
        #expect(sheet.state == .chosen(Self.topanga))
        sheet.setDisclaimerAccepted(true)
        let ticket = sheet.startPlanning()
        #expect(ticket != nil)
        #expect(sheet.state == ticket.map { .planning($0) })
    }

    @Test("the ticket is the typed start at 2 dp, the destination's id and the budget, whole")
    func ticketWhole() {
        var sheet = Self.ready(accepted: true)
        sheet.setBudget(45)
        let ticket = sheet.startPlanning()
        #expect(ticket == PlanTicket(serial: 1, origin: Coordinate(latitude: 34.01, longitude: -118.5), place: 42,
                                     budgetMinutes: 45))
        #expect(sheet.start == Self.santaMonica && sheet.destination == Self.topanga)
    }

    /// rv1-t0294 B3: each axis to the nearest hundredth, half away from zero, on both signs. Every expected value
    /// was computed outside Swift (Python's Decimal of the double `x * 100`, ROUND_HALF_UP, over 100) and typed in.
    /// A fraction below, at and above one half on each axis and each sign, so `.rounded(.up)`, `.down`,
    /// `.towardZero` and `.toNearestOrEven` on either axis each change at least one row.
    @Test("the origin is each axis to the nearest hundredth, half away from zero, on every sign")
    func originRoundingTable() {
        let rows: [(typed: Coordinate, sent: Coordinate)] = [
            (Coordinate(latitude: 34.0012, longitude: -118.4912), Coordinate(latitude: 34.0, longitude: -118.49)),
            (Coordinate(latitude: 34.005, longitude: -118.005), Coordinate(latitude: 34.01, longitude: -118.01)),
            (Coordinate(latitude: 0.125, longitude: -0.125), Coordinate(latitude: 0.13, longitude: -0.13)),
            (Coordinate(latitude: 34.0051, longitude: -118.0051), Coordinate(latitude: 34.01, longitude: -118.01)),
            (Coordinate(latitude: -33.8612, longitude: 151.2012), Coordinate(latitude: -33.86, longitude: 151.2)),
            (Coordinate(latitude: -33.8688, longitude: 151.2093), Coordinate(latitude: -33.87, longitude: 151.21)),
            (Coordinate(latitude: -34.005, longitude: 118.005), Coordinate(latitude: -34.01, longitude: 118.01)),
            (Coordinate(latitude: -0.125, longitude: 0.125), Coordinate(latitude: -0.13, longitude: 0.13)),
        ]
        for row in rows {
            var sheet = PlanSheet(disclaimerAccepted: true)
            sheet.search("start", for: .start)
            sheet.choose(PlanPlace(id: 3, name: "Typed start", coordinate: row.typed))
            sheet.search("topanga", for: .destination)
            sheet.choose(Self.topanga)
            sheet.setBudget(30)
            let ticket = sheet.startPlanning()
            #expect(ticket == PlanTicket(serial: 1, origin: row.sent, place: 42, budgetMinutes: 30),
                    "typed \(row.typed)")
        }
    }

    @Test("choosing fills the field being searched and keeps the other")
    func chooseFillsItsField() {
        var sheet = Self.ready(accepted: true)
        let pier = PlanPlace(id: 9, name: "Malibu Pier", coordinate: Coordinate(latitude: 34.0379, longitude: -118.677))
        sheet.search("malibu", for: .start)
        #expect(sheet.state == .searching(.start, "malibu"))
        sheet.choose(pier)
        #expect(sheet.start == pier && sheet.destination == Self.topanga && sheet.state == .chosen(Self.topanga))
        sheet.search("", for: .destination)
        sheet.endSearch()
        #expect(sheet.state == .chosen(Self.topanga))
    }

    @Test("no ticket from idle, searching or planning, nor without a start")
    func noTicketOutsideChosen() {
        var empty = PlanSheet(disclaimerAccepted: true)
        let issued2 = empty.startPlanning()
        #expect(issued2 == nil && empty.state == .idle)
        var noStart = PlanSheet(disclaimerAccepted: true)
        noStart.search("topanga", for: .destination)
        noStart.choose(Self.topanga)
        let issued3 = noStart.startPlanning()
        #expect(issued3 == nil && noStart.state == .chosen(Self.topanga))
        var sheet = Self.ready(accepted: true)
        sheet.search("x", for: .destination)
        let issued4 = sheet.startPlanning()
        #expect(issued4 == nil && sheet.state == .searching(.destination, "x"))
        sheet.endSearch()
        let first = sheet.startPlanning()
        #expect(first != nil)
        let issued5 = sheet.startPlanning()
        #expect(issued5 == nil)
        sheet.search("y", for: .destination)
        #expect(sheet.state == first.map { .planning($0) })
    }

    @Test("a reply lands only on the ticket in flight; a stale one is dropped")
    func staleReplyDropped() throws {
        var sheet = Self.ready(accepted: true)
        let issued6 = sheet.startPlanning()
        let first = try #require(issued6)
        sheet.finish(first, with: .failure(.routingOffline))
        #expect(sheet.state == .failed(first, .routingOffline))
        let issued7 = sheet.startPlanning()
        let second = try #require(issued7)
        #expect(second.serial == 2)
        sheet.finish(first, with: .preview(Self.preview))
        #expect(sheet.state == .planning(second))
        sheet.finish(second, with: .preview(Self.preview))
        #expect(sheet.state == .preview(second, Self.preview))
        let issued8 = sheet.startPlanning()
        let third = try #require(issued8)
        #expect(third.serial == 3)
    }

    /// The three states a plan can be launched from. Each row is reached with acceptance ON, then acceptance is
    /// withdrawn: the gate must refuse on every path, not only on the first launch (P-SAFE-03, class 1).
    static let launchPaths = ["chosen", "failed", "preview"]

    /// The sheet at `path`, reached the way the view gets there.
    static func reach(_ path: String) -> PlanSheet {
        var sheet = ready(accepted: true)
        guard path != "chosen", let ticket = sheet.startPlanning() else { return sheet }
        sheet.finish(ticket, with: path == "failed" ? .failure(.routingOffline) : .preview(preview))
        return sheet
    }

    /// The state `reach(path)` must be in, recomputed per row, so no row silently tests another row's state.
    static func expectedState(_ path: String) -> PlanSheetState {
        let first = PlanTicket(serial: 1, origin: Coordinate(latitude: 34.01, longitude: -118.5), place: 42,
                               budgetMinutes: 30)
        switch path {
        case "failed": return .failed(first, .routingOffline)
        case "preview": return .preview(first, preview)
        default: return .chosen(topanga)
        }
    }

    @Test("the gate holds on every path: acceptance withdrawn, no ticket from chosen, failed or preview",
          arguments: launchPaths)
    func gateOnEveryPath(path: String) {
        var sheet = Self.reach(path)
        #expect(sheet.state == Self.expectedState(path))
        sheet.setDisclaimerAccepted(false)
        let refused = sheet.startPlanning()
        #expect(refused == nil)
        #expect(sheet.state == Self.expectedState(path))
        sheet.setDisclaimerAccepted(true)
        let issued = sheet.startPlanning()
        #expect(issued?.serial == (path == "chosen" ? 1 : 2))
        #expect(sheet.state == issued.map { .planning($0) })
    }

    @Test("inputs are frozen while a plan is in flight: the budget, a search, a pick")
    func inputsFrozenInFlight() throws {
        var sheet = Self.ready(accepted: true)
        sheet.setBudget(45)
        let issued = sheet.startPlanning()
        let ticket = try #require(issued)
        #expect(ticket.budgetMinutes == 45)
        for minutes in [Int.min, -1, 0, 44, 46, 90, PlanSheet.maxBudgetMinutes, Int.max] {
            sheet.setBudget(minutes)
            #expect(sheet.budgetMinutes == 45)
            #expect(sheet.state == .planning(ticket))
        }
        let pier = PlanPlace(id: 9, name: "Malibu Pier", coordinate: Coordinate(latitude: 34.0379, longitude: -118.677))
        sheet.search("malibu", for: .start)
        sheet.choose(pier)
        sheet.endSearch()
        #expect(sheet.state == .planning(ticket))
        #expect(sheet.start == Self.santaMonica && sheet.destination == Self.topanga)
        sheet.finish(ticket, with: .preview(Self.preview))
        #expect(sheet.state == .preview(ticket, Self.preview))
        #expect(sheet.budgetMinutes == ticket.budgetMinutes)
        sheet.setBudget(90)
        #expect(sheet.budgetMinutes == 90)
        let next = sheet.startPlanning()
        #expect(next?.budgetMinutes == 90)
    }

    static let budgetRows: [(Int, Int)] = [
        (Int.min, 0), (-1, 0), (0, 0), (1, 1), (179, 179), (180, 180), (181, 180), (Int.max, 180),
    ]

    @Test("the extra time is clamped to 0...180 at every bound", arguments: budgetRows)
    func budgetBounds(minutes: Int, kept: Int) {
        var sheet = Self.ready(accepted: true)
        sheet.setBudget(minutes)
        #expect(sheet.budgetMinutes == kept)
        let issued9 = sheet.startPlanning()
        #expect(issued9?.budgetMinutes == kept)
    }

    @Test("the preview's ETA line against the fastest, rounded, never negative")
    func etaLine() {
        #expect(Self.preview.etaLine == "52 min · 14 min longer than the fastest way")
        let same = PlanPreview(route: [], etaSeconds: 1229, fastestEtaSeconds: 1213.65, etaIsEstimate: false, hazards: [])
        #expect(same.etaLine == "20 min · about as quick as the fastest way")
        let quicker = PlanPreview(route: [], etaSeconds: 1000, fastestEtaSeconds: 1300, etaIsEstimate: true, hazards: [])
        #expect(quicker.extraMinutes == 0 && quicker.etaLine == "17 min · about as quick as the fastest way")
        #expect(Self.preview.showsEstimateBadge && !same.showsEstimateBadge)
    }
}

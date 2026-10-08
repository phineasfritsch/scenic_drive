@testable import ScenicKit
import Testing

/// T-0313 R4: the road-trip sheet's transitions, every state x every event, compared WHOLE (state, both places, days,
/// percent, the ticket returned), plus every bound of days and percent and the 2-dp cut of the one coordinate.
@Suite("TripSheetTests")
struct TripSheetTests {
    static let pier = PlanPlace(id: 7, name: "Santa Monica Pier",
                                coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let bigSur = PlanPlace(id: 42, name: "Big Sur", coordinate: Coordinate(latitude: 36.27, longitude: -121.81))
    static let ojai = PlanPlace(id: 9, name: "Ojai", coordinate: Coordinate(latitude: 34.448, longitude: -119.243))
    static let pierAt2dp = Coordinate(latitude: 34.01, longitude: -118.5)
    static let itinerary = TripItinerary(isFull: false, etaSeconds: 30_000, fastestEtaSeconds: 24_000,
                                         etaIsEstimate: true, days: [
                                             TripItineraryDay(day: 1, driveSeconds: 15_000, distanceMeters: 200_000,
                                                              overnight: true, path: nil)])
    static let t1 = TripTicket(serial: 1, origin: pierAt2dp, place: 42, days: 2, extraBudgetPercent: 40)
    static let t2 = TripTicket(serial: 2, origin: pierAt2dp, place: 42, days: 2, extraBudgetPercent: 40)
    static let stale = TripTicket(serial: 99, origin: pierAt2dp, place: 42, days: 2, extraBudgetPercent: 40)

    enum From: String, CaseIterable { case idle, searching, chosen, planning, itinerary, failed }
    enum Event: String, CaseIterable {
        case search, choose, endSearch, edit, setDays, setPercent, start, finish, finishStale, revokedStart
    }

    struct Seen: Equatable {
        let state: TripSheetState
        let start: PlanPlace?
        let destination: PlanPlace?
        let days: Int
        let percent: Int
        let ticket: TripTicket?
    }

    static func sheet(_ from: From) -> TripSheet {
        var sheet = TripSheet(disclaimerAccepted: true)
        if from == .idle { return sheet }
        if from == .searching {
            sheet.search("san", for: .start)
            return sheet
        }
        sheet.search("pier", for: .start)
        sheet.choose(pier)
        sheet.search("big", for: .destination)
        sheet.choose(bigSur)
        if from == .chosen { return sheet }
        guard let ticket = sheet.startPlanning() else { return sheet }
        if from == .itinerary { sheet.finish(ticket, with: .itinerary(itinerary)) }
        if from == .failed { sheet.finish(ticket, with: .failure(.noRoute)) }
        return sheet
    }

    static func apply(_ event: Event, to sheet: inout TripSheet) -> TripTicket? {
        switch event {
        case .search: sheet.search("q", for: .destination)
        case .choose: sheet.choose(ojai)
        case .endSearch: sheet.endSearch()
        case .edit: sheet.edit()
        case .setDays: sheet.setDays(4)
        case .setPercent: sheet.setExtraPercent(20)
        case .start: return sheet.startPlanning()
        case .finish: sheet.finish(t1, with: .failure(.tooFewDays))
        case .finishStale: sheet.finish(stale, with: .itinerary(itinerary))
        case .revokedStart:
            sheet.setDisclaimerAccepted(false)
            return sheet.startPlanning()
        }
        return nil
    }

    /// The expected result of every event from every state, written out.
    static func expected(_ from: From, _ event: Event) -> Seen {
        let full = from != .idle && from != .searching
        let start: PlanPlace? = full ? pier : nil
        let destination: PlanPlace? = full ? bigSur : nil
        let before: TripSheetState
        switch from {
        case .idle: before = .idle
        case .searching: before = .searching(.start, "san")
        case .chosen: before = .chosen(bigSur)
        case .planning: before = .planning(t1)
        case .itinerary: before = .itinerary(t1, itinerary)
        case .failed: before = .failed(t1, .noRoute)
        }
        let settled: TripSheetState = full ? .chosen(bigSur) : .idle
        let same = Seen(state: before, start: start, destination: destination, days: 2, percent: 40, ticket: nil)
        let planning = from == .planning
        switch event {
        case .search:
            return planning ? same : Seen(state: .searching(.destination, "q"), start: start,
                                          destination: destination, days: 2, percent: 40, ticket: nil)
        case .choose:
            return from == .searching ? Seen(state: .idle, start: ojai, destination: nil, days: 2, percent: 40,
                                             ticket: nil) : same
        case .endSearch:
            return from == .searching ? Seen(state: .idle, start: nil, destination: nil, days: 2, percent: 40,
                                             ticket: nil) : same
        case .edit:
            return from == .itinerary || from == .failed
                ? Seen(state: settled, start: start, destination: destination, days: 2, percent: 40, ticket: nil)
                : same
        case .setDays:
            return Seen(state: before, start: start, destination: destination, days: planning ? 2 : 4, percent: 40,
                        ticket: nil)
        case .setPercent:
            return Seen(state: before, start: start, destination: destination, days: 2, percent: planning ? 40 : 20,
                        ticket: nil)
        case .start:
            switch from {
            case .chosen:
                return Seen(state: .planning(t1), start: start, destination: destination, days: 2, percent: 40,
                            ticket: t1)
            case .itinerary, .failed:
                return Seen(state: .planning(t2), start: start, destination: destination, days: 2, percent: 40,
                            ticket: t2)
            case .idle, .searching, .planning:
                return same
            }
        case .finish:
            return planning ? Seen(state: .failed(t1, .tooFewDays), start: start, destination: destination, days: 2,
                                   percent: 40, ticket: nil) : same
        case .finishStale, .revokedStart:
            return same
        }
    }

    @Test("every state x every event lands whole", arguments: From.allCases)
    func everyTransition(_ from: From) {
        for event in Event.allCases {
            var sheet = Self.sheet(from)
            let ticket = Self.apply(event, to: &sheet)
            let seen = Seen(state: sheet.state, start: sheet.start, destination: sheet.destination, days: sheet.days,
                            percent: sheet.extraBudgetPercent, ticket: ticket)
            #expect(seen == Self.expected(from, event), "from \(from) on \(event)")
        }
    }

    @Test("P-SAFE-03: no trip ticket before the disclaimer is accepted, one after")
    func disclaimerGate() {
        var sheet = TripSheet(disclaimerAccepted: false)
        sheet.search("pier", for: .start)
        sheet.choose(Self.pier)
        sheet.search("big", for: .destination)
        sheet.choose(Self.bigSur)
        #expect(sheet.startPlanning() == nil)
        #expect(sheet.state == .chosen(Self.bigSur))
        sheet.setDisclaimerAccepted(true)
        #expect(sheet.startPlanning() == Self.t1)
        #expect(sheet.state == .planning(Self.t1))
    }

    @Test("days are held to 1...5 at every bound", arguments: [
        (Int.min, 1), (-1, 1), (0, 1), (1, 1), (2, 2), (5, 5), (6, 5), (Int.max, 5),
    ])
    func daysBounds(_ value: Int, _ held: Int) {
        var sheet = TripSheet(disclaimerAccepted: true)
        sheet.setDays(value)
        #expect(sheet.days == held)
        #expect(TripSheet(disclaimerAccepted: true, days: value).days == held)
    }

    @Test("the extra-time percent is held to 0...40 at every bound", arguments: [
        (Int.min, 0), (-1, 0), (0, 0), (1, 1), (39, 39), (40, 40), (41, 40), (Int.max, 40),
    ])
    func percentBounds(_ value: Int, _ held: Int) {
        var sheet = TripSheet(disclaimerAccepted: true)
        sheet.setExtraPercent(value)
        #expect(sheet.extraBudgetPercent == held)
        #expect(TripSheet(disclaimerAccepted: true, extraBudgetPercent: value).extraBudgetPercent == held)
    }

    @Test("P-PRIV-05: the ticket carries the start cut to 2 dp on each axis, and the chosen days and percent")
    func ticketAtTwoDecimals() {
        let cases: [(Coordinate, Coordinate)] = [
            (Coordinate(latitude: 34.00862, longitude: -118.49853), Coordinate(latitude: 34.01, longitude: -118.5)),
            (Coordinate(latitude: 34.016, longitude: -118.494), Coordinate(latitude: 34.02, longitude: -118.49)),
            (Coordinate(latitude: -33.8712, longitude: 151.2063), Coordinate(latitude: -33.87, longitude: 151.21)),
        ]
        for (raw, cut) in cases {
            var sheet = TripSheet(disclaimerAccepted: true)
            sheet.search("a", for: .start)
            sheet.choose(PlanPlace(id: 1, name: "a", coordinate: raw))
            sheet.search("b", for: .destination)
            sheet.choose(Self.bigSur)
            sheet.setDays(3)
            sheet.setExtraPercent(30)
            #expect(sheet.startPlanning() == TripTicket(serial: 1, origin: cut, place: 42, days: 3,
                                                        extraBudgetPercent: 30))
        }
    }

    @Test("every trip failure has its own calm line")
    func failureLines() {
        let lines = TripFailure.allCases.map(\.line)
        #expect(Set(lines).count == TripFailure.allCases.count)
        #expect(lines.allSatisfy { !$0.isEmpty && !$0.contains("!") })
    }
}

@testable import ScenicKit
import Testing

/// T-0314 R3-R5: the loop sheet's transitions, every state x every event, compared WHOLE (state, start, minutes, the
/// ticket returned), plus every bound of the minutes dial and the 2-dp cut of the one coordinate.
@Suite("LoopSheetTests")
struct LoopSheetTests {
    static let pier = PlanPlace(id: 7, name: "Santa Monica Pier",
                                coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let ojai = PlanPlace(id: 9, name: "Ojai", coordinate: Coordinate(latitude: 34.448, longitude: -119.243))
    static let pierAt2dp = Coordinate(latitude: 34.01, longitude: -118.5)
    static let preview = LoopPreview(path: [pierAt2dp, Coordinate(latitude: 34.05, longitude: -118.5), pierAt2dp],
                                     waypoints: [Coordinate(latitude: 34.05, longitude: -118.5)], durationSeconds: 2_700,
                                     distanceMeters: 30_000, retraceFraction: 0.02, etaIsEstimate: true)
    static let t1 = LoopTicket(serial: 1, start: pierAt2dp, minutes: 45)
    static let t2 = LoopTicket(serial: 2, start: pierAt2dp, minutes: 45)
    static let stale = LoopTicket(serial: 99, start: pierAt2dp, minutes: 45)

    enum From: String, CaseIterable { case idle, searching, chosen, planning, preview, failed }
    enum Event: String, CaseIterable {
        case search, choose, endSearch, edit, setMinutes, start, finish, finishStale, revokedStart
    }

    struct Seen: Equatable {
        let state: LoopSheetState
        let start: PlanPlace?
        let minutes: Int
        let ticket: LoopTicket?
    }

    static func sheet(_ from: From) -> LoopSheet {
        var sheet = LoopSheet(disclaimerAccepted: true)
        if from == .idle { return sheet }
        if from == .searching {
            sheet.search("san")
            return sheet
        }
        sheet.search("pier")
        sheet.choose(pier)
        if from == .chosen { return sheet }
        guard let ticket = sheet.startPlanning() else { return sheet }
        if from == .preview { sheet.finish(ticket, with: .preview(preview)) }
        if from == .failed { sheet.finish(ticket, with: .failure(.noRoute)) }
        return sheet
    }

    static func apply(_ event: Event, to sheet: inout LoopSheet) -> LoopTicket? {
        switch event {
        case .search: sheet.search("q")
        case .choose: sheet.choose(ojai)
        case .endSearch: sheet.endSearch()
        case .edit: sheet.edit()
        case .setMinutes: sheet.setMinutes(90)
        case .start: return sheet.startPlanning()
        case .finish: sheet.finish(t1, with: .failure(.noCleanLoop))
        case .finishStale: sheet.finish(stale, with: .preview(preview))
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
        let before: LoopSheetState
        switch from {
        case .idle: before = .idle
        case .searching: before = .searching("san")
        case .chosen: before = .chosen(pier)
        case .planning: before = .planning(t1)
        case .preview: before = .preview(t1, preview)
        case .failed: before = .failed(t1, .noRoute)
        }
        let settled: LoopSheetState = full ? .chosen(pier) : .idle
        let same = Seen(state: before, start: start, minutes: 45, ticket: nil)
        let planning = from == .planning
        switch event {
        case .search:
            return planning ? same : Seen(state: .searching("q"), start: start, minutes: 45, ticket: nil)
        case .choose:
            return from == .searching ? Seen(state: .chosen(ojai), start: ojai, minutes: 45, ticket: nil) : same
        case .endSearch:
            return from == .searching ? Seen(state: .idle, start: nil, minutes: 45, ticket: nil) : same
        case .edit:
            return from == .preview || from == .failed ? Seen(state: settled, start: start, minutes: 45, ticket: nil)
                                                       : same
        case .setMinutes:
            return Seen(state: before, start: start, minutes: planning ? 45 : 90, ticket: nil)
        case .start:
            switch from {
            case .chosen: return Seen(state: .planning(t1), start: start, minutes: 45, ticket: t1)
            case .preview, .failed: return Seen(state: .planning(t2), start: start, minutes: 45, ticket: t2)
            case .idle, .searching, .planning: return same
            }
        case .finish:
            return planning ? Seen(state: .failed(t1, .noCleanLoop), start: start, minutes: 45, ticket: nil) : same
        case .finishStale, .revokedStart:
            return same
        }
    }

    @Test("every state x every event lands whole", arguments: From.allCases)
    func everyTransition(_ from: From) {
        for event in Event.allCases {
            var sheet = Self.sheet(from)
            let ticket = Self.apply(event, to: &sheet)
            let seen = Seen(state: sheet.state, start: sheet.start, minutes: sheet.minutes, ticket: ticket)
            #expect(seen == Self.expected(from, event), "from \(from) on \(event)")
        }
    }

    @Test("P-SAFE-03: no loop ticket before the disclaimer is accepted, one after")
    func disclaimerGate() {
        var sheet = LoopSheet(disclaimerAccepted: false)
        sheet.search("pier")
        sheet.choose(Self.pier)
        #expect(sheet.startPlanning() == nil)
        #expect(sheet.state == .chosen(Self.pier))
        sheet.setDisclaimerAccepted(true)
        #expect(sheet.startPlanning() == Self.t1)
        #expect(sheet.state == .planning(Self.t1))
    }

    @Test("the minutes dial is held to 10...180 at every bound, 45 by default", arguments: [
        (Int.min, 10), (-1, 10), (0, 10), (9, 10), (10, 10), (11, 11), (45, 45), (179, 179), (180, 180), (181, 180),
        (Int.max, 180),
    ])
    func minuteBounds(_ value: Int, _ held: Int) {
        var sheet = LoopSheet(disclaimerAccepted: true)
        #expect(sheet.minutes == 45)
        sheet.setMinutes(value)
        #expect(sheet.minutes == held)
        #expect(LoopSheet(disclaimerAccepted: true, minutes: value).minutes == held)
    }

    @Test("P-PRIV-05: the ticket carries the start cut to 2 dp on each axis, and the dial's minutes")
    func ticketAtTwoDecimals() {
        let cases: [(Coordinate, Coordinate)] = [
            (Coordinate(latitude: 34.00862, longitude: -118.49853), Coordinate(latitude: 34.01, longitude: -118.5)),
            (Coordinate(latitude: 34.016, longitude: -118.494), Coordinate(latitude: 34.02, longitude: -118.49)),
            (Coordinate(latitude: -33.8712, longitude: 151.2063), Coordinate(latitude: -33.87, longitude: 151.21)),
        ]
        for (raw, cut) in cases {
            var sheet = LoopSheet(disclaimerAccepted: true)
            sheet.search("a")
            sheet.choose(PlanPlace(id: 1, name: "a", coordinate: raw))
            sheet.setMinutes(75)
            #expect(sheet.startPlanning() == LoopTicket(serial: 1, start: cut, minutes: 75))
        }
    }

    @Test("every loop failure has its own calm line")
    func failureLines() {
        let lines = LoopFailure.allCases.map(\.line)
        #expect(Set(lines).count == LoopFailure.allCases.count)
        #expect(lines.allSatisfy { !$0.isEmpty && !$0.contains("!") })
    }
}

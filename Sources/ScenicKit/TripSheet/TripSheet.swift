/// The road-trip sheet's state machine (T-0313 R4). The ONLY maker of a TripTicket, and the gate: no ticket before
/// the safety disclaimer is accepted (P-SAFE-03), none without a start and a destination, none while one is in
/// flight. The origin is cut to 2 dp here, before anything can send it (P-PRIV-05). Days and the extra-time percent
/// are held inside the Worker's whitelist (tripRequest.ts: days 1...5, extra_budget_pct 0...40).
public struct TripSheet: Equatable, Sendable {
    public static let dayRange = 1...5
    public static let extraPercentRange = 0...40

    public private(set) var state: TripSheetState = .idle
    public private(set) var start: PlanPlace?
    public private(set) var destination: PlanPlace?
    public private(set) var days: Int
    public private(set) var extraBudgetPercent: Int
    public private(set) var disclaimerAccepted: Bool
    private var issued = 0

    public init(disclaimerAccepted: Bool, days: Int = 2, extraBudgetPercent: Int = 40) {
        self.disclaimerAccepted = disclaimerAccepted
        self.days = Self.clamp(days, to: Self.dayRange)
        self.extraBudgetPercent = Self.clamp(extraBudgetPercent, to: Self.extraPercentRange)
    }

    public mutating func setDisclaimerAccepted(_ accepted: Bool) {
        disclaimerAccepted = accepted
    }

    public mutating func search(_ query: String, for field: PlanField) {
        if case .planning = state { return }
        state = .searching(field, query)
    }

    public mutating func choose(_ place: PlanPlace) {
        guard case .searching(let field, _) = state else { return }
        switch field {
        case .destination: destination = place
        case .start: start = place
        }
        settle()
    }

    public mutating func endSearch() {
        guard case .searching = state else { return }
        settle()
    }

    /// Back from an itinerary or a failure to the form, keeping every choice.
    public mutating func edit() {
        switch state {
        case .itinerary, .failed: settle()
        case .idle, .searching, .chosen, .planning: return
        }
    }

    public mutating func setDays(_ value: Int) {
        if case .planning = state { return }
        days = Self.clamp(value, to: Self.dayRange)
    }

    public mutating func setExtraPercent(_ value: Int) {
        if case .planning = state { return }
        extraBudgetPercent = Self.clamp(value, to: Self.extraPercentRange)
    }

    public mutating func startPlanning() -> TripTicket? {
        guard disclaimerAccepted, let start, let destination else { return nil }
        switch state {
        case .chosen, .itinerary, .failed: break
        case .idle, .searching, .planning: return nil
        }
        issued += 1
        let ticket = TripTicket(serial: issued, origin: Self.twoDecimals(start.coordinate), place: destination.id,
                                days: days, extraBudgetPercent: extraBudgetPercent)
        state = .planning(ticket)
        return ticket
    }

    public mutating func finish(_ ticket: TripTicket, with outcome: TripOutcome) {
        guard case .planning(let inFlight) = state, inFlight == ticket else { return }
        switch outcome {
        case .itinerary(let itinerary): state = .itinerary(ticket, itinerary)
        case .failure(let failure): state = .failed(ticket, failure)
        }
    }

    static func twoDecimals(_ coordinate: Coordinate) -> Coordinate {
        Coordinate(latitude: (coordinate.latitude * 100).rounded() / 100,
                   longitude: (coordinate.longitude * 100).rounded() / 100)
    }

    static func clamp(_ value: Int, to range: ClosedRange<Int>) -> Int {
        min(max(value, range.lowerBound), range.upperBound)
    }

    private mutating func settle() {
        state = destination.map { .chosen($0) } ?? .idle
    }
}

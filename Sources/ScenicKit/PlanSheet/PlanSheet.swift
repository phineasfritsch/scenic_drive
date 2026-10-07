/// The plan sheet's state machine (T-0294 R2): what the user has chosen, and the ONE gate every plan passes.
///
/// idle -> searching(field, query) -> chosen(destination) -> planning(ticket) -> preview | failed. The view calls
/// `startPlanning()` and hands the ticket it returns - and only that - to a `RoutePlanning`; with the safety
/// disclaimer not accepted there is no ticket, so no planner call and no request (P-SAFE-03). The ticket's origin
/// is the typed start at 2 decimal places (P-PRIV-06, R4).
public struct PlanSheet: Equatable, Sendable {
    /// The Worker's MAX_BUDGET_MINUTES; the extra-time control is clamped to 0...this.
    public static let maxBudgetMinutes = 180

    public private(set) var state: PlanSheetState = .idle
    public private(set) var start: PlanPlace?
    public private(set) var destination: PlanPlace?
    public private(set) var budgetMinutes: Int
    public private(set) var disclaimerAccepted: Bool
    private var issued = 0

    public init(disclaimerAccepted: Bool, budgetMinutes: Int = 30) {
        self.disclaimerAccepted = disclaimerAccepted
        self.budgetMinutes = budgetMinutes
    }

    /// The home's on-device acknowledgement, read by the view; the sheet never writes it (R3).
    public mutating func setDisclaimerAccepted(_ accepted: Bool) {
        disclaimerAccepted = accepted
    }

    /// The user typed into a field's search. Ignored while a plan is in flight.
    public mutating func search(_ query: String, for field: PlanField) {
        if case .planning = state { return }
        state = .searching(field, query)
    }

    /// The user picked a search result for the field being searched.
    public mutating func choose(_ place: PlanPlace) {
        guard case .searching(let field, _) = state else { return }
        switch field {
        case .destination: destination = place
        case .start: start = place
        }
        settle()
    }

    /// The search was put away without a pick.
    public mutating func endSearch() {
        guard case .searching = state else { return }
        settle()
    }

    /// The extra-time control. Ignored while a plan is in flight.
    public mutating func setBudget(_ minutes: Int) {
        if case .planning = state { return }
        budgetMinutes = min(max(minutes, 0), Self.maxBudgetMinutes)
    }

    /// THE GATE. A ticket only with the disclaimer accepted, a start and a destination, from chosen, preview or
    /// failed; otherwise nil and nothing changes.
    public mutating func startPlanning() -> PlanTicket? {
        guard disclaimerAccepted, let start, let destination else { return nil }
        switch state {
        case .chosen, .preview, .failed: break
        case .idle, .searching, .planning: return nil
        }
        issued += 1
        let ticket = PlanTicket(serial: issued, origin: Self.twoDecimals(start.coordinate), place: destination.id,
                                budgetMinutes: budgetMinutes)
        state = .planning(ticket)
        return ticket
    }

    /// The planner's answer for `ticket`. Applied only to the ticket in flight; any other is dropped.
    public mutating func finish(_ ticket: PlanTicket, with outcome: PlanOutcome) {
        guard case .planning(let inFlight) = state, inFlight == ticket else { return }
        switch outcome {
        case .preview(let preview): state = .preview(ticket, preview)
        case .failure(let failure): state = .failed(ticket, failure)
        }
    }

    /// The start as it may leave the device: each axis to the nearest hundredth (R4). PlanRequestBody refuses rather
    /// than rounds, so the rounding is the caller's - here.
    static func twoDecimals(_ coordinate: Coordinate) -> Coordinate {
        Coordinate(latitude: (coordinate.latitude * 100).rounded() / 100,
                   longitude: (coordinate.longitude * 100).rounded() / 100)
    }

    private mutating func settle() {
        state = destination.map { .chosen($0) } ?? .idle
    }
}

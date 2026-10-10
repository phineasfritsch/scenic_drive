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
    /// T-0357 R6: /config's degrade, set by the view from its planner; the gate issues nothing unless it is clear.
    public private(set) var degrade: ConfigDegrade = .clear
    private var issued = 0

    public init(disclaimerAccepted: Bool, budgetMinutes: Int = 30) {
        self.disclaimerAccepted = disclaimerAccepted
        self.budgetMinutes = budgetMinutes
    }

    /// The home's on-device acknowledgement, read by the view; the sheet never writes it (R3).
    public mutating func setDisclaimerAccepted(_ accepted: Bool) {
        disclaimerAccepted = accepted
    }

    /// The planner's /config degrade (T-0357 R7), read by the view.
    public mutating func setDegrade(_ degrade: ConfigDegrade) {
        self.degrade = degrade
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

    /// THE GATE. A ticket only with the disclaimer accepted, a start and a destination, from chosen, preview,
    /// failed or offered; otherwise nil and nothing changes.
    public mutating func startPlanning() -> PlanTicket? {
        gate(budgetMinutes: budgetMinutes, allBackRoads: false)
    }

    /// T-0334: the "+40" offer - ONE fresh plan at budget + 40, through THE GATE. Only from `.offered`, only when
    /// the answer made the offer; otherwise nil and nothing changes.
    public mutating func takeMoreTime() -> PlanTicket? {
        guard case .offered(_, let offer) = state, let minutes = offer.moreTimeMinutes else { return nil }
        return gate(budgetMinutes: minutes, allBackRoads: false)
    }

    /// T-0334: the "all back roads" offer - ONE fresh plan at MAX_LAMBDA naming the minutes that cover its ETA, so the
    /// Worker checks its answer against fastest + those minutes like every plan (P-SAFE-04, R1). Through THE GATE.
    public mutating func takeBackRoads() -> PlanTicket? {
        guard case .offered(_, let offer) = state, let minutes = offer.backRoadsBudgetMinutes else { return nil }
        return gate(budgetMinutes: minutes, allBackRoads: true)
    }

    /// The one place a ticket is made. The minutes are the stepper's (clamped by setBudget) or an offer's (bounded by
    /// ScenicAPIClient's NothingPrettyOffer read); they become the sheet's budget only when a ticket is issued.
    private mutating func gate(budgetMinutes minutes: Int, allBackRoads: Bool) -> PlanTicket? {
        guard disclaimerAccepted, degrade == .clear, let start, let destination else { return nil }
        switch state {
        case .chosen, .preview, .failed: break
        case .idle, .searching, .planning: return nil
        case .offered: break
        }
        budgetMinutes = minutes
        issued += 1
        let ticket = PlanTicket(serial: issued, origin: Self.twoDecimals(start.coordinate), place: destination.id,
                                budgetMinutes: minutes, allBackRoads: allBackRoads)
        state = .planning(ticket)
        return ticket
    }

    /// A saved drive replayed (T-0306 R3): its start, its destination place and its budget become the sheet's, and
    /// the ticket - or nil - is THE GATE's, `startPlanning()`. Ignored while a plan is in flight.
    public mutating func replay(_ saved: SavedReplay) -> PlanTicket? {
        if case .planning = state { return nil }
        start = PlanPlace(id: 0, name: "Your saved start", coordinate: saved.start)
        destination = saved.destination
        budgetMinutes = min(max(saved.budgetMinutes, 0), Self.maxBudgetMinutes)
        state = .chosen(saved.destination)
        return startPlanning()
    }

    /// The planner's answer for `ticket`. Applied only to the ticket in flight; any other is dropped.
    public mutating func finish(_ ticket: PlanTicket, with outcome: PlanOutcome) {
        guard case .planning(let inFlight) = state, inFlight == ticket else { return }
        switch outcome {
        case .preview(let preview): state = .preview(ticket, preview)
        case .failure(let failure): state = .failed(ticket, failure)
        case .offered(let offer): state = .offered(ticket, offer)
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

/// The loop sheet's state machine (T-0314 R3-R5). The ONLY maker of a LoopTicket, and the gate: no ticket before the
/// safety disclaimer is accepted (P-SAFE-03), none without a start, none while one is in flight. The start is cut to
/// 2 dp here, before anything can send it (P-PRIV-05). The minutes dial is held inside the Worker's whitelist
/// (loopRequest.ts: MIN_LOOP_MINUTES 10, MAX_LOOP_MINUTES 180).
public struct LoopSheet: Equatable, Sendable {
    public static let minuteRange = 10...180
    public static let defaultMinutes = 45

    public private(set) var state: LoopSheetState = .idle
    public private(set) var start: PlanPlace?
    public private(set) var minutes: Int
    public private(set) var disclaimerAccepted: Bool
    private var issued = 0

    public init(disclaimerAccepted: Bool, minutes: Int = LoopSheet.defaultMinutes) {
        self.disclaimerAccepted = disclaimerAccepted
        self.minutes = Self.clamp(minutes)
    }

    public mutating func setDisclaimerAccepted(_ accepted: Bool) {
        disclaimerAccepted = accepted
    }

    public mutating func search(_ query: String) {
        if case .planning = state { return }
        state = .searching(query)
    }

    public mutating func choose(_ place: PlanPlace) {
        guard case .searching = state else { return }
        start = place
        settle()
    }

    public mutating func endSearch() {
        guard case .searching = state else { return }
        settle()
    }

    /// Back from a preview or a failure to the form, keeping the start and the minutes.
    public mutating func edit() {
        switch state {
        case .preview, .failed: settle()
        case .idle, .searching, .chosen, .planning: return
        }
    }

    public mutating func setMinutes(_ value: Int) {
        if case .planning = state { return }
        minutes = Self.clamp(value)
    }

    public mutating func startPlanning() -> LoopTicket? {
        guard disclaimerAccepted, let start else { return nil }
        switch state {
        case .chosen, .preview, .failed: break
        case .idle, .searching, .planning: return nil
        }
        issued += 1
        let ticket = LoopTicket(serial: issued, start: Self.twoDecimals(start.coordinate), minutes: minutes)
        state = .planning(ticket)
        return ticket
    }

    public mutating func finish(_ ticket: LoopTicket, with outcome: LoopOutcome) {
        guard case .planning(let inFlight) = state, inFlight == ticket else { return }
        switch outcome {
        case .preview(let preview): state = .preview(ticket, preview)
        case .failure(let failure): state = .failed(ticket, failure)
        }
    }

    static func twoDecimals(_ coordinate: Coordinate) -> Coordinate {
        Coordinate(latitude: (coordinate.latitude * 100).rounded() / 100,
                   longitude: (coordinate.longitude * 100).rounded() / 100)
    }

    static func clamp(_ value: Int) -> Int {
        min(max(value, minuteRange.lowerBound), minuteRange.upperBound)
    }

    private mutating func settle() {
        state = start.map { .chosen($0) } ?? .idle
    }
}

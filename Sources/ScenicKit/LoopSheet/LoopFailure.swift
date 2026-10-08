/// What a loop ended in, as the sheet tells it apart (T-0314 R2, R6, R7): one case per answer the driver can act on
/// differently, each with its own calm line (memory owner-route-intent: unhurried, never alarm).
public enum LoopFailure: String, CaseIterable, Equatable, Sendable {
    case quotaExhausted
    case planningPaused
    case routingOffline
    case noRoute
    case noCleanLoop
    case regionUnsupported
    case invalidRequest
    case refusedOnDevice
    case unexpectedResponse

    /// The one line the sheet shows for this failure.
    public var line: String {
        switch self {
        case .quotaExhausted: return "That was today's loop. Another one opens up tomorrow."
        case .planningPaused: return "Planning is resting for a moment. Try again in a little while."
        case .routingOffline: return "We could not reach the planner. Check your connection and try again."
        case .noRoute: return "We could not find a loop from this start. Try another place."
        case .noCleanLoop: return "Every loop from here doubled back on itself. Try another start or another length."
        case .regionUnsupported: return "Loops start inside the area we cover for now."
        case .invalidRequest: return "Something about this loop did not add up. Try choosing again."
        case .refusedOnDevice: return "This loop cannot be planned from here. Check the start and the time."
        case .unexpectedResponse: return "The planner answered in a way we did not expect. Try again."
        }
    }
}

/// What a loop ended in, as the sheet tells it apart (T-0314 R2, R6, R7): one case per answer the driver can act on
/// differently, each with its own calm line (memory owner-route-intent: unhurried, never alarm).
public enum LoopFailure: String, CaseIterable, Equatable, Sendable {
    case quotaExhausted
    case planningPaused
    case routingOffline
    case noRoute
    case noCleanLoop
    case nothingPretty
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
        case .nothingPretty:
            return "No loop from here was pretty enough to show today. Try another start or another length."
        case .regionUnsupported:
            return "Loops start inside the area we cover for now. We can count this area toward where we go next."
        case .invalidRequest: return "Something about this loop did not add up. Try choosing again."
        case .refusedOnDevice: return "This loop cannot be planned from here. Check the start and the time."
        case .unexpectedResponse: return "The planner answered in a way we did not expect. Try again."
        }
    }

    /// T-0365 R1: what this failure offers beside Try again and Change - a start outside the served region offers
    /// the plan sheet's "Count this area"; every other failure, nothing.
    public var waitlistAction: PlanFailureAction? {
        switch self {
        case .regionUnsupported: return .joinWaitlist
        case .quotaExhausted, .planningPaused, .routingOffline, .noRoute, .noCleanLoop, .nothingPretty,
             .invalidRequest, .refusedOnDevice, .unexpectedResponse: return nil
        }
    }
}

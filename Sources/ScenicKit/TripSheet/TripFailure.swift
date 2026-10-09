/// What a road trip ended in, as the sheet tells it apart (T-0313 R3): one case per Worker answer the driver can
/// act on differently, each with its own calm line (memory owner-route-intent: unhurried, never alarm).
public enum TripFailure: String, CaseIterable, Equatable, Sendable {
    case quotaExhausted
    case planningPaused
    case routingOffline
    case noRoute
    case regionUnsupported
    case unknownPlace
    case tooFewDays
    case ceilingBreached
    case nothingPretty
    case planRefused
    case invalidRequest
    case refusedOnDevice
    case unexpectedResponse

    /// The one line the sheet shows for this failure.
    public var line: String {
        switch self {
        case .quotaExhausted: return "That is all the planning for today. It opens up again soon."
        case .planningPaused: return "Planning is resting for a moment. Try again in a little while."
        case .routingOffline: return "We could not reach the planner. Check your connection and try again."
        case .noRoute: return "We could not find a road trip between these two places."
        case .regionUnsupported: return "Road trips start inside the area we cover for now."
        case .unknownPlace: return "We could not find that place. Try choosing it again."
        case .tooFewDays: return "That is more road than these days hold. Add a day and try again."
        case .ceilingBreached: return "Every scenic way ran past your extra time. Try a little more time."
        case .nothingPretty: return "Nothing on the way there was pretty enough to show. Try another place to head for."
        case .planRefused: return "We could not settle on a scenic way this time. Try again."
        case .invalidRequest: return "Something about this trip did not add up. Try choosing again."
        case .refusedOnDevice: return "This trip cannot be planned from here. Check the start and the days."
        case .unexpectedResponse: return "The planner answered in a way we did not expect. Try again."
        }
    }
}

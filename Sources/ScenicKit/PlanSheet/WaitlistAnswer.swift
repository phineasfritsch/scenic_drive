/// What one "Count this area" tap came to (T-0360 R4), and the one line the waitlist card says about it. Every line
/// says whether anything was sent and whether the area was counted - never more than happened.
public enum WaitlistAnswer: String, CaseIterable, Equatable, Sendable {
    /// 200 {"waitlisted":true}: the start's area was counted; the device remembers it (R3).
    case joined
    /// This install already counted the start's area: nothing was sent (R3).
    case alreadyJoined
    /// The start, or the area computed from it, is one the Worker would refuse: nothing was sent (R2).
    case refusedOnDevice
    /// 503 waitlist_unavailable, or no place to send it: not counted.
    case unavailable
    /// Any other reply: not counted.
    case failed
    /// No reply came back: it may or may not have been counted.
    case offline

    /// The card's words for this answer.
    public var line: String {
        switch self {
        case .joined:
            return "This area is counted. We sent one rough area around your start, about 250 square kilometres - "
                + "never the place itself."
        case .alreadyJoined: return "This phone already counted this area. Nothing new was sent."
        case .refusedOnDevice: return "That start couldn't be turned into an area, so nothing was sent."
        case .unavailable:
            return "The waitlist isn't taking requests right now, so this area wasn't counted. Try again later."
        case .failed: return "That didn't go through, so this area wasn't counted."
        case .offline: return "No reply came back, so this area may not be counted. Try again with signal."
        }
    }
}

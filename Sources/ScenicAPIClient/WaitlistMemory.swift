/// The cells this install has already counted on the waitlist (T-0360 R3): read before a request, written only after
/// a 200 {"waitlisted":true}. It stays on the device; nothing in it is ever sent.
public protocol WaitlistMemory: Sendable {
    func hasJoined(_ cell: String) -> Bool
    func rememberJoined(_ cell: String)
}

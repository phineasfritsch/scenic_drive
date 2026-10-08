import Foundation

/// The session decision (T-0310 R3), pure. A stored session whose expiry is more than `margin` after now is used and
/// nothing is sent. Otherwise, once this launch's one acquisition is spent, there is no session. Unspent: a stored
/// session (expired, or dropped after a 401) is renewed by its key's assertion; nothing stored, or an item that is
/// not a session, attests a new key; a failed Keychain read does nothing - a locked Keychain burns no key.
public enum SessionStep: Equatable, Sendable {
    /// A live token: zero requests.
    case use(String)
    /// POST /attest/challenge, then POST /attest/assert by the attested key `keyId`.
    case renew(keyId: String)
    /// POST /attest/challenge, then POST /attest for a new key.
    case attest
    /// No session: zero requests.
    case none

    /// Seconds a token must still have to be used: a request in flight never carries one that expires on the way.
    public static let margin: TimeInterval = 60

    public static func next(stored: KeychainRead<SessionRecord>, now: Date, spent: Bool) -> SessionStep {
        if case .valid(let record) = stored, record.expiresAt.timeIntervalSince(now) > margin {
            return .use(record.token)
        }
        if spent { return .none }
        switch stored {
        case .valid(let record): return .renew(keyId: record.keyId)
        case .absent, .malformed: return .attest
        case .failed: return .none
        }
    }
}

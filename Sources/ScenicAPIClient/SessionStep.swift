import Foundation

/// The session decision (T-0310 R3). STUB (RED).
public enum SessionStep: Equatable, Sendable {
    case use(String)
    case renew(keyId: String)
    case attest
    case none

    public static let margin: TimeInterval = 60

    public static func next(stored: KeychainRead<SessionRecord>, now: Date, spent: Bool) -> SessionStep {
        .none
    }
}

import Foundation

/// Who holds a session (T-0307 R2): the verified session JWT the Worker issued, or nil. A nil token means the
/// ledger is never called and the Surprise history stays on the device. The ledger is keyed by the token's `sub`
/// alone (T-0302 R1) - never by `x-scenic-device`, which `LedgerClient` never sends.
public protocol LedgerSessionProvider: Sendable {
    func sessionToken() -> String?
}

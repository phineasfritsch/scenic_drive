import Foundation

/// Who holds a session (T-0307 R2, T-0310 R4): the verified session JWT the Worker issued, or nil. A nil token means
/// the ledger is never called and the Surprise history stays on the device. The ledger is keyed by the token's `sub`
/// alone (T-0302 R1) - never by `x-scenic-device`, which `LedgerClient` never sends. Production's provider is
/// `SessionStore`, which may make the App Attest requests to obtain one.
public protocol LedgerSessionProvider: Sendable {
    func sessionToken() async -> String?
    /// The Worker answered 401 to `token`: the provider drops it, and a later call may obtain a new one.
    func sessionRejected(_ token: String) async
}

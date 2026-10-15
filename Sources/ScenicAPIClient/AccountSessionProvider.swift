import Foundation

/// Who holds the session DELETE /account is sent over (T-0356 R4). Production's provider is `SessionStore`, which
/// may make the App Attest requests to obtain one.
public protocol AccountSessionProvider: Sendable {
    /// The session token, or nil: no request is made without one.
    func accountSession() async -> String?
    /// The Worker answered 401 to `token`: the provider drops it and may grant one renewal.
    func accountSessionRejected(_ token: String) async
    /// The account is deleted: the provider drops the session from memory and from the Keychain.
    func forgetSession() async
}

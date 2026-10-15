import Foundation

/// Every answer one `AccountClient.deleteAccount()` can have (T-0356 R2): one case per answer of the Worker's
/// DELETE /account (services/api/src/account.ts), plus the one the device decides on its own (`noSession`) and the
/// one where no reply came (`offline`). Only `deleted` erases anything on the device (R3, R5).
public enum AccountOutcome: Equatable, Sendable {
    /// 200 {deleted: true, revoke_pending, plans_pending}.
    case deleted(revokePending: Bool, plansPending: Bool)
    /// No session token: no request was made.
    case noSession
    /// 401 unauthorized, after the one renewal (or with none to make).
    case unauthorized
    /// 405 - DELETE only.
    case methodRefused
    /// 503 auth_unavailable: the Worker has no session secret.
    case authUnavailable
    /// 503 account_unavailable: the user store failed; nothing was deleted there.
    case accountUnavailable
    /// A 200 whose body is not exactly the deletion's shape: the deletion is not confirmed.
    case unreadable
    /// Any other status, or a 503 with another body.
    case unexpected(Int)
    /// No HTTP reply arrived at all.
    case offline
}

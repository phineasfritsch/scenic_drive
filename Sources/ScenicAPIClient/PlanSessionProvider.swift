import Foundation

/// The session a plan-family request may carry as `authorization: Bearer` (T-0322 R3, R4): the Worker session JWT
/// whose `act` is exactly `account` - the purchase the same request names in `x-scenic-account-token` - or nil, and
/// then the request carries no Bearer at all. A session issued for another purchase (or for none) is never handed
/// out: the Worker reads a verified Bearer's act and ignores the header beside it, so a stale one would read anon.
/// Production's provider is `SessionStore`, which may renew the session to carry `account`.
///
/// T-0333 R3, R4: a plan-family 401 hands the token back through `planSessionRejected`; the provider drops it, and the
/// first time in a launch for that purchase lets the next `planSession` acquire once more (PlanFamilySend).
public protocol PlanSessionProvider: Sendable {
    func planSession(account: UUID?) async -> String?
    func planSessionRejected(_ token: String) async
}

import Foundation

/// Every answer one `LedgerClient` call can have (T-0307 R4): one case per Worker status, plus the two the device
/// decides on its own (`noSession`, `refusedOnDevice`) and the one where no reply came (`offline`). Nothing here is
/// retried: a 429 or a 401 is handed straight back to the caller.
public enum LedgerOutcome: Equatable, Sendable {
    /// 200 to POST /ledger: `{"recorded": true}`.
    case recorded
    /// 200 to GET /ledger: the caller's rows of the last 90 UTC days, in the Worker's order (newest day first).
    case places([LedgerRow])
    /// No session token: no request was made (R2).
    case noSession
    /// The place id or the cell would be refused by the Worker: no request was made (R3).
    case refusedOnDevice
    /// 400 invalid_request.
    case invalidRequest
    /// 401 unauthorized.
    case unauthorized
    /// 405 - GET or POST only.
    case methodRefused
    /// 429 ledger_daily_cap (T-0304).
    case dailyCap
    /// 503 auth_unavailable or ledger_unavailable.
    case unavailable
    /// A 200 whose body is not the shape the call expects.
    case unreadable
    /// Any other status, or a 429 that is not the daily cap.
    case unexpected(Int)
    /// No HTTP reply arrived at all.
    case offline
}

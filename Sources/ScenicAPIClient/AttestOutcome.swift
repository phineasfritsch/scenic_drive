import Foundation

/// Every answer one `AttestClient` call can have (T-0310 R2): one case per Worker answer, plus `offline` when no
/// reply came. Nothing here is retried; `SessionStore` spends one acquisition per launch whatever the answer.
public enum AttestOutcome: Equatable, Sendable {
    /// 200 to POST /attest/challenge: the single-use challenge (43 base64url characters).
    case challenge(String)
    /// 200 to POST /attest or /attest/assert: the session JWT and when it expires.
    case session(token: String, expiresAt: Date)
    /// 400 invalid_attestation or invalid_assertion.
    case rejected
    /// 405 - POST only.
    case methodRefused
    /// 429 challenge_rate_limited (T-0280).
    case rateLimited
    /// 503 attest_unavailable.
    case unavailable
    /// A 200 whose body is not the shape the call expects.
    case unreadable
    /// Any other status, or a 429 that is not the challenge limit.
    case unexpected(Int)
    /// No HTTP reply arrived at all.
    case offline
}

import Foundation

/// T-0310 R2: every /attest reply -> exactly one `AttestOutcome`, by status, then by body where the status alone does
/// not decide. Pure: no reply is ever re-requested from here.
enum AttestReplyReader {
    /// Which body a 200 must carry: the challenge's, or a session's (POST /attest and POST /attest/assert).
    enum Call {
        case challenge
        case session
    }

    private struct Challenge: Decodable {
        let challenge: String
        let expires_at: String
    }

    private struct Session: Decodable {
        let token: String
        let expires_at: String
    }

    private struct Failure: Decodable {
        let error: String
    }

    static func read(_ reply: PlanHTTPReply, call: Call) -> AttestOutcome {
        switch reply.status {
        case 200: return call == .challenge ? challenge(reply.body) : session(reply.body)
        case 400: return .rejected
        case 405: return .methodRefused
        case 429:
            let failure = try? JSONDecoder().decode(Failure.self, from: reply.body)
            return failure?.error == "challenge_rate_limited" ? .rateLimited : .unexpected(429)
        case 503: return .unavailable
        default: return .unexpected(reply.status)
        }
    }

    private static func challenge(_ body: Data) -> AttestOutcome {
        guard let value = try? JSONDecoder().decode(Challenge.self, from: body), isChallenge(value.challenge),
              instant(value.expires_at) != nil else { return .unreadable }
        return .challenge(value.challenge)
    }

    private static func session(_ body: Data) -> AttestOutcome {
        guard let value = try? JSONDecoder().decode(Session.self, from: body), !value.token.isEmpty,
              let expiresAt = instant(value.expires_at) else { return .unreadable }
        return .session(token: value.token, expiresAt: expiresAt)
    }

    /// attest.ts CHALLENGE: exactly 43 characters of A-Z, a-z, 0-9, "-" and "_".
    static func isChallenge(_ text: String) -> Bool {
        let bytes = Array(text.utf8)
        return bytes.count == 43 && bytes.allSatisfy {
            (48...57).contains($0) || (65...90).contains($0) || (97...122).contains($0) || $0 == 45 || $0 == 95
        }
    }

    /// The Worker's `Date.toISOString()`: YYYY-MM-DDTHH:MM:SS.sssZ.
    static func instant(_ text: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: text)
    }
}

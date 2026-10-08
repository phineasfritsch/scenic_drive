import Foundation

/// T-0310 R2: every /attest reply -> exactly one `AttestOutcome`. STUB (RED).
enum AttestReplyReader {
    enum Call {
        case challenge
        case session
    }

    static func read(_ reply: PlanHTTPReply, call: Call) -> AttestOutcome {
        .unreadable
    }
}

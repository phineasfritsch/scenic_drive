import Foundation
import ScenicKit

/// T-0360 R4: every /waitlist reply -> exactly one `WaitlistAnswer`. Pure: no reply is ever re-requested from here.
enum WaitlistReplyReader {
    private struct Waitlisted: Decodable {
        let waitlisted: Bool
    }

    static func read(_ reply: PlanHTTPReply) -> WaitlistAnswer {
        switch reply.status {
        case 200:
            return (try? JSONDecoder().decode(Waitlisted.self, from: reply.body))?.waitlisted == true ? .joined : .failed
        case 503: return .unavailable
        default: return .failed
        }
    }
}

import ScenicKit
import Testing

/// T-0360 acceptance A2 (R4): every WaitlistAnswer's line, compared WHOLE against a table typed here - an exhaustive
/// switch, so a new answer does not compile until this file names its line - and the cases' count and order.
@Suite("WaitlistAnswerTests")
struct WaitlistAnswerTests {
    static func expected(_ answer: WaitlistAnswer) -> String {
        switch answer {
        case .joined:
            return "This area is counted. We sent one rough area around your start, about 250 square kilometres - "
                + "never the place itself."
        case .alreadyJoined: return "This phone already counted this area. Nothing new was sent."
        case .refusedOnDevice: return "That start couldn't be turned into an area, so nothing was sent."
        case .unavailable:
            return "The waitlist isn't taking requests right now, so this area wasn't counted. Try again later."
        case .failed: return "That didn't go through, so this area wasn't counted."
        case .offline: return "No reply came back, so this area may not be counted. Try again with signal."
        }
    }

    @Test("every WaitlistAnswer has its one line, whole")
    func everyLineWhole() {
        for answer in WaitlistAnswer.allCases {
            #expect(answer.line == Self.expected(answer), "\(answer)")
        }
    }

    @Test("the answers are exactly the six R4 rules, in order, each line distinct and calm")
    func everyCase() {
        #expect(WaitlistAnswer.allCases.map(\.rawValue) == [
            "joined", "alreadyJoined", "refusedOnDevice", "unavailable", "failed", "offline",
        ])
        #expect(Set(WaitlistAnswer.allCases.map(\.line)).count == 6)
        for answer in WaitlistAnswer.allCases {
            #expect(answer.line.hasSuffix(".") && !answer.line.contains("!"), "\(answer)")
        }
    }
}

import ScenicKit
import Testing

/// T-0294 acceptance 2: every PlanSheetFailure maps to exactly one copy line and one action (the plan's Degraded states
/// row, R5), compared WHOLE against a table typed here - an exhaustive switch, so a fourteenth case does not
/// compile until this file names its row - plus the count and order of the cases themselves.
@Suite("PlanFailureCopyTests")
struct PlanFailureCopyTests {
    static func expected(_ failure: PlanSheetFailure) -> PlanFailureCopy {
        switch failure {
        case .quotaExhausted:
            return PlanFailureCopy(line: "That's all of today's planned drives. More open up when the daily count resets.",
                                   action: .surpriseMe)
        case .planningPaused:
            return PlanFailureCopy(line: "Planning is paused right now. Surprise Me still works.", action: .surpriseMe)
        case .routingOffline:
            return PlanFailureCopy(line: "The route planner can't be reached right now. Try again in a little while.",
                                   action: .tryAgain)
        case .noRoute:
            return PlanFailureCopy(line: "Couldn't reach that place by paved road.", action: .chooseAnotherPlace)
        case .regionUnsupported:
            return PlanFailureCopy(line: "Drives can't be planned from that start yet. Try a start in a region we cover.",
                                   action: .changeStart)
        case .attestUnsupported:
            return PlanFailureCopy(line: "This phone can't plan drives yet. Surprise Me still works.", action: .surpriseMe)
        case .offlineDuringDrive:
            return PlanFailureCopy(line: "You're offline. Keep to the road you're on; the route comes back with signal.",
                                   action: .close)
        case .noScenicAlternative:
            return PlanFailureCopy(line: "The quickest way there is already the scenic one. Try another place.",
                                   action: .chooseAnotherPlace)
        case .nothingPretty:
            return PlanFailureCopy(line: "Not much pretty within reach of this drive. More time might find some.",
                                   action: .chooseAnotherPlace)
        case .unknownPlace:
            return PlanFailureCopy(line: "That place isn't in our list anymore. Choose another one.",
                                   action: .chooseAnotherPlace)
        case .planRefused:
            return PlanFailureCopy(line: "That route didn't pass our own checks, so it isn't shown. Try another place.",
                                   action: .chooseAnotherPlace)
        case .invalidRequest:
            return PlanFailureCopy(line: "That plan didn't go through. Try again.", action: .tryAgain)
        case .refusedOnDevice:
            return PlanFailureCopy(line: "That plan wasn't sent. Check the start and the extra time.",
                                   action: .changeStart)
        case .unexpectedResponse:
            return PlanFailureCopy(line: "Something went wrong on our side. Try again in a moment.", action: .tryAgain)
        }
    }

    @Test("every PlanSheetFailure has its one copy line and one action")
    func everyRowWhole() {
        for failure in PlanSheetFailure.allCases {
            #expect(PlanFailureCopy.of(failure) == Self.expected(failure), "\(failure)")
        }
    }

    @Test("the table covers all fourteen PlanError cases, in PlanError's order")
    func coversEveryCase() {
        #expect(PlanSheetFailure.allCases.map(\.rawValue) == [
            "quotaExhausted", "planningPaused", "routingOffline", "noRoute", "regionUnsupported", "attestUnsupported",
            "offlineDuringDrive", "noScenicAlternative", "nothingPretty", "unknownPlace", "planRefused", "invalidRequest",
            "refusedOnDevice", "unexpectedResponse",
        ])
        #expect(Set(PlanSheetFailure.allCases.map { PlanFailureCopy.of($0).line }).count == 14)
    }

    @Test("copy lines are calm: a full sentence, no exclamation mark")
    func calmLines() {
        for failure in PlanSheetFailure.allCases {
            let line = PlanFailureCopy.of(failure).line
            #expect(!line.isEmpty && line.hasSuffix(".") && !line.contains("!"), "\(failure): \(line)")
        }
    }

    @Test("every action has its button words")
    func actionTitles() {
        #expect(PlanFailureAction.allCases.map(\.title) == [
            "Surprise me instead", "Try again", "Choose another place", "Change the start", "Close",
        ])
    }
}

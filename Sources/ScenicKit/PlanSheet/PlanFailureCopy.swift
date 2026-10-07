/// One copy line and one action per `PlanSheetFailure` (the plan's Degraded states row; T-0294 R5). Calm and specific: it
/// says what happened and what still works, names no clock it cannot keep, and never raises its voice.
public struct PlanFailureCopy: Equatable, Sendable {
    public let line: String
    public let action: PlanFailureAction

    public init(line: String, action: PlanFailureAction) {
        self.line = line
        self.action = action
    }

    /// The row for `failure`. An exhaustive switch: a new case does not compile until it has its row.
    public static func of(_ failure: PlanSheetFailure) -> PlanFailureCopy {
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
        case .unknownPlace:
            return PlanFailureCopy(line: "That place isn't in our list anymore. Choose another one.",
                                   action: .chooseAnotherPlace)
        case .planRefused:
            return PlanFailureCopy(line: "That route didn't pass our own checks, so it isn't shown. Try another place.",
                                   action: .chooseAnotherPlace)
        case .invalidRequest:
            return PlanFailureCopy(line: "That plan didn't go through. Try again.", action: .tryAgain)
        case .refusedOnDevice:
            return PlanFailureCopy(line: "That plan wasn't sent. Check the start and the extra time.", action: .changeStart)
        case .unexpectedResponse:
            return PlanFailureCopy(line: "Something went wrong on our side. Try again in a moment.", action: .tryAgain)
        }
    }
}

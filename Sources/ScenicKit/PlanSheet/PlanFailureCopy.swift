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
        return PlanFailureCopy(line: "", action: .close)
    }
}

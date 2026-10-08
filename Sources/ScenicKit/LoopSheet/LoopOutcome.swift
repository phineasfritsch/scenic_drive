/// What a loop planner hands back for one ticket: a preview or a failure (T-0314 R3).
public enum LoopOutcome: Equatable, Sendable {
    case preview(LoopPreview)
    case failure(LoopFailure)
}

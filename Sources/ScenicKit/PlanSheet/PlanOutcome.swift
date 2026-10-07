/// What one ticket came back as: a route to preview, or the reason there is none (T-0294 R2).
public enum PlanOutcome: Equatable, Sendable {
    case preview(PlanPreview)
    case failure(PlanSheetFailure)
}

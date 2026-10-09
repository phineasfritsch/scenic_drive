/// What one ticket came back as: a route to preview, or the reason there is none (T-0294 R2).
public enum PlanOutcome: Equatable, Sendable {
    case preview(PlanPreview)
    case failure(PlanSheetFailure)
    /// T-0334 R4: nothing pretty within this budget, and what the answer offers instead.
    case offered(PlanOffer)
}

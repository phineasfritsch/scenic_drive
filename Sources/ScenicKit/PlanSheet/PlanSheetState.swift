/// Where the plan sheet is (T-0294 R2): idle -> searching -> chosen -> planning -> preview | failed.
public enum PlanSheetState: Equatable, Sendable {
    case idle
    case searching(PlanField, String)
    case chosen(PlanPlace)
    case planning(PlanTicket)
    case preview(PlanTicket, PlanPreview)
    case failed(PlanTicket, PlanSheetFailure)
}

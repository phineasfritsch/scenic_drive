/// Where the plan sheet is (T-0294 R2): idle -> searching -> chosen -> planning -> preview | failed | offered.
public enum PlanSheetState: Equatable, Sendable {
    case idle
    case searching(PlanField, String)
    case chosen(PlanPlace)
    case planning(PlanTicket)
    case preview(PlanTicket, PlanPreview)
    case failed(PlanTicket, PlanSheetFailure)
    /// T-0334 R4: the ticket came back nothing_pretty with these offers.
    case offered(PlanTicket, PlanOffer)
}

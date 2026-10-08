/// The loop sheet's states (T-0314 R3): start chosen -> planning -> preview | failed.
public enum LoopSheetState: Equatable, Sendable {
    case idle
    case searching(String)
    case chosen(PlanPlace)
    case planning(LoopTicket)
    case preview(LoopTicket, LoopPreview)
    case failed(LoopTicket, LoopFailure)
}

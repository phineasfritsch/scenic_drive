/// The loop planner the sheet is handed (T-0314 R3) - RoutePlanning's shape, so the feature target never sees
/// ScenicAPIClient; PlanAdapter supplies the live one.
public protocol LoopPlanning: Sendable {
    func plan(_ ticket: LoopTicket) async -> LoopOutcome
}

/// The plan sheet's one way to plan (T-0294 R1). ScenicAPIClient's `ClientPlanner` is the production conformer; the
/// sheet hands it only tickets its gate issued, so a planner is never asked before the disclaimer is accepted.
public protocol RoutePlanning: Sendable {
    func plan(_ ticket: PlanTicket) async -> PlanOutcome
}

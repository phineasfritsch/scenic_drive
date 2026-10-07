import ScenicKit

/// The planner when no Worker is configured (T-0294 R7): every ticket is routingOffline, and nothing is sent.
struct UnreachablePlanner: RoutePlanning {
    func plan(_ ticket: PlanTicket) async -> PlanOutcome {
        .failure(.routingOffline)
    }
}

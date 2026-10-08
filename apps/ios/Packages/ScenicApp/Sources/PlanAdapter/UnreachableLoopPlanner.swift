import ScenicKit

/// With no planner configured every loop says the planner could not be reached, and sends nothing.
struct UnreachableLoopPlanner: LoopPlanning {
    func plan(_ ticket: LoopTicket) async -> LoopOutcome {
        .failure(.routingOffline)
    }
}

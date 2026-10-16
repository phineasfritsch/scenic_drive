import ScenicKit

/// With no planner configured every loop says the planner could not be reached, and sends nothing.
struct UnreachableLoopPlanner: LoopPlanning {
    func plan(_ ticket: LoopTicket) async -> LoopOutcome {
        .failure(.routingOffline)
    }

    /// T-0364 R3: with no Worker there is no /config to read, so nothing degrades.
    func degrade() async -> ConfigDegrade {
        .clear
    }
}

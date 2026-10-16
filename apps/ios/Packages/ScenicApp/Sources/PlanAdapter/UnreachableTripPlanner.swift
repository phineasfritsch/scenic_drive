import ScenicKit

/// With no planner configured every road trip says the planner could not be reached, and sends nothing.
struct UnreachableTripPlanner: TripPlanning {
    func plan(_ ticket: TripTicket) async -> TripOutcome {
        .failure(.routingOffline)
    }

    /// T-0364 R3: with no Worker there is no /config to read, so nothing degrades.
    func degrade() async -> ConfigDegrade {
        .clear
    }
}

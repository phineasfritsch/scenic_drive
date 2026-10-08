import ScenicKit

/// With no planner configured every road trip says the planner could not be reached, and sends nothing.
struct UnreachableTripPlanner: TripPlanning {
    func plan(_ ticket: TripTicket) async -> TripOutcome {
        .failure(.routingOffline)
    }
}

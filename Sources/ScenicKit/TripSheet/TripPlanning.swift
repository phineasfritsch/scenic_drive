/// The road-trip planner the sheet is handed (T-0313 R4) - RoutePlanning's shape, so the feature target never sees
/// ScenicAPIClient; PlanAdapter supplies the live one.
public protocol TripPlanning: Sendable {
    func plan(_ ticket: TripTicket) async -> TripOutcome
}

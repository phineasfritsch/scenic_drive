/// What a road-trip planner hands back for one ticket: an itinerary or a failure (T-0313 R4).
public enum TripOutcome: Equatable, Sendable {
    case itinerary(TripItinerary)
    case failure(TripFailure)
}

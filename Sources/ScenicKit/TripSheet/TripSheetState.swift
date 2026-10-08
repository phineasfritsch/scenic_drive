/// The road-trip sheet's states (T-0313 R4): destination chosen -> planning -> itinerary | failed.
public enum TripSheetState: Equatable, Sendable {
    case idle
    case searching(PlanField, String)
    case chosen(PlanPlace)
    case planning(TripTicket)
    case itinerary(TripTicket, TripItinerary)
    case failed(TripTicket, TripFailure)
}

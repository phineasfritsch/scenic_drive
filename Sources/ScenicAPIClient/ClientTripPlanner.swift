import Foundation
import ScenicKit

/// The live road-trip planner (T-0313 R4): one TripClient call per ticket, the answer turned into the itinerary the
/// sheet shows. A day's path is its leg, which only a full itinerary carries (R5).
public struct ClientTripPlanner: TripPlanning {
    public let client: TripClient

    public init(client: TripClient) {
        self.client = client
    }

    public func plan(_ ticket: TripTicket) async -> TripOutcome {
        do {
            let response = try await client.trip(from: ticket.origin, to: ticket.place, days: ticket.days,
                                                 extraBudgetPercent: ticket.extraBudgetPercent)
            return .itinerary(Self.itinerary(of: response))
        } catch {
            return .failure(error.failure)
        }
    }

    public static func itinerary(of response: TripResponse) -> TripItinerary {
        TripItinerary(isFull: response.isFull, etaSeconds: response.etaSeconds,
                      fastestEtaSeconds: response.fastestEtaSeconds, etaIsEstimate: response.etaIsEstimate,
                      days: response.days.map {
                          TripItineraryDay(day: $0.day, driveSeconds: $0.driveSeconds,
                                           distanceMeters: $0.distanceMeters, overnight: $0.overnight,
                                           path: $0.leg)
                      })
    }
}

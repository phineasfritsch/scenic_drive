import ScenicKit
import Telemetry

/// The road-trip sheet's planner with plan_requested (feature road_trip, budget 0: a trip's budget is a percent,
/// not minutes - R7) and plan_result (T-0355 R5).
struct TelemetryTripPlanner: TripPlanning {
    let inner: any TripPlanning

    func plan(_ ticket: TripTicket) async -> TripOutcome {
        LiveTelemetry.planRequested(.roadTrip, budgetMinutes: 0, origin: ticket.origin)
        let outcome = await inner.plan(ticket)
        LiveTelemetry.planResult(Self.kind(outcome))
        return outcome
    }

    static func kind(_ outcome: TripOutcome) -> PlanResultKind {
        switch outcome {
        case .itinerary: return .routed
        case .failure(.quotaExhausted): return .quotaExceeded
        case .failure(.ceilingBreached), .failure(.nothingPretty): return .noAlternative
        case .failure: return .failed
        }
    }
}

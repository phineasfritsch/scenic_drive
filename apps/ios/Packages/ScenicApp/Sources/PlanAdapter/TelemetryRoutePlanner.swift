import ScenicKit
import Telemetry

/// The plan sheet's planner with plan_requested before the plan and plan_result after it (T-0355 R5, R7).
struct TelemetryRoutePlanner: RoutePlanning {
    let inner: any RoutePlanning

    func plan(_ ticket: PlanTicket) async -> PlanOutcome {
        LiveTelemetry.planRequested(.scenic, budgetMinutes: ticket.budgetMinutes, origin: ticket.origin)
        let outcome = await inner.plan(ticket)
        LiveTelemetry.planResult(Self.kind(outcome))
        return outcome
    }

    static func kind(_ outcome: PlanOutcome) -> PlanResultKind {
        switch outcome {
        case .preview: return .routed
        case .offered: return .noAlternative
        case .failure(.quotaExhausted): return .quotaExceeded
        case .failure(.noScenicAlternative), .failure(.nothingPretty): return .noAlternative
        case .failure: return .failed
        }
    }
}

import ScenicKit
import Telemetry

/// The loop sheet's planner with plan_requested (feature loop, the loop's minutes) and plan_result (T-0355 R5, R7).
struct TelemetryLoopPlanner: LoopPlanning {
    let inner: any LoopPlanning

    func plan(_ ticket: LoopTicket) async -> LoopOutcome {
        LiveTelemetry.planRequested(.loop, budgetMinutes: ticket.minutes, origin: ticket.start)
        let outcome = await inner.plan(ticket)
        LiveTelemetry.planResult(Self.kind(outcome))
        return outcome
    }

    static func kind(_ outcome: LoopOutcome) -> PlanResultKind {
        switch outcome {
        case .preview: return .routed
        case .failure(.quotaExhausted): return .quotaExceeded
        case .failure(.noCleanLoop), .failure(.nothingPretty): return .noAlternative
        case .failure: return .failed
        }
    }
}

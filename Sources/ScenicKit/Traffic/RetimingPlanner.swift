import Foundation

/// The plan sheet's planner with the device's learned speeds on the answer (T-0343 R4): a preview that carries time
/// runs comes back as RetimedPreview.of over the learner, departing `now()` - when the answer arrives - so the card
/// and the drive it starts show the same ETA and badge. A preview without runs, a failure and an offer pass through.
public struct RetimingPlanner: RoutePlanning {
    private let inner: any RoutePlanning
    private let learner: CorridorLearner
    private let now: @Sendable () -> Date

    public init(inner: any RoutePlanning, learner: CorridorLearner, now: @escaping @Sendable () -> Date) {
        self.inner = inner
        self.learner = learner
        self.now = now
    }

    public func plan(_ ticket: PlanTicket) async -> PlanOutcome {
        let outcome = await inner.plan(ticket)
        guard case let .preview(preview) = outcome, let runs = preview.timeRuns else { return outcome }
        let speeds = await learner.speeds
        return .preview(RetimedPreview.of(preview, timeRuns: runs, by: speeds, departsAt: now()))
    }
}

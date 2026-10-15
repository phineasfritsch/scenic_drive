import ScenicKit

/// The plan sheet's planner and its waitlist as one value (T-0360 R5): LivePlanner.make() hands the sheet this, so the
/// shell's one call builds both. Without an https base there is no client and the waitlist answers `unavailable`,
/// sending nothing.
struct WaitlistRoutePlanner: RoutePlanning, WaitlistJoining {
    let planner: any RoutePlanning
    let waitlist: (any WaitlistJoining)?

    func plan(_ ticket: PlanTicket) async -> PlanOutcome {
        await planner.plan(ticket)
    }

    func joinWaitlist(near start: Coordinate) async -> WaitlistAnswer {
        guard let waitlist else { return .unavailable }
        return await waitlist.joinWaitlist(near: start)
    }
}

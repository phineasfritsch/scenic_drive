import ScenicKit

/// The plan sheet's planner, its waitlist and (T-0362 R9) its address search as one value (T-0360 R5): LivePlanner.make()
/// hands the sheet this, so the shell's one call builds all three. Without an https base there is no client: the
/// waitlist answers `unavailable` and the search is NoPlaceSearch, both sending nothing.
struct WaitlistRoutePlanner: RoutePlanning, WaitlistJoining, PlaceSearching {
    let planner: any RoutePlanning
    let waitlist: (any WaitlistJoining)?
    let search: any PlaceSearching

    func plan(_ ticket: PlanTicket) async -> PlanOutcome {
        await planner.plan(ticket)
    }

    /// The config gate is the wrapped planner's (T-0357 R7, merge with T-0360): asking it joins nothing and plans nothing.
    func degrade() async -> ConfigDegrade { await planner.degrade() }

    func joinWaitlist(near start: Coordinate) async -> WaitlistAnswer {
        guard let waitlist else { return .unavailable }
        return await waitlist.joinWaitlist(near: start)
    }

    func searchPlaces(_ query: String, near: Coordinate?) async -> PlaceSearchAnswer {
        await search.searchPlaces(query, near: near)
    }
}

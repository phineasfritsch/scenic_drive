/// The plan sheet's one way to ask for a region it cannot plan in yet (T-0360 R5). ScenicAPIClient's
/// `WaitlistClient` is the production conformer: it sends at most the one H3 resolution-5 cell around `start`
/// rounded to 2 decimals, once per cell per install, and never the coordinate itself (R2, R3).
public protocol WaitlistJoining: Sendable {
    func joinWaitlist(near start: Coordinate) async -> WaitlistAnswer
}

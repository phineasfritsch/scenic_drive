/// What a reroute needs to continue THIS plan (T-0328 R1): the token the Worker remembered its pins and lambda under,
/// and the destination place and budget the plan was asked with. Held in memory for the drive only - never Codable,
/// never in a SavedDraft, never printed.
public struct PlanContinuation: Equatable, Sendable {
    public let token: String
    public let place: Int64
    public let budgetMinutes: Int

    public init(token: String, place: Int64, budgetMinutes: Int) {
        self.token = token
        self.place = place
        self.budgetMinutes = budgetMinutes
    }
}

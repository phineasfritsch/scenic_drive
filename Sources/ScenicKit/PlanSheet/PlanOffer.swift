/// What a nothing_pretty answer offers the sheet (T-0334 R4): the extra minutes the plan asked with, and the two ways
/// on - "+40" (`moreTimeMinutes`, nil past the Worker's 180) and "all back roads" (its real ETA, and the whole minutes a
/// back-roads plan must name to cover it - nil when no budget can). ScenicAPIClient's `ClientPlanner` builds it from
/// `NothingPrettyOffer` only when the answer echoes the ticket's own budget.
public struct PlanOffer: Equatable, Sendable {
    public let budgetMinutes: Int
    public let moreTimeMinutes: Int?
    public let backRoadsEtaSeconds: Double?
    public let backRoadsBudgetMinutes: Int?

    public init(budgetMinutes: Int, moreTimeMinutes: Int?, backRoadsEtaSeconds: Double?, backRoadsBudgetMinutes: Int?) {
        self.budgetMinutes = budgetMinutes
        self.moreTimeMinutes = moreTimeMinutes
        self.backRoadsEtaSeconds = backRoadsEtaSeconds
        self.backRoadsBudgetMinutes = backRoadsBudgetMinutes
    }
}

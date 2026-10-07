/// One saved drive as the Saved list holds it (T-0306 R4): its store id, its name, when it was saved, whether it
/// needs a re-plan, the budget, and the route's two saved ends - which are kept for the replay and NEVER shown. There
/// is no address field, and the only lines the list draws are `name` and `detail` (P-PRIV-05).
public struct SavedRow: Equatable, Sendable {
    public let id: Int64
    public let name: String
    /// Unix seconds, as the user store keeps it.
    public let createdAt: Int64
    public let needsReplan: Bool
    /// The saved first point (5 dp), the replay's origin before it is cut to 2 dp. Not drawn.
    public let start: Coordinate?
    /// The saved last point (5 dp), from which the replay's destination place is found on the device. Not drawn.
    public let end: Coordinate?
    public let budgetMinutes: Int

    public init(id: Int64, name: String, createdAt: Int64, needsReplan: Bool, start: Coordinate?, end: Coordinate?,
                budgetMinutes: Int) {
        self.id = id
        self.name = name
        self.createdAt = createdAt
        self.needsReplan = needsReplan
        self.start = start
        self.end = end
        self.budgetMinutes = budgetMinutes
    }

    /// The row's second line: the extra minutes it was planned with, and the re-plan note when it needs one.
    public var detail: String {
        needsReplan ? "Needs a re-plan · \(budgetMinutes) min extra" : "\(budgetMinutes) min extra"
    }

    /// The same row under a new name.
    func renamed(_ newName: String) -> SavedRow {
        SavedRow(id: id, name: newName, createdAt: createdAt, needsReplan: needsReplan, start: start, end: end,
                 budgetMinutes: budgetMinutes)
    }
}

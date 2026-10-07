import Foundation

/// The Saved list's state machine (T-0306 R4): the rows, newest first, and the one thing the user is doing to one of
/// them. Edits come back as a `SavedEdit` for the view to hand the user store; a replay comes back as a `SavedReplay`
/// for the plan sheet's gate. A drive that needs a re-plan - or has no saved ends, or no place near its end - is never
/// replayed: the list shows `needsReplanLine` instead and nothing is issued.
public struct SavedList: Equatable, Sendable {
    /// The longest name a rename keeps, after trimming.
    public static let maxNameLength = 60
    /// The refused replay's own line (calm copy, memory owner-route-intent).
    public static let needsReplanLine =
        "The roads on this drive have changed since you saved it. Plan it fresh from the plan sheet."

    public private(set) var state: SavedListState = .loading
    public private(set) var rows: [SavedRow] = []

    public init() {}

    init(rows: [SavedRow], state: SavedListState) {
        self.rows = rows
        self.state = state
    }

    /// The store's rows arrived: kept newest first (a tie to the higher id), and the list is shown.
    public mutating func load(_ rows: [SavedRow]) {
        self.rows = rows.sorted { ($0.createdAt, $0.id) > ($1.createdAt, $1.id) }
        state = .list
    }

    public mutating func beginRename(_ id: Int64) {
        guard case .list = state, let row = row(id) else { return }
        state = .renaming(id, row.name)
    }

    public mutating func editName(_ text: String) {
        guard case .renaming(let id, _) = state else { return }
        state = .renaming(id, text)
    }

    /// The trimmed name of 1...maxNameLength characters is kept and handed to the store; otherwise nothing changes.
    public mutating func commitRename() -> SavedEdit? {
        guard case .renaming(let id, let text) = state, let index = rows.firstIndex(where: { $0.id == id }) else {
            return nil
        }
        let name = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard (1...Self.maxNameLength).contains(name.count) else { return nil }
        rows[index] = rows[index].renamed(name)
        state = .list
        return .rename(id, name)
    }

    public mutating func askDelete(_ id: Int64) {
        guard case .list = state, row(id) != nil else { return }
        state = .confirmDelete(id)
    }

    public mutating func confirmDelete() -> SavedEdit? {
        guard case .confirmDelete(let id) = state else { return nil }
        rows.removeAll { $0.id == id }
        state = .list
        return .delete(id)
    }

    /// Back to the list from a rename, a delete question or a refused replay.
    public mutating func cancel() {
        switch state {
        case .renaming, .confirmDelete, .needsReplan: state = .list
        case .loading, .list, .replaying: return
        }
    }

    /// Replay `id` with the corpus places near its saved end: a `SavedReplay` (the start at 2 dp), or nil and the
    /// needsReplan state when the drive needs a re-plan, has no saved ends or has no place within reach.
    public mutating func replay(_ id: Int64, near places: [PlanPlace]) -> SavedReplay? {
        guard case .list = state, let row = row(id) else { return nil }
        guard !row.needsReplan, let start = row.start, let end = row.end,
              let place = SavedReplay.nearest(to: end, among: places) else {
            state = .needsReplan(id)
            return nil
        }
        state = .replaying(id)
        return SavedReplay(id: id, start: PlanSheet.twoDecimals(start), destination: place,
                           budgetMinutes: row.budgetMinutes)
    }

    /// The replay was handed to the plan sheet.
    public mutating func finishReplay() {
        guard case .replaying = state else { return }
        state = .list
    }

    private func row(_ id: Int64) -> SavedRow? {
        rows.first { $0.id == id }
    }
}

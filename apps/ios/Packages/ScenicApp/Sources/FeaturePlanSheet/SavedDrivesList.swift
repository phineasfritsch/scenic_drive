import DesignSystem
import ScenicKit
import SwiftUI

/// The Saved list (T-0306 R1, R4): in-sheet content of the full-height plan sheet, never a presentation over the map
/// (P-ATTR-01). A row draws its name and its detail line and nothing else - never an address (P-PRIV-05). Rename and
/// delete are asked inline; a replay goes back to the plan sheet's gate.
struct SavedDrivesList: View {
    @Binding var list: SavedList
    let onReplay: (SavedReplay) -> Void

    var body: some View {
        List {
            if case .loading = list.state {
                ProgressView()
            } else {
                if case .needsReplan = list.state {
                    Section {
                        Text(SavedList.needsReplanLine)
                            .foregroundStyle(DesignTokens.fg)
                            .fixedSize(horizontal: false, vertical: true)
                        Button("OK") { list.cancel() }
                    }
                }
                if list.rows.isEmpty {
                    Text("No saved drives yet. Save one from a route preview.")
                        .foregroundStyle(DesignTokens.fgMuted)
                }
                ForEach(list.rows, id: \.id) { row in
                    rowView(row)
                }
            }
        }
        .onAppear { list.load(PlanRehearsal.atLaunch.map { $0.savedRows } ?? SavedDriveShelf.rows()) }
    }

    @ViewBuilder private func rowView(_ row: SavedRow) -> some View {
        switch list.state {
        case .renaming(let id, let text) where id == row.id:
            VStack(alignment: .leading, spacing: 8) {
                TextField("Name", text: Binding(get: { text }, set: { list.editName($0) }))
                HStack(spacing: 16) {
                    Button("Keep this name") {
                        if let edit = list.commitRename() { SavedDriveShelf.apply(edit) }
                    }
                    Button("Cancel") { list.cancel() }
                }
                .buttonStyle(.borderless)
            }
        case .confirmDelete(let id) where id == row.id:
            VStack(alignment: .leading, spacing: 8) {
                Text("Delete \(row.name)?")
                    .foregroundStyle(DesignTokens.fg)
                HStack(spacing: 16) {
                    Button("Delete", role: .destructive) {
                        if let edit = list.confirmDelete() { SavedDriveShelf.apply(edit) }
                    }
                    Button("Keep it") { list.cancel() }
                }
                .buttonStyle(.borderless)
            }
        default:
            VStack(alignment: .leading, spacing: 6) {
                Text(row.name)
                    .font(.body)
                    .foregroundStyle(DesignTokens.fg)
                Text(row.detail)
                    .font(.footnote)
                    .foregroundStyle(DesignTokens.fgMuted)
                HStack(spacing: 16) {
                    Button("Drive it again") { replay(row) }
                    Button("Rename") { list.beginRename(row.id) }
                    Button("Delete") { list.askDelete(row.id) }
                }
                .buttonStyle(.borderless)
            }
        }
    }

    /// The places near the saved end are looked up on the device; the list decides whether there is a replay at all.
    private func replay(_ row: SavedRow) {
        let places = row.end.map { SavedDriveShelf.places(near: $0) } ?? []
        guard let saved = list.replay(row.id, near: places) else { return }
        list.finishReplay()
        onReplay(saved)
    }
}

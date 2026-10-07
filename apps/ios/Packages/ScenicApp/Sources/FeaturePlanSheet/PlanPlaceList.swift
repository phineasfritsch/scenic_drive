import DesignSystem
import ScenicKit
import SwiftUI

/// The search half of the plan sheet: a field, and the corpus places matching it, best first (T-0294).
struct PlanPlaceList: View {
    let field: PlanField
    @Binding var query: String
    let onPick: (PlanPlace) -> Void
    let onCancel: () -> Void

    var body: some View {
        List {
            Section {
                TextField(field == .start ? "Start from a place" : "Where to", text: $query)
                    .textInputAutocapitalization(.words)
                    .autocorrectionDisabled()
                    .accessibilityIdentifier("plan.search")
            }
            Section {
                ForEach(PlanPlaceSearch.find(query), id: \.id) { place in
                    Button(place.name) { onPick(place) }
                }
            }
        }
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button("Back", action: onCancel)
            }
        }
    }
}

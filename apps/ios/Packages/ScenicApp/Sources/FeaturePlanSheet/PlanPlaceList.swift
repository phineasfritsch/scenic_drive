import DesignSystem
import ScenicKit
import SwiftUI

/// The search half of the plan sheet: a field, the corpus places matching it, best first (T-0294), and (T-0362) the
/// addresses the Worker found for the SUBMITTED text. The corpus list follows every keystroke on the device; the address
/// search is asked only from the field's submit action, once per submit (R6), and its answer is dropped as soon as the
/// text changes so a list never stands under text it was not asked for. The loop and trip screens pass no search
/// (T-0362 R10): /trip resolves corpus ids only, and the loop keeps the list it had.
struct PlanPlaceList: View {
    let field: PlanField
    @Binding var query: String
    var search: PlaceSearchSubmit?
    var start: PlanPlace?
    var destination: PlanPlace?
    /// T-0373 R3: a DEBUG rehearsal's answer, shown from the first frame; nil from every production call site.
    var rehearsed: PlaceSearchAnswer? = nil
    let onPick: (PlanPlace) -> Void
    let onCancel: () -> Void
    @State private var answer: PlaceSearchAnswer?
    @State private var asking = false

    var body: some View {
        List {
            Section {
                TextField(field == .start ? "Start from a place" : "Where to", text: $query)
                    .textInputAutocapitalization(.words)
                    .autocorrectionDisabled()
                    .submitLabel(.search)
                    .onSubmit(submit)
                    .accessibilityIdentifier("plan.search")
            } footer: {
                if search != nil { Text("Press Search to look up a street address.") }
            }
            Section {
                ForEach(PlanPlaceSearch.find(query), id: \.id) { place in
                    Button(place.name) { onPick(place) }
                }
            }
            addresses
        }
        .onAppear { if answer == nil, let rehearsed { answer = rehearsed } }
        .onChange(of: query) { answer = nil }
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button("Back", action: onCancel)
            }
        }
    }

    @ViewBuilder private var addresses: some View {
        if asking {
            Section("Addresses") { ProgressView() }
        } else if let answer {
            Section("Addresses") {
                switch answer {
                case .places(let places):
                    ForEach(places, id: \.id) { place in
                        Button(place.name) { onPick(place) }
                    }
                case .notice(let line):
                    Text(line).accessibilityIdentifier("plan.search.notice")
                }
            }
        }
    }

    /// R6: the one call site of the address search - a submit, never a keystroke; one submit at a time.
    private func submit() {
        guard let search, !asking else { return }
        let text = query
        asking = true
        Task {
            let found = await search.submit(text, start: start, destination: destination)
            asking = false
            if query == text { answer = found }
        }
    }
}

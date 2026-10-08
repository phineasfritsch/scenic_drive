import DesignSystem
import ScenicKit
import SwiftUI

/// The road-trip content of the full-height plan sheet (T-0313 R4): the form (start, destination, days, extra time),
/// the place search, the planning wait, the itinerary and a refusal. Every ticket comes from TripSheet's gate, so
/// nothing is planned before the safety note is read (P-SAFE-03).
struct RoadTripScreen: View {
    @Binding var trip: TripSheet
    let planner: any TripPlanning
    let dayLinks: ([Coordinate]) -> [URL]
    @State private var query = ""

    init(trip: Binding<TripSheet>, planner: any TripPlanning, dayLinks: @escaping ([Coordinate]) -> [URL]) {
        _trip = trip
        self.planner = planner
        self.dayLinks = dayLinks
    }

    var body: some View {
        switch trip.state {
        case .idle, .chosen:
            form
        case .searching(let field, _):
            PlanPlaceList(field: field, query: $query, onPick: { trip.choose($0) }, onCancel: { trip.endSearch() })
        case .planning:
            ProgressView("Laying out the days")
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        case .itinerary(_, let itinerary):
            TripItineraryCard(itinerary: itinerary, destination: trip.destination?.name ?? "", dayLinks: dayLinks,
                              onChange: { trip.edit() })
        case .failed(_, let failure):
            VStack(alignment: .leading, spacing: 12) {
                Text(failure.line)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("trip.failure")
                Button("Try again", action: planTrip)
                Button("Change the trip") { trip.edit() }
            }
            .padding()
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
    }

    private var form: some View {
        Form {
            Section("From") {
                Button(trip.start?.name ?? "Choose a start") { searchFor(.start) }
                    .accessibilityIdentifier("trip.from")
            }
            Section("To") {
                Button(trip.destination?.name ?? "Choose a place") { searchFor(.destination) }
                    .accessibilityIdentifier("trip.to")
            }
            Section {
                Stepper(trip.days == 1 ? "1 day" : "\(trip.days) days",
                        value: Binding(get: { trip.days }, set: { trip.setDays($0) }), in: TripSheet.dayRange)
            } header: {
                Text("Days")
            } footer: {
                Text("Each day holds up to 6 hours or 300 miles of driving.")
            }
            Section("Extra time") {
                Stepper("Up to \(trip.extraBudgetPercent)% longer than the fastest way",
                        value: Binding(get: { trip.extraBudgetPercent }, set: { trip.setExtraPercent($0) }),
                        in: TripSheet.extraPercentRange, step: 10)
            }
            Section {
                if trip.disclaimerAccepted {
                    Button("Plan the road trip", action: planTrip)
                        .disabled(trip.start == nil || trip.destination == nil)
                        .accessibilityIdentifier("trip.go")
                } else {
                    Text("Planning starts after the safety note. Tap Apple Maps on any drive on the home screen to read it.")
                        .foregroundStyle(DesignTokens.fgMuted)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    private func searchFor(_ field: PlanField) {
        query = ""
        trip.search("", for: field)
    }

    private func planTrip() {
        guard let ticket = trip.startPlanning() else { return }
        let planner = self.planner
        Task { @MainActor in
            let outcome = await planner.plan(ticket)
            trip.finish(ticket, with: outcome)
        }
    }
}

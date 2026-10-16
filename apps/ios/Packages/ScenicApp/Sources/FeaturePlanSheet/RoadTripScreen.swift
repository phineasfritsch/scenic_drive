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
    /// T-0365 R4: the plan sheet's own joiner - one WaitlistClient, one memory, so an area counts once per install.
    let waitlist: any WaitlistJoining
    @State private var query = ""
    /// T-0365: the waitlist card replaces the failure from the tap; nil answer while the request is out.
    @State private var showingWaitlist = false
    @State private var waitlistAnswer: WaitlistAnswer?

    init(trip: Binding<TripSheet>, planner: any TripPlanning, waitlist: any WaitlistJoining,
         dayLinks: @escaping ([Coordinate]) -> [URL]) {
        _trip = trip
        self.planner = planner
        self.waitlist = waitlist
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
            if showingWaitlist {
                WaitlistCard(answer: waitlistAnswer, onChangeStart: { searchFor(.start) })
            } else {
                VStack(alignment: .leading, spacing: 12) {
                    Text(failure.line)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("trip.failure")
                    if let action = failure.waitlistAction {
                        Button(action.title, action: joinWaitlist)
                            .accessibilityIdentifier("trip.failure.waitlist")
                    }
                    Button("Try again", action: planTrip)
                    Button("Change the trip") { trip.edit() }
                }
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            }
        }
    }

    /// T-0365 R3, R4: the sheet's waitlistStart only, at most one request, the answer shown in place of the failure.
    private func joinWaitlist() {
        guard !showingWaitlist, let start = trip.waitlistStart else { return }
        showingWaitlist = true
        waitlistAnswer = nil
        let waitlist = self.waitlist
        Task { @MainActor in
            waitlistAnswer = await waitlist.joinWaitlist(near: start)
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
                if let notice = trip.degrade.notice(on: .trip) {
                    // T-0364 R3: a pause, an update or road trips switched off, heard from /config before the tap.
                    Text(notice)
                        .foregroundStyle(DesignTokens.fg)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("trip.degrade")
                } else if trip.disclaimerAccepted {
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
        .task {
            // T-0364 R3: this screen's /config degrade, each time its form shows; a DEBUG rehearsal keeps its own.
            guard PlanRehearsal.atLaunch == nil else { return }
            trip.setDegrade(await planner.degrade())
        }
    }

    private func searchFor(_ field: PlanField) {
        query = ""
        showingWaitlist = false
        waitlistAnswer = nil
        trip.search("", for: field)
    }

    private func planTrip() {
        guard let ticket = trip.startPlanning() else { return }
        showingWaitlist = false
        waitlistAnswer = nil
        let planner = self.planner
        Task { @MainActor in
            let outcome = await planner.plan(ticket)
            trip.finish(ticket, with: outcome)
        }
    }
}

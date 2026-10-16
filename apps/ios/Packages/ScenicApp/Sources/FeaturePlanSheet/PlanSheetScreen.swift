import DesignSystem
import ScenicKit
import SwiftUI

/// The plan sheet (T-0294): a start and a destination typed against the bundled corpus, the extra minutes, Plan,
/// and the preview or the failure's one line and one action.
///
/// Every plan passes `PlanSheet.startPlanning()`, the gate: before the home's safety disclaimer has been accepted
/// on this device there is no ticket, so the planner is never called (P-SAFE-03, R3). The sheet READS the home's
/// acknowledgement and never writes it - the home's disclaimer stays the one place it is given. The start is a
/// typed place (R4): this module asks for no location at all.
///
/// Presented full height, as Settings is, with no detent: a partial sheet over the map would cover its credit
/// (P-ATTR-01).
public struct PlanSheetScreen: View {
    /// T-0362 R9: the same value is the sheet's address search, so the shell's one LivePlanner.make() builds it too.
    private let planner: any RoutePlanning & WaitlistJoining & PlaceSearching
    /// T-0360: the waitlist card replaces the failure card from the tap; nil answer while the request is out.
    @State private var showingWaitlist = false
    @State private var waitlistAnswer: WaitlistAnswer?
    private let onClose: () -> Void
    /// The door to the drive (T-0324 R4): the shell takes the previewed plan and shows the drive in place of the home.
    private let onDrive: (PlanPreview) -> Void

    /// The home's on-device acknowledgement, read only (R3).
    @AppStorage("safety.disclaimer.acknowledged.v1") private var safetyNoteRead = false
    @State private var sheet = PlanSheet(disclaimerAccepted: false)
    @State private var query = ""
    /// The Saved list, shown in place of the plan form - in-sheet content, not a presentation (T-0306 R1).
    @State private var showingSaved = false
    @State private var saved = SavedList()
    @State private var saveLine: String?
    /// The road trip, shown in place of the plan form - in-sheet content, not a presentation (T-0313 R4).
    @State private var showingTrip = false
    @State private var trip = TripSheet(disclaimerAccepted: false)
    private let tripPlanner: any TripPlanning
    private let dayLinks: ([Coordinate]) -> [URL]
    /// The loop, shown in place of the plan form - in-sheet content, not a presentation (T-0314 R3).
    @State private var showingLoop = false
    @State private var loop = LoopSheet(disclaimerAccepted: false)
    private let loopPlanner: any LoopPlanning
    private let loopLink: (Coordinate, [Coordinate]) -> URL?
    /// T-0373 R3: a DEBUG rehearsal's address-search answer, shown on the search list; nil in every release build.
    private var rehearsedSearch: PlaceSearchAnswer?

    public init(planner: any RoutePlanning & WaitlistJoining & PlaceSearching, tripPlanner: any TripPlanning,
                dayLinks: @escaping ([Coordinate]) -> [URL], loopPlanner: any LoopPlanning,
                loopLink: @escaping (Coordinate, [Coordinate]) -> URL?, onDrive: @escaping (PlanPreview) -> Void,
                onClose: @escaping () -> Void) {
        self.planner = planner
        self.tripPlanner = tripPlanner
        self.dayLinks = dayLinks
        self.loopPlanner = loopPlanner
        self.loopLink = loopLink
        self.onClose = onClose
        self.onDrive = onDrive
        // T-0336: a DEBUG `-screen` rehearsal opens on its fixed state; nil in every release build.
        if let rehearsal = PlanRehearsal.atLaunch {
            _sheet = State(initialValue: rehearsal.sheet)
            _loop = State(initialValue: rehearsal.loop)
            _trip = State(initialValue: rehearsal.trip)
            _showingLoop = State(initialValue: rehearsal.tab == .loop)
            _showingTrip = State(initialValue: rehearsal.tab == .trip)
            _showingSaved = State(initialValue: rehearsal.tab == .saved)
            // T-0373 R2: the plan tab's waitlist answer only; the loop and trip screens seed their own.
            _showingWaitlist = State(initialValue: rehearsal.tab == .plan && rehearsal.waitlist != nil)
            _waitlistAnswer = State(initialValue: rehearsal.tab == .plan ? rehearsal.waitlist : nil)
            _query = State(initialValue: rehearsal.searchQuery)
            rehearsedSearch = rehearsal.searchAnswer
        }
    }

    public var body: some View {
        NavigationStack {
            content
                .navigationTitle(showingLoop ? "Just drive a loop" : showingTrip ? "Plan a road trip" : "Plan a drive")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close", action: onClose)
                    }
                    ToolbarItem(placement: .primaryAction) {
                        Button(showingSaved ? "Plan" : "Saved") {
                            showingSaved.toggle()
                            showingTrip = false
                            showingLoop = false
                        }
                        .accessibilityIdentifier("plan.savedTab")
                    }
                    ToolbarItem(placement: .bottomBar) {
                        Button(showingTrip ? "Plan a drive" : "Plan a road trip") {
                            showingTrip.toggle()
                            showingSaved = false
                            showingLoop = false
                        }
                        .accessibilityIdentifier("plan.tripTab")
                    }
                    ToolbarItem(placement: .bottomBar) {
                        Button(showingLoop ? "Plan a drive" : "Just drive a loop") {
                            showingLoop.toggle()
                            showingSaved = false
                            showingTrip = false
                        }
                        .accessibilityIdentifier("plan.loopTab")
                    }
                }
        }
        .onAppear {
            sheet.setDisclaimerAccepted(safetyNoteRead)
            trip.setDisclaimerAccepted(safetyNoteRead)
            loop.setDisclaimerAccepted(safetyNoteRead)
        }
        .task {
            // T-0357 R7: the planner's /config degrade, once per appearance; a DEBUG rehearsal keeps its own.
            guard PlanRehearsal.atLaunch == nil else { return }
            sheet.setDegrade(await planner.degrade())
        }
        .onChange(of: safetyNoteRead) { _, accepted in
            sheet.setDisclaimerAccepted(accepted)
            trip.setDisclaimerAccepted(accepted)
            loop.setDisclaimerAccepted(accepted)
        }
    }

    @ViewBuilder private var content: some View {
        if showingLoop {
            LoopScreen(loop: $loop, planner: loopPlanner, waitlist: planner, mapsURL: loopLink)
        } else if showingTrip {
            RoadTripScreen(trip: $trip, planner: tripPlanner, waitlist: planner, dayLinks: dayLinks)
        } else if showingSaved {
            SavedDrivesList(list: $saved, onReplay: replay)
        } else {
            planContent
        }
    }

    @ViewBuilder private var planContent: some View {
        switch sheet.state {
        case .idle, .chosen:
            form
        case .searching(let field, _):
            PlanPlaceList(field: field, query: $query, search: PlaceSearchSubmit(searcher: planner), start: sheet.start,
                          destination: sheet.destination, rehearsed: rehearsedSearch, onPick: { sheet.choose($0) },
                          onCancel: { sheet.endSearch() })
        case .planning:
            ProgressView("Finding a calmer way there")
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        case .preview(let ticket, let preview):
            PlanPreviewCard(preview: preview, destination: sheet.destination?.name ?? "", saveLine: saveLine,
                            onSave: { save(preview, budgetMinutes: ticket.budgetMinutes) },
                            onChangePlace: { searchFor(.destination) }, onDrive: { onDrive(preview) })
        case .failed(_, let failure):
            if showingWaitlist {
                WaitlistCard(answer: waitlistAnswer, onChangeStart: { searchFor(.start) })
            } else {
                PlanFailureCard(copy: PlanFailureCopy.of(failure), onAction: act)
            }
        case .offered(_, let offer):
            // T-0334: each offer is ONE fresh plan through the gate, run down the same planner path.
            PlanOfferCard(copy: PlanOfferCopy.of(offer),
                          onMoreTime: { if let ticket = sheet.takeMoreTime() { run(ticket) } },
                          onBackRoads: { if let ticket = sheet.takeBackRoads() { run(ticket) } },
                          onAction: act)
        }
    }

    private var form: some View {
        Form {
            Section("From") {
                Button(sheet.start?.name ?? "Choose a start") { searchFor(.start) }
                    .accessibilityIdentifier("plan.from")
            }
            Section("To") {
                Button(sheet.destination?.name ?? "Choose a place") { searchFor(.destination) }
                    .accessibilityIdentifier("plan.to")
            }
            Section("Extra time") {
                Stepper("\(sheet.budgetMinutes) min more than the fastest way",
                        value: Binding(get: { sheet.budgetMinutes }, set: { sheet.setBudget($0) }),
                        in: 0...PlanSheet.maxBudgetMinutes, step: 15)
            }
            Section {
                if let notice = sheet.degrade.notice(on: .plan) {
                    // T-0357 R6: a pause or an update heard from /config, said before the tap; the gate issues nothing.
                    Text(notice)
                        .foregroundStyle(DesignTokens.fg)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("plan.degrade")
                } else if sheet.disclaimerAccepted {
                    Button("Plan the long way", action: planDrive)
                        .disabled(sheet.start == nil || sheet.destination == nil)
                        .accessibilityIdentifier("plan.go")
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
        endWaitlist()
        sheet.search("", for: field)
    }

    private func act(_ action: PlanFailureAction) {
        switch action {
        case .surpriseMe, .close: onClose()
        case .tryAgain: planDrive()
        case .chooseAnotherPlace: searchFor(.destination)
        case .changeStart: searchFor(.start)
        case .joinWaitlist: joinWaitlist()
        }
    }

    /// T-0360 R2, R3: the failed ticket's start (T-0365 R3: the sheet's waitlistStart), at most one request, the
    /// answer shown in place of the failure.
    private func joinWaitlist() {
        guard !showingWaitlist, let start = sheet.waitlistStart else { return }
        showingWaitlist = true
        waitlistAnswer = nil
        let planner = self.planner
        Task { @MainActor in
            waitlistAnswer = await planner.joinWaitlist(near: start)
        }
    }

    private func endWaitlist() {
        showingWaitlist = false
        waitlistAnswer = nil
    }

    /// The view's whole plan path: the gate's ticket, or nothing; then the planner's outcome for that ticket.
    private func planDrive() {
        guard let ticket = sheet.startPlanning() else { return }
        run(ticket)
    }

    /// A saved drive replayed (T-0306 R3): through the same gate, as one plan, then the same planner path.
    private func replay(_ drive: SavedReplay) {
        showingSaved = false
        guard let ticket = sheet.replay(drive) else { return }
        run(ticket)
    }

    /// Keeps the previewed route on this device (T-0306 R2); nothing is sent anywhere.
    private func save(_ preview: PlanPreview, budgetMinutes: Int) {
        let name = String((sheet.destination?.name ?? "Saved drive").prefix(SavedList.maxNameLength))
        let draft = SavedDraft.of(preview, budgetMinutes: budgetMinutes, name: name,
                                  createdAt: Int64(Date().timeIntervalSince1970))
        let kept = draft.map { SavedDriveShelf.save($0) } ?? false
        saveLine = kept ? "Saved to your drives." : "This drive could not be saved."
    }

    private func run(_ ticket: PlanTicket) {
        saveLine = nil
        endWaitlist()
        let planner = self.planner
        Task { @MainActor in
            let outcome = await planner.plan(ticket)
            sheet.finish(ticket, with: outcome)
        }
    }
}

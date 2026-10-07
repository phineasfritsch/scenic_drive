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
    private let planner: any RoutePlanning
    private let onClose: () -> Void

    /// The home's on-device acknowledgement, read only (R3).
    @AppStorage("safety.disclaimer.acknowledged.v1") private var safetyNoteRead = false
    @State private var sheet = PlanSheet(disclaimerAccepted: false)
    @State private var query = ""

    public init(planner: any RoutePlanning, onClose: @escaping () -> Void) {
        self.planner = planner
        self.onClose = onClose
    }

    public var body: some View {
        NavigationStack {
            content
                .navigationTitle("Plan a drive")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close", action: onClose)
                    }
                }
        }
        .onAppear { sheet.setDisclaimerAccepted(safetyNoteRead) }
        .onChange(of: safetyNoteRead) { _, accepted in sheet.setDisclaimerAccepted(accepted) }
    }

    @ViewBuilder private var content: some View {
        switch sheet.state {
        case .idle, .chosen:
            form
        case .searching(let field, _):
            PlanPlaceList(field: field, query: $query, onPick: { sheet.choose($0) }, onCancel: { sheet.endSearch() })
        case .planning:
            ProgressView("Finding a calmer way there")
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        case .preview(_, let preview):
            PlanPreviewCard(preview: preview, destination: sheet.destination?.name ?? "",
                            onChangePlace: { searchFor(.destination) })
        case .failed(_, let failure):
            PlanFailureCard(copy: PlanFailureCopy.of(failure), onAction: act)
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
                if sheet.disclaimerAccepted {
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
        sheet.search("", for: field)
    }

    private func act(_ action: PlanFailureAction) {
        switch action {
        case .surpriseMe, .close: onClose()
        case .tryAgain: planDrive()
        case .chooseAnotherPlace: searchFor(.destination)
        case .changeStart: searchFor(.start)
        }
    }

    /// The view's whole plan path: the gate's ticket, or nothing; then the planner's outcome for that ticket.
    private func planDrive() {
        guard let ticket = sheet.startPlanning() else { return }
        let planner = self.planner
        Task { @MainActor in
            let outcome = await planner.plan(ticket)
            sheet.finish(ticket, with: outcome)
        }
    }
}

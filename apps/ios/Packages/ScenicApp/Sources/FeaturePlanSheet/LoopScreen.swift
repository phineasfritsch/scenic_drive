import DesignSystem
import ScenicKit
import SwiftUI

/// The loop content of the full-height plan sheet (T-0314 R3-R7): the form (a typed start and the minutes dial), the
/// place search, the planning wait, the preview and a refusal. Every ticket comes from LoopSheet's gate, so nothing is
/// planned before the safety note is read (P-SAFE-03).
struct LoopScreen: View {
    @Binding var loop: LoopSheet
    let planner: any LoopPlanning
    let mapsURL: (Coordinate, [Coordinate]) -> URL?
    /// T-0365 R4: the plan sheet's own joiner - one WaitlistClient, one memory, so an area counts once per install.
    let waitlist: any WaitlistJoining
    @State private var query = ""
    /// T-0365: the waitlist card replaces the failure from the tap; nil answer while the request is out.
    @State private var showingWaitlist = false
    @State private var waitlistAnswer: WaitlistAnswer?

    init(loop: Binding<LoopSheet>, planner: any LoopPlanning, waitlist: any WaitlistJoining,
         mapsURL: @escaping (Coordinate, [Coordinate]) -> URL?) {
        _loop = loop
        self.planner = planner
        self.waitlist = waitlist
        self.mapsURL = mapsURL
    }

    var body: some View {
        switch loop.state {
        case .idle, .chosen:
            form
        case .searching:
            PlanPlaceList(field: .start, query: $query, onPick: { loop.choose($0) }, onCancel: { loop.endSearch() })
        case .planning:
            ProgressView("Finding a loop that does not double back")
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        case .preview(let ticket, let preview):
            LoopPreviewCard(preview: preview, minutes: ticket.minutes, start: loop.start?.name ?? "",
                            link: mapsURL(ticket.start, preview.waypoints), onChange: { loop.edit() })
        case .failed(_, let failure):
            if showingWaitlist {
                WaitlistCard(answer: waitlistAnswer, onChangeStart: changeStart)
            } else {
                VStack(alignment: .leading, spacing: 12) {
                    Text(failure.line)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("loop.failure")
                    if let action = failure.waitlistAction {
                        Button(action.title, action: joinWaitlist)
                            .accessibilityIdentifier("loop.failure.waitlist")
                    }
                    Button("Try again", action: planLoop)
                    Button("Change the loop") { loop.edit() }
                }
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            }
        }
    }

    /// T-0365 R3, R4: the sheet's waitlistStart only, at most one request, the answer shown in place of the failure.
    private func joinWaitlist() {
        guard !showingWaitlist, let start = loop.waitlistStart else { return }
        showingWaitlist = true
        waitlistAnswer = nil
        let waitlist = self.waitlist
        Task { @MainActor in
            waitlistAnswer = await waitlist.joinWaitlist(near: start)
        }
    }

    private func changeStart() {
        showingWaitlist = false
        waitlistAnswer = nil
        query = ""
        loop.search("")
    }

    private var form: some View {
        Form {
            Section("Start") {
                Button(loop.start?.name ?? "Choose a start") {
                    query = ""
                    loop.search("")
                }
                .accessibilityIdentifier("loop.from")
            }
            Section {
                Stepper("About \(loop.minutes) min of driving",
                        value: Binding(get: { loop.minutes }, set: { loop.setMinutes($0) }), in: LoopSheet.minuteRange,
                        step: 5)
            } header: {
                Text("Time")
            } footer: {
                Text("You come back to where you started. One loop a day is free.")
            }
            Section {
                if let notice = loop.degrade.notice(on: .loop) {
                    // T-0364 R3: a pause, an update or loops switched off, heard from /config before the tap.
                    Text(notice)
                        .foregroundStyle(DesignTokens.fg)
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("loop.degrade")
                } else if loop.disclaimerAccepted {
                    Button("Find a loop", action: planLoop)
                        .disabled(loop.start == nil)
                        .accessibilityIdentifier("loop.go")
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
            loop.setDegrade(await planner.degrade())
        }
    }

    private func planLoop() {
        guard let ticket = loop.startPlanning() else { return }
        showingWaitlist = false
        waitlistAnswer = nil
        let planner = self.planner
        Task { @MainActor in
            let outcome = await planner.plan(ticket)
            loop.finish(ticket, with: outcome)
        }
    }
}

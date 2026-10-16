import ScenicKit
import Testing

/// T-0294 acceptance 2, T-0368 acceptance 1: every PlanSheetFailure under each SurpriseGate maps to exactly one copy
/// line and one action (the plan's Degraded states row, R5; T-0368 R4), compared WHOLE against a table typed here - an
/// exhaustive switch, so a fifteenth case does not compile until this file names its row - plus the count and order of
/// the cases themselves, and meta-rows that only the three Surprise rows read the gate.
@Suite("PlanFailureCopyTests")
struct PlanFailureCopyTests {
    /// The three rows that offer Surprise Me while it is on (T-0368 R4); every other row ignores the gate.
    static let gated: Set<PlanSheetFailure> = [.quotaExhausted, .planningPaused, .attestUnsupported]

    static func expected(_ failure: PlanSheetFailure, _ gate: SurpriseGate) -> PlanFailureCopy {
        switch (failure, gate) {
        case (.quotaExhausted, .on):
            return PlanFailureCopy(line: "That's all of today's planned drives. More open up when the daily count resets.",
                                   action: .surpriseMe)
        case (.quotaExhausted, .off):
            return PlanFailureCopy(line: "That's all of today's planned drives. More open up when the daily count resets.",
                                   action: .close)
        case (.planningPaused, .on):
            return PlanFailureCopy(line: "Planning is paused right now. Surprise Me still works.", action: .surpriseMe)
        case (.planningPaused, .off):
            return PlanFailureCopy(line: "Planning is paused right now. Try again in a little while.", action: .close)
        case (.routingOffline, _):
            return PlanFailureCopy(line: "The route planner can't be reached right now. Try again in a little while.",
                                   action: .tryAgain)
        case (.noRoute, _):
            return PlanFailureCopy(line: "Couldn't reach that place by paved road.", action: .chooseAnotherPlace)
        case (.regionUnsupported, _):
            return PlanFailureCopy(line: "Drives can't be planned from that start yet. We can count this area toward "
                                       + "where we go next.", action: .joinWaitlist)
        case (.attestUnsupported, .on):
            return PlanFailureCopy(line: "This phone can't plan drives yet. Surprise Me still works.", action: .surpriseMe)
        case (.attestUnsupported, .off):
            return PlanFailureCopy(line: "This phone can't plan drives yet.", action: .close)
        case (.offlineDuringDrive, _):
            return PlanFailureCopy(line: "You're offline. Keep to the road you're on; the route comes back with signal.",
                                   action: .close)
        case (.noScenicAlternative, _):
            return PlanFailureCopy(line: "The quickest way there is already the scenic one. Try another place.",
                                   action: .chooseAnotherPlace)
        case (.nothingPretty, _):
            return PlanFailureCopy(line: "Not much pretty within reach of this drive. More time might find some.",
                                   action: .chooseAnotherPlace)
        case (.unknownPlace, _):
            return PlanFailureCopy(line: "That place isn't in our list anymore. Choose another one.",
                                   action: .chooseAnotherPlace)
        case (.planRefused, _):
            return PlanFailureCopy(line: "That route didn't pass our own checks, so it isn't shown. Try another place.",
                                   action: .chooseAnotherPlace)
        case (.invalidRequest, _):
            return PlanFailureCopy(line: "That plan didn't go through. Try again.", action: .tryAgain)
        case (.refusedOnDevice, _):
            return PlanFailureCopy(line: "That plan wasn't sent. Check the start and the extra time.",
                                   action: .changeStart)
        case (.unexpectedResponse, _):
            return PlanFailureCopy(line: "Something went wrong on our side. Try again in a moment.", action: .tryAgain)
        }
    }

    @Test("every PlanSheetFailure under each SurpriseGate has its one copy line and one action (28 rows)")
    func everyRowWhole() {
        var rows = 0
        for failure in PlanSheetFailure.allCases {
            for gate in SurpriseGate.allCases {
                #expect(PlanFailureCopy.of(failure, surprise: gate) == Self.expected(failure, gate), "\(failure) \(gate)")
                rows += 1
            }
        }
        #expect(rows == 28)
    }

    @Test("exactly the three Surprise rows read the gate; no off row offers or names Surprise Me")
    func onlySurpriseRowsReadTheGate() {
        for failure in PlanSheetFailure.allCases {
            let on = PlanFailureCopy.of(failure, surprise: .on)
            let off = PlanFailureCopy.of(failure, surprise: .off)
            #expect((on != off) == Self.gated.contains(failure), "\(failure)")
            #expect((on.action == .surpriseMe) == Self.gated.contains(failure), "\(failure)")
            #expect(off.action != .surpriseMe && !off.line.contains("Surprise"), "\(failure): \(off.line)")
        }
        // Meta: the typed table itself differs on exactly those rows, so a row that ignored the gate would show.
        #expect(Set(PlanSheetFailure.allCases.filter { Self.expected($0, .on) != Self.expected($0, .off) }) == Self.gated)
    }

    @Test("the table covers all fourteen PlanError cases, in PlanError's order, 14 distinct lines under each gate")
    func coversEveryCase() {
        #expect(PlanSheetFailure.allCases.map(\.rawValue) == [
            "quotaExhausted", "planningPaused", "routingOffline", "noRoute", "regionUnsupported", "attestUnsupported",
            "offlineDuringDrive", "noScenicAlternative", "nothingPretty", "unknownPlace", "planRefused", "invalidRequest",
            "refusedOnDevice", "unexpectedResponse",
        ])
        for gate in SurpriseGate.allCases {
            #expect(Set(PlanSheetFailure.allCases.map { PlanFailureCopy.of($0, surprise: gate).line }).count == 14, "\(gate)")
        }
    }

    @Test("copy lines are calm: a full sentence, no exclamation mark")
    func calmLines() {
        for failure in PlanSheetFailure.allCases {
            for gate in SurpriseGate.allCases {
                let line = PlanFailureCopy.of(failure, surprise: gate).line
                #expect(!line.isEmpty && line.hasSuffix(".") && !line.contains("!"), "\(failure) \(gate): \(line)")
            }
        }
    }

    @Test("every action has its button words")
    func actionTitles() {
        #expect(PlanFailureAction.allCases.map(\.title) == [
            "Surprise me instead", "Try again", "Choose another place", "Change the start", "Close",
            "Count this area",
        ])
    }
}

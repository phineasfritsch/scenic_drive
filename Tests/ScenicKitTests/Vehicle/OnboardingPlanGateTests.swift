import ScenicKit
import Testing

/// T-0309 acceptance 3 (P-SAFE-03, R5): first launch driven through onboarding event by event. At every prefix the
/// plan sheet is built from what onboarding has recorded and the shipping gate `startPlanning()` is pressed; any ticket
/// goes to a counting planner. Nothing reaches the planner before `accept`; one plan does after it.
@Suite("OnboardingPlanGateTests")
struct OnboardingPlanGateTests {
    actor CountingPlanner: RoutePlanning {
        private(set) var calls = 0
        func plan(_ ticket: PlanTicket) async -> PlanOutcome {
            calls += 1
            return .failure(.routingOffline)
        }
    }

    static let start = PlanPlace(id: 7, name: "Santa Monica Pier",
                                 coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let destination = PlanPlace(id: 42, name: "Topanga Lookout",
                                       coordinate: Coordinate(latitude: 34.09312, longitude: -118.60071))

    /// Every way a first launch can wander before agreeing: refused vehicles, skips, backs and nexts.
    static let script: [OnboardingEvent] = [.choose(.motorcycle), .skip, .back, .choose(.trailer), .next, .skip,
                                            .next, .back, .choose(.rv), .next, .choose(.lowClearance)]

    /// The plan button pressed with everything chosen, the disclaimer flag being whatever onboarding recorded.
    static func press(_ onboarding: Onboarding, _ planner: CountingPlanner) async -> PlanTicket? {
        var sheet = PlanSheet(disclaimerAccepted: onboarding.disclaimerAccepted)
        sheet.search("santa", for: .start)
        sheet.choose(start)
        sheet.search("topanga", for: .destination)
        sheet.choose(destination)
        let ticket = sheet.startPlanning()
        if let ticket { _ = await planner.plan(ticket) }
        return ticket
    }

    @Test("first launch through onboarding: zero plan requests before accept, one after")
    func noPlanBeforeAcceptance() async {
        let planner = CountingPlanner()
        var onboarding = Onboarding()
        #expect(await Self.press(onboarding, planner) == nil)
        for event in Self.script {
            onboarding.send(event)
            #expect(await Self.press(onboarding, planner) == nil, "after \(event)")
        }
        #expect(await planner.calls == 0)
        #expect(onboarding.step == .disclaimer)
        onboarding.send(.accept)
        #expect(onboarding.disclaimerAccepted)
        #expect(await Self.press(onboarding, planner) != nil)
        #expect(await planner.calls == 1)
    }
}

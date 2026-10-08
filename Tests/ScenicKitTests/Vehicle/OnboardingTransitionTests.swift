@testable import ScenicKit
import Testing

/// T-0309 acceptance 2: the onboarding machine (R3) as a full-equality transition table over every (state, event)
/// pair, and the property the safety gate rests on - skipping or backing out never accepts the disclaimer.
@Suite("OnboardingTransitionTests")
struct OnboardingTransitionTests {
    static let atVehicle = Onboarding(step: .vehicle, vehicle: .standard, disclaimerAccepted: false)
    static let atDisclaimer = Onboarding(step: .disclaimer, vehicle: .standard, disclaimerAccepted: false)
    static let done = Onboarding(step: .done, vehicle: .standard, disclaimerAccepted: true)
    static let states = [atVehicle, atDisclaimer, done]
    static let events: [OnboardingEvent] = VehicleProfile.allCases.map { .choose($0) } + [.next, .back, .skip, .accept]
    static let declining: [OnboardingEvent] = events.filter { $0 != .accept }

    struct Row {
        let from: Onboarding
        let event: OnboardingEvent
        let to: Onboarding
    }

    /// Every row is the WHOLE expected value. Only standard can be chosen, so every choose leaves the value as it was.
    static let table: [Row] = [
        Row(from: atVehicle, event: .choose(.standard), to: atVehicle),
        Row(from: atVehicle, event: .choose(.lowClearance), to: atVehicle),
        Row(from: atVehicle, event: .choose(.motorcycle), to: atVehicle),
        Row(from: atVehicle, event: .choose(.trailer), to: atVehicle),
        Row(from: atVehicle, event: .choose(.rv), to: atVehicle),
        Row(from: atVehicle, event: .next, to: atDisclaimer),
        Row(from: atVehicle, event: .back, to: atVehicle),
        Row(from: atVehicle, event: .skip, to: atDisclaimer),
        Row(from: atVehicle, event: .accept, to: atVehicle),
        Row(from: atDisclaimer, event: .choose(.standard), to: atDisclaimer),
        Row(from: atDisclaimer, event: .choose(.lowClearance), to: atDisclaimer),
        Row(from: atDisclaimer, event: .choose(.motorcycle), to: atDisclaimer),
        Row(from: atDisclaimer, event: .choose(.trailer), to: atDisclaimer),
        Row(from: atDisclaimer, event: .choose(.rv), to: atDisclaimer),
        Row(from: atDisclaimer, event: .next, to: atDisclaimer),
        Row(from: atDisclaimer, event: .back, to: atVehicle),
        Row(from: atDisclaimer, event: .skip, to: atDisclaimer),
        Row(from: atDisclaimer, event: .accept, to: done),
        Row(from: done, event: .choose(.standard), to: done),
        Row(from: done, event: .choose(.lowClearance), to: done),
        Row(from: done, event: .choose(.motorcycle), to: done),
        Row(from: done, event: .choose(.trailer), to: done),
        Row(from: done, event: .choose(.rv), to: done),
        Row(from: done, event: .next, to: done),
        Row(from: done, event: .back, to: done),
        Row(from: done, event: .skip, to: done),
        Row(from: done, event: .accept, to: done),
    ]

    @Test("the table has exactly one row for every (state, event) pair")
    func tableIsTheCrossProduct() {
        #expect(Self.table.count == Self.states.count * Self.events.count)
        for from in Self.states {
            for event in Self.events {
                #expect(Self.table.filter { $0.from == from && $0.event == event }.count == 1)
            }
        }
    }

    @Test("transition table: send(event) from each state equals the row's whole expected value")
    func transitionTable() {
        for row in Self.table {
            var onboarding = row.from
            onboarding.send(row.event)
            #expect(onboarding == row.to, "\(row.from.step) + \(row.event)")
        }
    }

    @Test("first launch is the vehicle step with a standard car and nothing accepted")
    func firstLaunch() {
        #expect(Onboarding() == Self.atVehicle)
    }

    @Test("skipping or backing out never marks the disclaimer accepted")
    func decliningNeverAccepts() {
        var frontier = [Onboarding()]
        for _ in 0..<4 {
            var reached: [Onboarding] = []
            for state in frontier {
                for event in Self.declining {
                    var next = state
                    next.send(event)
                    #expect(next.disclaimerAccepted == false, "\(state.step) + \(event)")
                    #expect(next.step != .done, "\(state.step) + \(event)")
                    if !reached.contains(next) { reached.append(next) }
                }
            }
            frontier = reached
        }
        #expect(frontier.contains(Self.atVehicle) && frontier.contains(Self.atDisclaimer))
    }

    @Test("accept marks the disclaimer accepted only from the disclaimer step")
    func acceptOnlyFromDisclaimer() {
        var first = Onboarding()
        first.send(.accept)
        #expect(first == Self.atVehicle)
        first.send(.skip)
        first.send(.accept)
        #expect(first == Self.done)
    }
}

@testable import ScenicKit
import Testing

/// T-0365 R3: the plan sheet's one binding for "Count this area" - the failed ticket's 2-dp origin exactly when the
/// failure's action is .joinWaitlist, nil for every other failure and every other state.
@Suite("PlanWaitlistStartTests")
struct PlanWaitlistStartTests {
    static let pier = PlanPlace(id: 7, name: "Santa Monica Pier",
                                coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let ojai = PlanPlace(id: 9, name: "Ojai", coordinate: Coordinate(latitude: 34.448, longitude: -119.243))
    static let zuma = PlanPlace(id: 42, name: "Zuma", coordinate: Coordinate(latitude: 34.015, longitude: -118.822))
    static let preview = PlanPreview(route: [Coordinate(latitude: 34.01, longitude: -118.5)], etaSeconds: 3120,
                                     fastestEtaSeconds: 2700, etaIsEstimate: true, hazards: [])

    /// A sheet with `place` as its start and Zuma as its destination, its plan answered with `outcome` (nil: none).
    static func sheet(from place: PlanPlace, _ outcome: PlanOutcome?) -> PlanSheet {
        var sheet = PlanSheet(disclaimerAccepted: true)
        sheet.search("q", for: .start)
        sheet.choose(place)
        sheet.search("z", for: .destination)
        sheet.choose(zuma)
        guard let outcome, let ticket = sheet.startPlanning() else { return sheet }
        sheet.finish(ticket, with: outcome)
        return sheet
    }

    @Test("the waitlist start is the failed ticket's 2-dp origin only on regionUnsupported")
    func waitlistStartTable() {
        let starts: [(PlanPlace, Coordinate)] = [(Self.pier, Coordinate(latitude: 34.01, longitude: -118.5)),
                                                 (Self.ojai, Coordinate(latitude: 34.45, longitude: -119.24))]
        for (place, at2dp) in starts {
            for failure in PlanSheetFailure.allCases {
                let expected: Coordinate? = failure == .regionUnsupported ? at2dp : nil
                #expect(Self.sheet(from: place, .failure(failure)).waitlistStart == expected, "\(failure) \(place.name)")
            }
            #expect(Self.sheet(from: place, nil).waitlistStart == nil, "chosen \(place.name)")
            #expect(Self.sheet(from: place, .preview(Self.preview)).waitlistStart == nil, "preview \(place.name)")
        }
        #expect(Self.sheet(from: Self.pier, .failure(.regionUnsupported)).waitlistStart
            != Self.sheet(from: Self.ojai, .failure(.regionUnsupported)).waitlistStart)
        #expect(PlanSheet(disclaimerAccepted: true).waitlistStart == nil)
    }
}

import Foundation
import Testing
@testable import ScenicKit

/// T-0343 R4: the planner's answer carries the device's learned speeds - retimed at the planner's `now`, the moment
/// the answer arrives - and only a preview with runs is touched. Outcomes compared WHOLE, written out per row.
@Suite("the plan answer is retimed by the device's learner at answer time (T-0343)") struct RetimingPlannerTests {
    static let server = CorridorLearnerTests.server
    static let departs = RetimedPreviewTests.departs

    static func expected(eta: Double, estimate: Bool) -> PlanPreview {
        PlanPreview(route: server.route, etaSeconds: eta, fastestEtaSeconds: 250, etaIsEstimate: estimate,
                    hazards: server.hazards, lambda: 1.5, continuation: server.continuation, timeRuns: server.timeRuns)
    }

    @Test("previews with runs are retimed at now(); a preview without runs, a failure and an offer pass unchanged")
    @MainActor
    func outcomeTable() async {
        let noRuns = PlanPreview(route: Self.server.route, etaSeconds: 333, fastestEtaSeconds: 250, etaIsEstimate: true,
                                 hazards: Self.server.hazards)
        let untiled = PlanPreview(route: Self.server.route, etaSeconds: 333, fastestEtaSeconds: 250,
                                  etaIsEstimate: true, hazards: [],
                                  timeRuns: [CorridorTimeRun(from: 0, to: 3, milliseconds: 1000)])
        let offer = PlanOffer(budgetMinutes: 30, moreTimeMinutes: 45, backRoadsEtaSeconds: 2400,
                              backRoadsBudgetMinutes: 40)
        let learned = RetimedPreviewTests.learner(samples: 5, oneShort: false)
        let empty = LearnedCorridorSpeeds(timeZone: RetimedPreviewTests.utc)
        let dayLater = Self.departs.addingTimeInterval(86_400)
        // (name, the inner answer, the learner, now, the answer expected)
        let rows: [(String, PlanOutcome, LearnedCorridorSpeeds, Date, PlanOutcome)] = [
            ("runs, nothing learned", .preview(Self.server), empty, Self.departs,
             .preview(Self.expected(eta: 310, estimate: true))),
            ("runs, every edge learned at now", .preview(Self.server), learned, Self.departs,
             .preview(Self.expected(eta: 620, estimate: false))),
            ("runs, learned for another day than now", .preview(Self.server), learned, dayLater,
             .preview(Self.expected(eta: 310, estimate: true))),
            ("no runs", .preview(noRuns), learned, Self.departs, .preview(noRuns)),
            ("runs that do not tile", .preview(untiled), learned, Self.departs, .preview(untiled)),
            ("a failure", .failure(.noRoute), learned, Self.departs, .failure(.noRoute)),
            ("an offer", .offered(offer), learned, Self.departs, .offered(offer)),
        ]
        for (name, inner, speeds, now, expected) in rows {
            let planner = RetimingPlanner(inner: CorridorLearnerTests.Fixed(outcome: inner),
                                          learner: CorridorLearner(speeds: speeds, save: { _ in }), now: { now })
            #expect(await planner.plan(CorridorLearnerTests.ticket) == expected, "\(name)")
        }
    }
}

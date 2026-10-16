import Foundation
import Testing
@testable import ScenicKit

/// T-0230 rv1 B1/B2: the two bounds the honest-failure suite left open, both through `ScenicPlanner.plan` - the
/// symbol `PlanCommand.run`, and so `ops/plan`, calls - and the `lines()` ops/plan prints after `REFUSED: `.
/// Every expected value is typed here against literals (0.45, 2700 s, the minute spellings), never read back from
/// the constants or the formatters under test.
@Suite("T-0230 rv1: the back-roads offer's floor and the refusal's minute spelling, at every bound")
struct PlanNothingPrettyBoundsTests {

    typealias Honest = ScenicPlannerHonestFailureTests

    static let floor = 0.45
    static let unmeasuredLine = "NO-OFFER all-back-roads: lambda 8 was not measured (no recorded response at lambda 8.0)"

    // MARK: - B1: the back-roads offer's own floor

    @Test("all back roads at lambda 8: nextDown(0.45) is dull, exactly 0.45 and nextUp(0.45) are offered")
    func backRoadsOfferIsStrictAtEveryBound() throws {
        let rows = Honest.floorRows()
        let chosenScore = try #require(Honest.score(Honest.dull))
        try #require(chosenScore < Self.floor, "the dull fixture itself moved: \(chosenScore)")
        for target in [Self.floor.nextDown, Self.floor, Self.floor.nextUp] {
            let eight = try #require(rows[target], "no geometry lands on \(target)")
            let router = Honest.Router(chosen: Honest.dull)
            router.scenicPaths[LambdaCustomModel.multiplier(8)] = eight
            let offered = target >= Self.floor
            let expected: PlanNothingPretty.BackRoads = offered
                ? .offered(duration: 2700, routeScore: target) : .dull(duration: 2700, routeScore: target)
            let state = try #require(try Honest.refusal(router), "at \(target)")
            #expect(state == PlanNothingPretty(budget: 1500, fastestDuration: 1800, routeScore: chosenScore,
                                               backRoads: expected), "at \(target)")
            #expect(router.requested == [4, 8], "at \(target)")
            #expect(state.lines().last == (offered
                ? "OFFER all-back-roads: lambda 8, measured ETA 45m00s, RouteScore 0.450"
                : "NO-OFFER all-back-roads: lambda 8, measured ETA 45m00s, RouteScore 0.450 is under the floor too"),
                    "at \(target)")
        }
    }

    // MARK: - B2: the budget's spelling, whole minutes and not

    /// (budget seconds, its spelling, the spelling of budget + 40 minutes), typed here: 0, 59, 60, 61 and 90 s
    /// are the bounds of `minutes`' whole-minute test and its singular; 1500 s is the suite's ordinary budget.
    static let budgetRows: [(budget: TimeInterval, asked: String, more: String)] = [
        (0, "0 minutes", "40 minutes"),
        (59, "0m59s", "40m59s"),
        (60, "1 minute", "41 minutes"),
        (61, "1m01s", "41m01s"),
        (90, "1m30s", "41m30s"),
        (1500, "25 minutes", "65 minutes"),
    ]

    @Test("ops/plan's refusal lines through ScenicPlanner.plan, whole, at budgets 0, 59, 60, 61, 90 and 1500 s")
    func refusalLinesSpellEveryBudgetBound() throws {
        // Unscored, inside every ceiling here (1800 s <= 1800 + 0) and on other ways than the fastest route.
        let chosen = Honest.path(ms: 1_800_000, legs: [(nil, 0.01), (nil, 0.01)])
        for row in Self.budgetRows {
            let router = Honest.Router(chosen: chosen)
            var refused: PlanNothingPretty?
            do {
                _ = try Honest.plan(router, budget: row.budget)
            } catch PlanFailure.nothingPretty(let state) {
                refused = state
            }
            let state = try #require(refused, "budget \(row.budget) was not refused as nothingPretty")
            #expect(state == PlanNothingPretty(budget: row.budget, fastestDuration: 1800, routeScore: nil,
                                               backRoads: .unmeasured(Honest.unrecordedEight)), "budget \(row.budget)")
            #expect(state.lines() == [
                "not much pretty within \(row.asked) of this drive: the route carries no scored road",
                "OFFER more-time: plan again with \(row.more) of extra time (+40 minutes)",
                Self.unmeasuredLine,
            ], "budget \(row.budget)")
        }
    }
}

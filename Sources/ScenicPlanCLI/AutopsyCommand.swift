import Foundation
import ScenicKit

/// What `ops/route-autopsy` DOES (T-0327): re-plan with the shipping planner, then print every edge's GATE,
/// M, E and score, the lambda trace and the RouteScore terms - or write the plan as a pinned negative fixture.
///
/// The router is chosen HERE from `--recorded`/`--router`, as `PlanCommand.run` does and for its reason: which
/// graph the autopsy planned against is part of what a run of it is. The planner is `ScenicPlanner` with the
/// production `LambdaSearch`, wrapped only by `TracingRouteSource`, which forwards every call unchanged - so
/// the plan autopsied is the plan `ops/plan` prints for the same arguments, refusals included (exit 3).
public enum AutopsyCommand {

    public static func run(_ arguments: AutopsyArguments) throws -> [String] {
        let source: RouteSource
        switch arguments.plan.router {
        case let .http(url):
            source = GraphHopperRouteSource(baseURL: url)
        case let .recorded(directory):
            source = RecordedRouteSource(directory: directory)
        }
        // Read before any request: a malformed terms file is the operator's to fix, and finding out after a
        // live router has been asked six times is the expensive order.
        let terms = try arguments.terms.map(AutopsyTerms.load)

        let tracer = TracingRouteSource(source)
        let planner = ScenicPlanner(source: tracer, maxEvaluations: arguments.plan.maxEvaluations)
        let plan = try planner.plan(from: arguments.plan.origin, to: arguments.plan.destination,
                                    budget: arguments.plan.budget)

        if let directory = arguments.fixture {
            return try AutopsyFixture.write(arguments, plan: plan, steps: tracer.steps, into: directory)
        }
        return ["ROUTER \(source.describedSource)"]
            + AutopsyReport(plan: plan, steps: tracer.steps, terms: terms).lines()
    }
}

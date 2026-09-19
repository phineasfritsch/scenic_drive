import Foundation
import Handoff
import ScenicKit

/// What `ops/plan <O> <D> <B>` DOES, once the arguments are understood: the lines the terminal shows, or
/// a thrown refusal.
///
/// ## Why this is not in main.swift
///
/// main.swift is top-level code. A run of it is a run of the PROCESS, so nothing can bind a test to the
/// path `ops/plan` actually takes - and T-0182's own pre-review pass found the consequence: the CLI's one
/// unit conversion (minutes -> seconds) could be changed to `* 3600` and the whole suite stayed green
/// while the tool shipped a 25-HOUR ceiling and printed `budget=25h00m00s`. The invariant CLAUDE.md states
/// - *returned ETA <= fastest + budget, always* - is over the budget the USER stated, and this is the only
/// code that turns what they typed into the seconds the ceiling is computed from.
///
/// So everything between parsing and printing lives here, `main.swift` is the four lines that call it and
/// map a failure to an exit code, and the test named for that defect drives THIS function with the
/// arguments `ops/plan` was given (CLAUDE.md: *a test named for a defect binds to the shipping symbol -
/// the entry point production runs*).
public enum PlanCommand {

    /// Route, plan, render. The `RouteSource` is chosen HERE from `--router`/`--recorded` rather than
    /// passed in, because which graph the tool planned against is part of what a run of it is: a caller
    /// that could hand in its own source would be exercising a different tool from the one shipped.
    public static func run(_ arguments: PlanArguments) throws -> [String] {
        let source: RouteSource
        switch arguments.router {
        case let .http(url):
            source = GraphHopperRouteSource(baseURL: url)
        case let .recorded(directory):
            source = RecordedRouteSource(directory: directory)
        }

        let planner = ScenicPlanner(source: source, maxEvaluations: arguments.maxEvaluations)
        let plan = try planner.plan(from: arguments.origin, to: arguments.destination,
                                    budget: arguments.budget)
        let url = try AppleMapsDirections(source: plan.origin, destination: plan.destination,
                                          waypoints: plan.waypoints).url()
        // Built whole and returned, not printed as it goes: a run that refuses at the URL after printing
        // half a plan is a terminal showing a plan that was never issued.
        return ["ROUTER \(source.describedSource)"] + plan.report() + ["URL \(url.absoluteString)"]
    }
}

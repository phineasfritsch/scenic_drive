import Foundation
import ScenicKit

/// `ops/route-autopsy <O> <D> <B> (--recorded <dir> | --router <url>) [--terms <file>] [--fixture <dir>]`,
/// parsed.
///
/// A "plan" here is exactly what `ops/plan` takes, re-planned by the shipping `ScenicPlanner` (T-0327 R1):
/// the server keeps no plans - a plan_token holds pins and a lambda for twelve hours and no edges - so the
/// only honest way to look at a bad drive's edges again is to plan it again against the graph it was planned
/// on. The two flags of its own are split off here and everything else is `PlanArguments.parse`, so the
/// two tools cannot disagree about what an origin, a budget or a router is.
public struct AutopsyArguments {

    public static let usage = "usage: ops/route-autopsy <origin lat,lon> <destination lat,lon> <extra-minutes> "
        + "(--recorded <dir> | --router <url>) [--terms <ways.json>] [--fixture <Tests/Fixtures/negative/name>] "
        + "[--max-evaluations N]"

    public let plan: PlanArguments
    /// The per-way tags and terms file (T-0327 R2), or nil: every GATE/M/E cell then prints `-`.
    public let terms: URL?
    /// Where to write the plan as a pinned negative fixture (T-0327 R6), or nil.
    public let fixture: URL?

    public init(plan: PlanArguments, terms: URL?, fixture: URL?) {
        self.plan = plan
        self.terms = terms
        self.fixture = fixture
    }

    public static func parse(_ arguments: [String]) throws -> AutopsyArguments {
        var rest: [String] = []
        var terms: URL?
        var fixture: URL?
        var index = 0
        while index < arguments.count {
            switch arguments[index] {
            case "--terms":
                guard let value = arguments.dropFirst(index + 1).first else {
                    throw PlanArguments.Failure.usage("--terms needs a per-way tags and terms file")
                }
                terms = URL(fileURLWithPath: value)
                index += 2
            case "--fixture":
                guard let value = arguments.dropFirst(index + 1).first else {
                    throw PlanArguments.Failure.usage("--fixture needs the directory to write the fixture into")
                }
                fixture = URL(fileURLWithPath: value)
                index += 2
            default:
                rest.append(arguments[index])
                index += 1
            }
        }
        let plan = try PlanArguments.parse(rest)
        if fixture != nil, case .http = plan.router {
            throw PlanArguments.Failure.usage("--fixture needs --recorded: a live router's responses are not on "
                + "disk, so there is nothing to pin")
        }
        return AutopsyArguments(plan: plan, terms: terms, fixture: fixture)
    }
}

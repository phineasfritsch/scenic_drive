import Foundation
import ScenicKit

/// `ops/plan --menu <O> <D> [--max N] --recorded <dir>`, parsed (T-0239 R4, R10).
///
/// `--max` LOWERS the menu's cap and is refused above `RouteMenu.capMinutes` rather than clamped: a person
/// who typed 60 and was silently shown a 45-minute menu has been told something false about what exists.
/// `--router` is refused by name: there is no served graph yet (T-0209/T-0221) and this task builds no live
/// alternative_route request, so a menu is a replay of a recording or it is nothing.
public struct MenuArguments {

    public static let usage = "usage: ops/plan --menu <origin lat,lon> <destination lat,lon> "
        + "[--max <minutes, at most 45>] --recorded <dir>"

    public let origin: Coordinate
    public let destination: Coordinate
    public let maxMinutes: Double
    public let recorded: URL

    /// The arguments AFTER `--menu`.
    public static func parse(_ arguments: [String]) throws -> MenuArguments {
        var positional: [String] = []
        var recorded: URL?
        var maxMinutes = RouteMenu.capMinutes
        var index = 0
        while index < arguments.count {
            let argument = arguments[index]
            switch argument {
            case "--recorded":
                guard let value = arguments.dropFirst(index + 1).first else {
                    throw PlanArguments.Failure.usage("--recorded needs a directory the recorder wrote with "
                        + "--alternatives on")
                }
                recorded = URL(fileURLWithPath: value)
                index += 2
            case "--max":
                guard let value = arguments.dropFirst(index + 1).first, let minutes = Double(value),
                      minutes.isFinite, minutes > 0 else {
                    throw PlanArguments.Failure.usage("--max needs a positive number of minutes")
                }
                guard minutes <= RouteMenu.capMinutes else {
                    throw PlanArguments.Failure.usage("--max \(value) is above the menu's cap of "
                        + "\(ScenicPlan.fixed(RouteMenu.capMinutes, 0)) minutes; it lowers the cap, never "
                        + "raises it")
                }
                maxMinutes = minutes
                index += 2
            case "--router":
                throw PlanArguments.Failure.usage("--menu replays a recording (--recorded <dir>); no served "
                    + "graph exists yet (T-0209/T-0221), so a live menu is refused rather than guessed")
            default:
                if argument.hasPrefix("--") { throw PlanArguments.Failure.usage("unknown option \(argument)") }
                positional.append(argument)
                index += 1
            }
        }
        guard positional.count == 2 else {
            throw PlanArguments.Failure.usage("expected 2 positional arguments after --menu, got "
                + "\(positional.count)")
        }
        guard let recorded else {
            throw PlanArguments.Failure.usage("--recorded <dir> is required: the menu never guesses which "
                + "graph it is reading")
        }
        return MenuArguments(
            origin: try PlanArguments.coordinate(positional[0], "origin"),
            destination: try PlanArguments.coordinate(positional[1], "destination"),
            maxMinutes: maxMinutes,
            recorded: recorded
        )
    }
}

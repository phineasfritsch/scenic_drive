import Foundation
import ScenicKit

/// `ops/plan <O> <D> <B>`, parsed.
///
/// Three positional arguments in the order the plan writes them, and one required router choice, because a
/// planner with a default router is a tool that quietly plans against the wrong graph when a flag is
/// mistyped. Everything is refused by name with the usage line: this runs in a terminal, and the fastest
/// path to a correct second attempt is being told exactly which argument was wrong.
public struct PlanArguments {

    public enum Router {
        /// A live GraphHopper `/route` endpoint.
        case http(URL)
        /// A directory of responses recorded off a real graph (see `RecordedRouteSource`).
        case recorded(URL)
    }

    public enum Failure: Error, CustomStringConvertible {
        case usage(String)

        public var description: String {
            switch self {
            case let .usage(what): return what
            }
        }
    }

    public static let usage = "usage: ops/plan <origin lat,lon> <destination lat,lon> <extra-minutes> "
        + "(--router <url> | --recorded <dir>) [--max-evaluations N]"

    public let origin: Coordinate
    public let destination: Coordinate
    public let budgetMinutes: Double
    public let router: Router
    public let maxEvaluations: Int

    /// Seconds of extra time. The CLI takes MINUTES because that is the unit the product speaks in
    /// ("I have 25 extra minutes"); everything below this line is seconds.
    public var budget: TimeInterval { budgetMinutes * 60 }

    public static func parse(_ arguments: [String]) throws -> PlanArguments {
        var positional: [String] = []
        var router: Router?
        var maxEvaluations = 6
        var index = 0
        while index < arguments.count {
            let argument = arguments[index]
            switch argument {
            case "--router":
                guard let value = arguments.dropFirst(index + 1).first, let url = URL(string: value) else {
                    throw Failure.usage("--router needs a base URL, e.g. http://127.0.0.1:8989")
                }
                router = .http(url)
                index += 2
            case "--recorded":
                guard let value = arguments.dropFirst(index + 1).first else {
                    throw Failure.usage("--recorded needs a directory of recorded responses")
                }
                router = .recorded(URL(fileURLWithPath: value))
                index += 2
            case "--max-evaluations":
                guard let value = arguments.dropFirst(index + 1).first, let count = Int(value), count > 0
                else {
                    throw Failure.usage("--max-evaluations needs a positive whole number")
                }
                maxEvaluations = count
                index += 2
            default:
                if argument.hasPrefix("--") { throw Failure.usage("unknown option \(argument)") }
                positional.append(argument)
                index += 1
            }
        }

        guard positional.count == 3 else {
            throw Failure.usage("expected 3 positional arguments, got \(positional.count)")
        }
        guard let minutes = Double(positional[2]), minutes.isFinite, minutes >= 0 else {
            throw Failure.usage("the extra-time budget is a non-negative number of minutes, "
                + "not \(positional[2])")
        }
        guard let router else {
            throw Failure.usage("one of --router <url> or --recorded <dir> is required: this tool never "
                + "guesses which graph it is planning against")
        }
        return PlanArguments(
            origin: try coordinate(positional[0], "origin"),
            destination: try coordinate(positional[1], "destination"),
            budgetMinutes: minutes,
            router: router,
            maxEvaluations: maxEvaluations
        )
    }

    /// `lat,lon`, in that order, which is the order every label in this app uses and the reverse of
    /// GeoJSON's. Full precision is kept: this CLI runs on the owner's own box and talks to the router
    /// directly, so P-PRIV-05's two-decimal rule - what OUR SERVER may receive - does not govern it.
    static func coordinate(_ text: String, _ role: String) throws -> Coordinate {
        let parts = text.split(separator: ",", omittingEmptySubsequences: false)
        guard parts.count == 2, let latitude = Double(parts[0]), let longitude = Double(parts[1]),
              latitude >= -90, latitude <= 90, longitude >= -180, longitude <= 180 else {
            throw Failure.usage("the \(role) is a lat,lon pair like 34.0392,-118.5836, not \(text)")
        }
        return Coordinate(latitude: latitude, longitude: longitude)
    }
}

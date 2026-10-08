import Foundation
import ScenicKit

/// A `RouteSource` that remembers every scenic request the bisection made, in order - the lambda trace
/// `ops/route-autopsy` prints (T-0327 R4).
///
/// `LambdaSearch` keeps its samples in a local and returns only the winner, and the plan's playbook wants
/// every step. Rather than widen ScenicKit's budget type for a debugging tool, the trace is taken where
/// the steps are actually paid for: each `scenic(lambda:)` call is one evaluation, `ScenicPlanner` makes
/// exactly one per evaluation, and the duration recorded is the one the router returned for it.
final class TracingRouteSource: RouteSource {

    struct Step: Equatable {
        let lambda: Double
        let duration: TimeInterval
    }

    let inner: RouteSource
    private(set) var steps: [Step] = []

    init(_ inner: RouteSource) {
        self.inner = inner
    }

    var describedSource: String { inner.describedSource }

    func fastest(from origin: Coordinate, to destination: Coordinate) throws -> RoutePath {
        try inner.fastest(from: origin, to: destination)
    }

    func scenic(from origin: Coordinate, to destination: Coordinate, lambda: Double) throws -> RoutePath {
        let path = try inner.scenic(from: origin, to: destination, lambda: lambda)
        steps.append(Step(lambda: lambda, duration: path.duration))
        return path
    }
}

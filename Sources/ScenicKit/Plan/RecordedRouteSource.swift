import Foundation

/// A `RouteSource` that answers from responses recorded off a real graph.
///
/// It exists because the graph this engine is aimed at - T-0213's canyon window - has no HTTP surface yet
/// (that is T-0209's half), so the only way to drive the CLI end to end over REAL routing numbers is to
/// record real responses and replay them. It is not a fake: every byte it returns was computed by
/// GraphHopper 11.0 over the built graph, and the fixture header records the image, the graph and the
/// request that produced it.
///
/// ## Why it refuses instead of interpolating
///
/// A replay that answered an unrecorded lambda with the nearest recorded one would turn a fixture into a
/// stub: the bisection would appear to explore a curve nobody measured, and the duration it reported would
/// be a number no router ever returned for that lambda - which is precisely what `BudgetOutcome` promises
/// never happens. So a missing lambda is `PlanFailure.noRecordedResponse` and the run stops.
public struct RecordedRouteSource: RouteSource {

    /// The file a lambda's response lives in: `lambda-0.json`, `lambda-7.75.json`. The number is formatted
    /// by `LambdaCustomModel.multiplier`, which is the same six-decimal, trailing-zero-trimmed spelling the
    /// custom model's own multipliers use, so a lambda has one spelling across the whole tool.
    public static func fileName(forLambda lambda: Double) -> String {
        "lambda-\(LambdaCustomModel.multiplier(lambda)).json"
    }

    public static let fastestFileName = "fastest.json"

    public let directory: URL

    public init(directory: URL) {
        self.directory = directory
    }

    public var describedSource: String {
        "recorded \(directory.lastPathComponent)"
    }

    public func fastest(from origin: Coordinate, to destination: Coordinate) throws -> RoutePath {
        try path(Self.fastestFileName, lambda: nil)
    }

    public func scenic(from origin: Coordinate, to destination: Coordinate,
                       lambda: Double) throws -> RoutePath {
        try path(Self.fileName(forLambda: lambda), lambda: lambda)
    }

    func path(_ name: String, lambda: Double?) throws -> RoutePath {
        let url = directory.appendingPathComponent(name)
        guard let data = FileManager.default.contents(atPath: url.path) else {
            throw lambda.map(PlanFailure.noRecordedResponse)
                ?? PlanFailure.malformedResponse("no recording at \(url.path)")
        }
        return try RoutePath.decode(data)
    }
}

import Foundation

/// The menu's population, replayed from a directory the committed recorder wrote with `--alternatives on`
/// (Tests/Fixtures/t0182-recorder/Recorder.java; T-0239 rulings R1, R7).
///
/// The layout is the recorder's: `fastest.json` (car_fast's best path - the reference the menu's extra
/// minutes are measured from), `alternatives-fastest.json` (car_fast under alternative_route) and one
/// `alternatives-lambda-<L>.json` per ladder rung (car_scenic under that lambda's model). Each alternatives
/// file carries EVERY path the router returned in `paths[]`, which is GraphHopper's documented shape for
/// alternatives.
///
/// Like `RecordedRouteSource`, it refuses rather than interpolates: a rung with no recording is
/// `PlanFailure.noRecordedResponse`, because a menu built from a ladder nobody recorded is a menu of routes
/// no router ever returned.
public enum RecordedAlternatives {

    public static let fastestFileName = RecordedRouteSource.fastestFileName
    public static let fastestAlternativesFileName = "alternatives-fastest.json"

    /// `alternatives-lambda-2.json`: the lambda spelled by `LambdaCustomModel.multiplier`, the one spelling
    /// the model, the plain recordings and this file share.
    public static func fileName(forLambda lambda: Double) -> String {
        "alternatives-lambda-\(LambdaCustomModel.multiplier(lambda)).json"
    }

    /// The reference path, and every recorded alternative in ladder order (car_fast's first).
    public static func load(directory: URL, ladder: [Double]) throws
        -> (fastest: RoutePath, candidates: [RoutePath]) {
        let fastest = try RoutePath.decode(try contents(directory, fastestFileName, lambda: nil))
        var candidates = try decodeAll(try contents(directory, fastestAlternativesFileName, lambda: nil))
        for lambda in ladder {
            candidates += try decodeAll(try contents(directory, fileName(forLambda: lambda), lambda: lambda))
        }
        return (fastest, candidates)
    }

    /// Every entry of `paths[]`, each decoded by `RoutePath.decode` itself - re-wrapped as a one-path body -
    /// so the response format stays known in exactly one place.
    public static func decodeAll(_ data: Data) throws -> [RoutePath] {
        guard let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let paths = root["paths"] as? [[String: Any]], !paths.isEmpty else {
            return [try RoutePath.decode(data)]
        }
        return try paths.map { path in
            try RoutePath.decode(try JSONSerialization.data(withJSONObject: ["paths": [path]]))
        }
    }

    static func contents(_ directory: URL, _ name: String, lambda: Double?) throws -> Data {
        let url = directory.appendingPathComponent(name)
        guard let data = FileManager.default.contents(atPath: url.path) else {
            throw lambda.map(PlanFailure.noRecordedResponse)
                ?? PlanFailure.malformedResponse("no recording at \(url.path)")
        }
        return data
    }
}

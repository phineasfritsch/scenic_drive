import Foundation

/// The per-request GraphHopper custom model at a given lambda - the SAME model the Worker's
/// `buildCustomModel` (services/api/src/customModel.ts) emits for `closures = null`.
///
/// ## Why this is a port and not a call
///
/// The CLI has to run where GraphHopper runs and must not need a second runtime to ask for a route, so it
/// does not shell to node. A port of an arithmetic function is safe only if something holds the two copies
/// together, so the parity is a GOLDEN: the bytes node prints from customModel.ts are committed under
/// Tests/Fixtures/custom-model/ and a test asserts this type reproduces them exactly at several lambdas.
/// A drift in either direction fails that test by name.
///
/// ## What is deliberately absent
///
/// The safety gates - `road_access == PRIVATE || NO`, the unpaved `surface` list, `road_class == TRACK` -
/// live in car_scenic_base.json on the server and are NOT restated here, for the reason customModel.ts
/// gives: a per-request model that mentioned them could relax them. The emitted text therefore names
/// neither `road_access` nor `surface`, which is an assertable property of the output and is asserted.
///
/// Closures (`areas`) are the Worker's to add from its KV feed; this CLI sends none and says so by not
/// having a parameter for them, rather than by passing an empty collection that looks like a feed.
public enum LambdaCustomModel {

    /// Decimals kept when a multiplier is serialised, from customModel.ts's `MULTIPLIER_DECIMALS`.
    public static let multiplierDecimals = 6

    /// The three `scenic_score` bands of plan :105-107.
    ///
    /// lambda = 0 leaves every band at 1, which is what makes lambda = 0 the fastest route and the
    /// bisection's lower bracket. Rising lambda only ever pushes a band down - and only the LOW and MID
    /// bands, so a high-scoring road is never penalised at any lambda.
    public static func bands(_ lambda: Double) throws -> (high: Double, mid: Double, low: Double) {
        guard lambda.isFinite, lambda >= 0, lambda <= LambdaSearch.maxLambda else {
            throw PlanFailure.lambdaOutOfRange(lambda)
        }
        return (1, 1 / (1 + 0.5 * lambda), 1 / (1 + lambda))
    }

    /// `Number(value.toFixed(6)).toString()`, the JavaScript expression this must reproduce, done with
    /// integer arithmetic so no locale is consulted and no formatter is trusted.
    ///
    /// Trailing zeros are dropped, so 1 stays `"1"` and 0.2 stays `"0.2"` - GraphHopper wants
    /// `multiply_by` as a STRING, and `"1.000000"` is a different byte sequence from the Worker's for the
    /// same number, which is exactly what the parity golden would then fail on.
    ///
    /// Total for every finite value whose magnitude fits an Int after scaling, which every band multiplier
    /// does: they are in (0, 1].
    public static func multiplier(_ value: Double) -> String {
        let scale = (0..<multiplierDecimals).reduce(1) { acc, _ in acc * 10 }
        let scaled = (value * Double(scale)).rounded()
        let sign = scaled < 0 ? "-" : ""
        let magnitude = Int(abs(scaled))
        var digits = String(magnitude % scale)
        while digits.count < multiplierDecimals { digits = "0" + digits }
        while digits.hasSuffix("0") { digits.removeLast() }
        let whole = String(magnitude / scale)
        return digits.isEmpty ? sign + whole : sign + whole + "." + digits
    }

    /// The model as JSON text, byte-for-byte what `JSON.stringify(buildCustomModel(lambda, null), null, 2)`
    /// prints on the Worker.
    ///
    /// Written out rather than built through `JSONSerialization` because the golden is about BYTES: key
    /// order inside a clause (`if` before `multiply_by`) is JavaScript's insertion order and is not a
    /// property `JSONSerialization` will promise, and a dictionary that serialises its keys in another
    /// order is the same model and a different fixture.
    public static func json(for lambda: Double) throws -> String {
        let band = try bands(lambda)
        return """
        {
          "priority": [
            {
              "if": "scenic_score >= 7",
              "multiply_by": "\(multiplier(band.high))"
            },
            {
              "else_if": "scenic_score >= 4",
              "multiply_by": "\(multiplier(band.mid))"
            },
            {
              "else": "",
              "multiply_by": "\(multiplier(band.low))"
            },
            {
              "if": "road_class == RESIDENTIAL && scenic_score < 7",
              "multiply_by": "0.5"
            }
          ]
        }
        """
    }
}

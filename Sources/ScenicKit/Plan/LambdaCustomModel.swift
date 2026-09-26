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

    /// plan :105's high band: a road scored at or above this is never penalised, at any lambda.
    public static let highBand = 7

    /// T-0244 (a): a residential / living_street / service edge scored below `highBand` - a rat-run
    /// candidate - costs 1 + minorSlope x lambda, against 1 + lambda for the dullest (score 0) arterial. The
    /// clause is the FIRST branch of the band chain, so it replaces the band rather than multiplying it and
    /// every 1/p stays linear in lambda. T-0209 V4: the constant x0.5 it replaces cost 10 against 9 at lambda 8.
    public static let minorSlope = 2.0

    /// The minor clause's condition, customModel.ts's `MINOR_CONDITION`.
    public static let minorCondition =
        "(road_class == RESIDENTIAL || road_class == LIVING_STREET || road_class == SERVICE) && scenic_score < 7"

    /// T-0244 (c): the band ladder - one band per integer `scenic_score` below `highBand`, highest first,
    /// customModel.ts's `BAND_LADDER`. Measured over LA (T-0244 run1) it moves the route before lambda 8 on all
    /// three pairs where the old three bands left two of them unmoved through lambda 4.
    public static let ladder = [6, 5, 4, 3, 2, 1, 0]

    /// The penalty slope of a road scored `score`: (highBand - s) / highBand below the high band, 0 at or above.
    public static func slope(_ score: Int) -> Double {
        score >= highBand ? 0 : Double(highBand - score) / Double(highBand)
    }

    /// The priority of a band with penalty `slope` at `lambda`: 1 / (1 + slope x lambda).
    ///
    /// lambda = 0 leaves every band at 1, which - with distance_influence 0 - makes the lambda-0 weight the
    /// route's seconds: the fastest route, the bisection's lower bracket, and T(lambda) non-decreasing (T-0244
    /// (b)). Rising lambda only ever pushes a band down, and a slope-0 band never moves.
    public static func band(slope: Double, lambda: Double) throws -> Double {
        guard lambda.isFinite, lambda >= 0, lambda <= LambdaSearch.maxLambda else {
            throw PlanFailure.lambdaOutOfRange(lambda)
        }
        return 1 / (1 + slope * lambda)
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
        var clauses = [("if", minorCondition, try band(slope: minorSlope, lambda: lambda)),
                       ("else_if", "scenic_score >= \(highBand)", try band(slope: slope(highBand), lambda: lambda))]
        for score in ladder where score > 0 {
            clauses.append(("else_if", "scenic_score >= \(score)", try band(slope: slope(score), lambda: lambda)))
        }
        clauses.append(("else", "", try band(slope: slope(0), lambda: lambda)))
        let priority = clauses.map { key, condition, value in
            """
                {
                  "\(key)": "\(condition)",
                  "multiply_by": "\(multiplier(value))"
                }
            """
        }
        return """
        {
          "distance_influence": 0,
          "priority": [
        \(priority.joined(separator: ",\n"))
          ]
        }
        """
    }
}

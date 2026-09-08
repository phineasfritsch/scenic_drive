import Foundation

/// How pretty one way is to drive, in `0...1`.
///
/// ## The mean is geometric, and that is the design
///
///     score = M^0.35 * E^0.65
///
/// The plan's own justification: it *"keeps a curvy industrial road (0.32) apart from a straight redwood road
/// (0.62)"*. A road that is thrilling to drive but ugly and a road that is beautiful but dull are different
/// products, and an **arithmetic** mean says they are the same thing. The geometric mean punishes imbalance -
/// a term near zero drags the whole score down however good the other one is - which is the behaviour this
/// product wants, because nobody enjoys a hairpin through a scrapyard.
///
/// The exponents say scenery leads: `alpha = 0.35` on how the road drives, `0.65` on what it goes past,
/// because this is a **car** product and not a motorcycle one. Those two numbers are the single most
/// product-defining constants in the repository, and the plan's tuning process exists to move them.
///
/// Substituting an arithmetic mean is the "simplification" this file is most likely to suffer, and most
/// fixtures would not notice: the two means agree whenever M and E are close. The test suite carries a
/// fixture where they are deliberately far apart.
///
/// ## A motorway scores zero and is still allowed
///
/// `highway = motorway` scores **0** here. It is **not** gated - `Gates.decide` returns `.allowed` for it, and
/// CLAUDE.md lists that as an invariant. The two are different mechanisms and the whole freeway-shoulders
/// design needs both at once: a motorway is *dull*, so lambda penalises it like any other dull edge, and the
/// router is free to use one for the shoulders of a drive whose middle is Skyline.
public enum SegmentScore {

    // MARK: - the exponents

    /// The weight on M, how the road drives. The plan's `alpha`.
    public static let driveExponent = 0.35
    /// The weight on E, what the road goes past.
    public static let sceneryExponent = 0.65

    // MARK: - M's weights

    public static let curvatureWeight = 0.45
    public static let elevationGainWeight = 0.20
    public static let speedFitWeight = 0.20
    public static let sinuosityWeight = 0.15

    // MARK: - E's weights

    public static let canopyWeight = 0.24
    public static let reliefWeight = 0.22
    public static let openGroundWeight = 0.16
    public static let poiWeight = 0.14
    public static let waterWeight = 0.12
    public static let quietRoadsideWeight = 0.12

    /// Added to E for a designated scenic byway, then E is capped at 1.
    public static let bywayBonus = 0.15

    // MARK: - the soft multipliers

    /// A tunnel longer than this makes the way almost worthless as scenery - you cannot see out of it.
    public static let tunnelThresholdMeters = 300.0
    public static let tunnelMultiplier = 0.15

    /// A road this close to a motorway hears it, whatever the trees are doing.
    public static let motorwayProximityMeters = 150.0
    public static let motorwayProximityMultiplier = 0.7

    /// Roads whose missing `surface` tag means "probably paved" - these classes are surveyed enough that an
    /// absent tag says nothing.
    public static let assumedPavedClasses: Set<String> = ["primary", "secondary", "tertiary",
                                                          "primary_link", "secondary_link", "tertiary_link"]

    /// Roads whose missing `surface` tag is worth a small penalty and a flag to the driver. The plan's x0.8.
    public static let unsurveyedClasses: Set<String> = ["unclassified", "residential"]
    public static let unsurveyedMultiplier = 0.8

    /// Ways that are dull by construction. **Score zero, never gated.**
    public static let dullClasses: Set<String> = ["motorway", "motorway_link", "trunk", "trunk_link"]

    // MARK: - the score

    /// The scenic score for a way, or nil if a term is outside `0...1`.
    ///
    /// Nil rather than a clamp: a term out of range is an ETL bug, and a plausible score computed from a
    /// wrong input is the hardest kind of error to find later.
    public static func score(for t: SegmentTerms) -> Double? {
        for term in t.unitTerms where !(term.value.isFinite && (0.0...1.0).contains(term.value)) {
            return nil
        }
        guard t.tunnelMeters.isFinite, t.tunnelMeters >= 0 else { return nil }
        guard !t.metersToNearestMotorway.isNaN, t.metersToNearestMotorway >= 0 else { return nil }

        if dullClasses.contains(t.highway) { return 0 }

        let m = curvatureWeight * t.curvature
            + elevationGainWeight * t.elevationGain
            + speedFitWeight * t.speedFit
            + sinuosityWeight * t.sinuosity

        var e = canopyWeight * t.canopy
            + reliefWeight * t.relief
            + openGroundWeight * (1 - t.impervious)
            + poiWeight * t.pointsOfInterest
            + waterWeight * t.water
            + quietRoadsideWeight * (1 - t.furniture)
        if t.isByway { e = min(1, e + bywayBonus) }

        // pow(0, positive) is 0, which is what the geometric mean should say: a way with nothing going for
        // it on one axis scores nothing, however good the other axis is. That is the whole point of using
        // this mean rather than an arithmetic one.
        var score = pow(m, driveExponent) * pow(e, sceneryExponent)

        if t.tunnelMeters > tunnelThresholdMeters { score *= tunnelMultiplier }
        if t.metersToNearestMotorway < motorwayProximityMeters { score *= motorwayProximityMultiplier }
        if t.surface == nil, unsurveyedClasses.contains(t.highway) { score *= unsurveyedMultiplier }

        return score
    }

    /// Whether this way's missing `surface` tag should be told to the driver.
    ///
    /// Separate from the score on purpose: the penalty is the scoring function's business and the flag is the
    /// hazard strip's, and a route can accumulate enough flagged distance to be worth a line on screen even
    /// when no single way scored badly for it.
    public static func raisesSurfaceUnknownFlag(_ t: SegmentTerms) -> Bool {
        t.surface == nil && unsurveyedClasses.contains(t.highway)
    }
}

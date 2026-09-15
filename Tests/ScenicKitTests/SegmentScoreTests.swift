import Foundation
import Testing
@testable import ScenicKit

/// The formula's structure is what these pin, and the hardest thing to pin is the **geometric** mean, because
/// an arithmetic one agrees with it whenever M and E are close - which is most fixtures. So the discriminating
/// case is built on purpose, with M and E as far apart as the range allows, and the expected values are
/// computed by hand from the stated weights rather than read off a run.
///
/// The plan quotes two worked outputs - 0.32 for a curvy industrial road, 0.62 for a straight redwood one -
/// but gives no term values that produce them. Reverse-engineering inputs to hit those numbers would be
/// fitting the answer to the target, so it is not done here and the numbers are recorded as unreproduced.
@Suite("Segment score")
struct SegmentScoreTests {

    /// Terms where every `0...1` input takes the same value, so M == E == v. Both weight sets sum to 1, which
    /// is what makes this true - and `unbalancedTerms` below relies on it.
    static func uniform(_ v: Double, highway: String = "tertiary") -> SegmentTerms {
        SegmentTerms(curvature: v, elevationGain: v, speedFit: v, sinuosity: v,
                     canopy: v, relief: v, impervious: 1 - v, pointsOfInterest: v, water: v,
                     furniture: 1 - v, highway: highway)
    }

    /// M and E set independently. `impervious` and `furniture` enter the formula as `1 - x`.
    static func split(drive m: Double, scenery e: Double, highway: String = "tertiary") -> SegmentTerms {
        SegmentTerms(curvature: m, elevationGain: m, speedFit: m, sinuosity: m,
                     canopy: e, relief: e, impervious: 1 - e, pointsOfInterest: e, water: e,
                     furniture: 1 - e, highway: highway)
    }

    // MARK: - THE MEAN

    @Test("the mean is geometric, so a thrilling drive through an ugly place does not average out")
    func meanIsGeometricNotArithmetic() throws {
        // M = 0.9, E = 0.1. A hairpin road through a scrapyard.
        //   geometric   0.9^0.35 * 0.1^0.65 = 0.9637955 * 0.2238721 = 0.2157672
        //   arithmetic  0.35*0.9 + 0.65*0.1 = 0.315 + 0.065        = 0.38
        // The gap is the whole design: an arithmetic mean would rate this road a third better than it is.
        let thrillingButUgly = try #require(SegmentScore.score(for: Self.split(drive: 0.9, scenery: 0.1)))
        #expect(abs(thrillingButUgly - 0.2157672) < 1e-5, "got \(thrillingButUgly)")
        #expect(thrillingButUgly < 0.30, "an arithmetic mean would give 0.38 here")

        // M = 0.1, E = 0.9. A straight road through redwoods.
        //   geometric   0.1^0.35 * 0.9^0.65 = 0.4466839 * 0.9338075 = 0.4171165
        //   arithmetic  0.35*0.1 + 0.65*0.9 = 0.035 + 0.585        = 0.62
        let dullButBeautiful = try #require(SegmentScore.score(for: Self.split(drive: 0.1, scenery: 0.9)))
        #expect(abs(dullButBeautiful - 0.4171165) < 1e-5, "got \(dullButBeautiful)")
        #expect(dullButBeautiful < 0.50, "an arithmetic mean would give 0.62 here")

        // Scenery leads, which is what the 0.35 / 0.65 split says. True of both means, so it is NOT what
        // distinguishes them - it is here to pin the exponents' ORDER, not the mean.
        #expect(dullButBeautiful > thrillingButUgly)
    }

    @Test("a balanced road is where the two means agree, which is why most fixtures miss the difference")
    func balancedRoadHidesTheDifference() throws {
        // M = E = 0.5 gives 0.5^0.35 * 0.5^0.65 = 0.5^1 = 0.5 exactly, and the arithmetic mean gives 0.5 too.
        // Recorded so nobody later "simplifies" the mean, sees this fixture pass, and believes it.
        let balanced = try #require(SegmentScore.score(for: Self.uniform(0.5)))
        #expect(abs(balanced - 0.5) < 1e-12)
    }

    @Test("a term at zero on one axis takes the whole score to zero")
    func zeroOnOneAxisIsZero() throws {
        // The behaviour that follows from a geometric mean and is the reason for choosing it: nothing
        // compensates for having nothing to look at.
        #expect(try #require(SegmentScore.score(for: Self.split(drive: 1, scenery: 0))) == 0)
        #expect(try #require(SegmentScore.score(for: Self.split(drive: 0, scenery: 1))) == 0)
    }

    // MARK: - the exponents and the weights

    @Test("the exponents are 0.35 and 0.65, and they sum to one")
    func exponentsArePinned() {
        #expect(SegmentScore.driveExponent == 0.35)
        #expect(SegmentScore.sceneryExponent == 0.65)
        // Summing to 1 is what makes the score a mean rather than an arbitrary product, and what keeps the
        // output in 0...1. Compared against a literal, not against `driveExponent + sceneryExponent`.
        #expect(SegmentScore.driveExponent + SegmentScore.sceneryExponent == 1.0)
    }

    @Test("both weight sets sum to one, proved through the formula rather than by adding the constants")
    func weightSetsSumToOne() throws {
        // `score = M^a * E^b` is ONE equation in the two sums, and one equation does not pin two unknowns.
        // A reviewer produced the counterexample by measurement: with M's weights summing to 1.05 and E's to
        // 1.05^(-a/b), about 0.97407046996785, `uniform(1.0)` still scores 1.0 to within 1e-12. So this test
        // needs a SECOND equation, and the byway cap - the formula's only non-linearity - supplies it.
        //
        //   (1)  SM^a * SE^b          == 1
        //   (2)  SM^a * min(1, SE+B)^b == 1      with B > 0
        //
        // Dividing, min(1, SE+B) == SE. If SE+B < 1 that forces B == 0, excluded by (3) below; so the cap is
        // active, SE == 1, and (1) then forces SM == 1. Neither sum is added up here, and the counterexample
        // above fails (2) at 1.0172231953677011.
        let best = try #require(SegmentScore.score(for: Self.uniform(1.0)))
        #expect(abs(best - 1.0) < 1e-12, "(1) every term at 1 must score exactly 1; got \(best)")

        var saturated = Self.uniform(1.0)
        saturated.isByway = true
        let cappedBest = try #require(SegmentScore.score(for: saturated))
        #expect(abs(cappedBest - 1.0) < 1e-12, "(2) the cap must bite at E = 1 and change nothing; got \(cappedBest)")

        // (3) B > 0, behaviourally rather than against the literal: below saturation the bonus must move the
        // score up. Without this, B == 0 collapses (2) back onto (1) and the pair proves nothing again.
        let plain = try #require(SegmentScore.score(for: Self.uniform(0.5)))
        var bonused = Self.uniform(0.5)
        bonused.isByway = true
        #expect(try #require(SegmentScore.score(for: bonused)) > plain, "(3) the byway bonus is strictly positive")

        // And the individual weights, written out, since the tuning process in the plan will move them and a
        // moved weight should be a deliberate act with a visible diff.
        #expect(SegmentScore.curvatureWeight == 0.45)
        #expect(SegmentScore.elevationGainWeight == 0.20)
        #expect(SegmentScore.speedFitWeight == 0.20)
        #expect(SegmentScore.sinuosityWeight == 0.15)
        #expect(SegmentScore.canopyWeight == 0.24)
        #expect(SegmentScore.reliefWeight == 0.22)
        #expect(SegmentScore.openGroundWeight == 0.16)
        #expect(SegmentScore.poiWeight == 0.14)
        #expect(SegmentScore.waterWeight == 0.12)
        #expect(SegmentScore.quietRoadsideWeight == 0.12)
    }

    /// One M term at 1 and the rest at 0, scenery held level, so the scores rank exactly as the M weights do.
    static func driveOnly(_ path: WritableKeyPath<SegmentTerms, Double>) -> SegmentTerms {
        var t = SegmentTerms(canopy: 0.5, relief: 0.5, impervious: 0.5,
                             pointsOfInterest: 0.5, water: 0.5, furniture: 0.5, highway: "tertiary")
        t[keyPath: path] = 1
        return t
    }

    @Test("curvature carries more of M than any other term")
    func curvatureDominatesM() throws {
        // Against EVERY other term in M, not only sinuosity. The earlier version compared curvature with
        // sinuosity alone and carried a comment claiming a weight swap "would leave `weightSetsSumToOne`
        // green" - both wrong. That test pins all ten weights as literals, so it catches any swap of the
        // CONSTANTS; what it cannot see is the effective weights moving at the point of use. Measured: with
        // 0.16 * curvature and 0.49 * elevationGain in the sum, M still totals 1.00, every literal stays
        // green, and a curvature-vs-sinuosity comparison stays green too while curvature no longer dominates.
        let curvy = try #require(SegmentScore.score(for: Self.driveOnly(\.curvature)))
        for (name, path) in [("elevationGain", \SegmentTerms.elevationGain),
                             ("speedFit", \SegmentTerms.speedFit),
                             ("sinuosity", \SegmentTerms.sinuosity)] {
            let other = try #require(SegmentScore.score(for: Self.driveOnly(path)))
            #expect(curvy > other, "curvature must outrank \(name); got \(curvy) vs \(other)")
        }
    }

    @Test("impervious ground and street furniture count against the score, not for it")
    func invertedTermsAreInverted() throws {
        let clean = SegmentTerms(curvature: 0.5, elevationGain: 0.5, speedFit: 0.5, sinuosity: 0.5,
                                 canopy: 0.5, relief: 0.5, impervious: 0.0, pointsOfInterest: 0.5,
                                 water: 0.5, furniture: 0.0, highway: "tertiary")
        let pavedAndCluttered = SegmentTerms(curvature: 0.5, elevationGain: 0.5, speedFit: 0.5,
                                             sinuosity: 0.5, canopy: 0.5, relief: 0.5, impervious: 1.0,
                                             pointsOfInterest: 0.5, water: 0.5, furniture: 1.0,
                                             highway: "tertiary")
        #expect(try #require(SegmentScore.score(for: clean)) > #require(SegmentScore.score(for: pavedAndCluttered)))
    }

    // MARK: - THE OTHER INVARIANT

    @Test("a motorway scores zero, which is not the same as being refused")
    func motorwayScoresZero() throws {
        // CLAUDE.md: motorway and trunk carry scenic_score 0 and are PENALISED, not hard-excluded. This file
        // owns the "scores 0" half. The "is still allowed" half belongs to Gates, which is not on this branch,
        // so the pairing cannot be asserted here - recorded in the task Log rather than implied.
        //
        // Given the best possible terms, so this cannot pass by the terms being poor.
        for highway in ["motorway", "motorway_link", "trunk", "trunk_link"] {
            let best = Self.uniform(1.0, highway: highway)
            #expect(try #require(SegmentScore.score(for: best)) == 0, "\(highway) must score 0")
        }
        // And a road that is not one of those four keeps its score with identical terms, so the rule is about
        // the class and not about something else in the fixture.
        #expect(try #require(SegmentScore.score(for: Self.uniform(1.0, highway: "secondary"))) == 1.0)
    }

    // MARK: - the soft multipliers, at and either side of each threshold

    @Test("a tunnel longer than 300 m costs 85 percent of the score, and 300 m exactly does not")
    func tunnelThresholdIsStrict() throws {
        var t = Self.uniform(0.5)
        t.tunnelMeters = 300
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5) < 1e-12, "300 m is not over 300 m")

        t.tunnelMeters = 301
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5 * 0.15) < 1e-12)

        t.tunnelMeters = 0
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5) < 1e-12)
    }

    @Test("a road within 150 m of a motorway hears it, and 150 m exactly does not")
    func motorwayProximityThresholdIsStrict() throws {
        var t = Self.uniform(0.5)
        t.metersToNearestMotorway = 150
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5) < 1e-12, "150 m is not within 150 m")

        t.metersToNearestMotorway = 149
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5 * 0.7) < 1e-12)

        t.metersToNearestMotorway = .infinity
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5) < 1e-12)
    }

    @Test("the soft multipliers compound rather than replacing one another")
    func multipliersCompound() throws {
        var t = Self.uniform(0.5)
        t.tunnelMeters = 400
        t.metersToNearestMotorway = 100
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5 * 0.15 * 0.7) < 1e-12)
    }

    // MARK: - absent surface

    @Test("both unsurveyed classes with no surface tag are penalised and flagged; assumed-paved ones are not")
    func absentSurfaceRule() throws {
        // The plan names TWO classes on each side: unclassified/residential take x0.8 and raise a flag, while
        // primary/secondary/tertiary are treated as paved. An earlier version exercised `residential` and
        // `tertiary` only, so dropping "unclassified" from `unsurveyedClasses` changed nothing any test could
        // see - every unclassified road in the graph silently losing both the penalty and the driver-facing
        // flag. Absent is never treated as unpaved: that is the gates' business and they need positive
        // evidence.
        for highway in ["unclassified", "residential"] {
            let t = Self.uniform(0.5, highway: highway)
            #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5 * 0.8) < 1e-12, "\(highway) takes x0.8")
            #expect(SegmentScore.raisesSurfaceUnknownFlag(t), "\(highway) must raise the flag")
        }

        // The assumed-paved half of the rule is what NOT being in `unsurveyedClasses` means, so it is pinned
        // here by behaviour rather than by a second constant that lists the classes and is read by nothing.
        for highway in ["primary", "secondary", "tertiary"] {
            let t = Self.uniform(0.5, highway: highway)
            #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5) < 1e-12, "\(highway) is assumed paved")
            #expect(!SegmentScore.raisesSurfaceUnknownFlag(t), "\(highway) must raise no flag")
        }

        // A road that DOES carry a surface tag takes neither the penalty nor the flag.
        var surfaced = Self.uniform(0.5, highway: "residential")
        surfaced.surface = "asphalt"
        #expect(abs(try #require(SegmentScore.score(for: surfaced)) - 0.5) < 1e-12)
        #expect(!SegmentScore.raisesSurfaceUnknownFlag(surfaced))
    }

    // MARK: - byway, and the range

    @Test("a byway bonus is added to scenery and capped, so it cannot push the score past one")
    func bywayBonusIsCapped() throws {
        var t = Self.uniform(0.9)
        t.isByway = true
        // E = 0.9 + 0.15 = 1.05, capped to 1. Score = 0.9^0.35 * 1^0.65 = 0.9637955.
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.9637955) < 1e-5)

        var best = Self.uniform(1.0)
        best.isByway = true
        #expect(try #require(SegmentScore.score(for: best)) == 1.0, "the cap must hold at the top")
    }

    @Test("a term outside 0...1 is refused rather than quantised")
    func termsAreValidatedNotClamped() {
        // A value out of range is an ETL bug, and a plausible score computed from a wrong input is the
        // hardest kind of error to find later.
        var t = Self.uniform(0.5)
        t.curvature = 1.5
        #expect(SegmentScore.score(for: t) == nil)

        t = Self.uniform(0.5)
        t.canopy = -0.1
        #expect(SegmentScore.score(for: t) == nil)

        t = Self.uniform(0.5)
        t.water = .nan
        #expect(SegmentScore.score(for: t) == nil)

        t = Self.uniform(0.5)
        t.tunnelMeters = -1
        #expect(SegmentScore.score(for: t) == nil)
    }
}

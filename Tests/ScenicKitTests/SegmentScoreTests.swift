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
        // Adding the constants together and checking the total is asking each set about itself. Instead:
        // every term at 1 must give M = 1 and E = 1, so the score is 1 - which is only true if each set sums
        // to exactly 1. A weight moved anywhere breaks this without any other test needing to know the split.
        let best = try #require(SegmentScore.score(for: Self.uniform(1.0)))
        #expect(abs(best - 1.0) < 1e-12, "got \(best)")

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

    @Test("curvature carries more of M than any other term")
    func curvatureDominatesM() throws {
        // 0.45 against 0.20 / 0.20 / 0.15 is a product decision, not an accident, and swapping two weights
        // would leave `weightSetsSumToOne` green.
        let curvy = SegmentTerms(curvature: 1, canopy: 0.5, relief: 0.5, impervious: 0.5,
                                 pointsOfInterest: 0.5, water: 0.5, furniture: 0.5, highway: "tertiary")
        let sinuous = SegmentTerms(sinuosity: 1, canopy: 0.5, relief: 0.5, impervious: 0.5,
                                   pointsOfInterest: 0.5, water: 0.5, furniture: 0.5, highway: "tertiary")
        #expect(try #require(SegmentScore.score(for: curvy)) > #require(SegmentScore.score(for: sinuous)))
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

    @Test("a residential road with no surface tag is penalised and flagged; a tertiary one is not")
    func absentSurfaceRule() throws {
        // The plan: primary/secondary/tertiary with no surface tag are treated as paved, while
        // unclassified/residential take x0.8 and raise a flag. Absent is never treated as unpaved - that is
        // the gates' business and they need positive evidence.
        let residential = Self.uniform(0.5, highway: "residential")
        #expect(abs(try #require(SegmentScore.score(for: residential)) - 0.5 * 0.8) < 1e-12)
        #expect(SegmentScore.raisesSurfaceUnknownFlag(residential))

        let tertiary = Self.uniform(0.5, highway: "tertiary")
        #expect(abs(try #require(SegmentScore.score(for: tertiary)) - 0.5) < 1e-12)
        #expect(!SegmentScore.raisesSurfaceUnknownFlag(tertiary))

        // A residential road that DOES carry a surface tag takes neither the penalty nor the flag.
        var surfaced = residential
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

import Foundation
import Testing
@testable import ScenicKit

/// The two soft multipliers, pinned where they actually switch.
///
/// Both tests below moved here from `SegmentScoreTests` with their names and their original assertions
/// intact, and each gained one probe. The move is the 300-line cap: that file stood at 290 lines and the
/// story these two have to tell needs room.
///
/// ## A probe one metre out is not a pin
///
/// They probed at 301 m and 149 m - the nearest INTEGER either side - and an integer is a fact about how
/// people write distances, not about where a `Double` comparison switches. Measured on the committed tree at
/// `e2b77f5`: `tunnelThresholdMeters = 300.0` could become `300.5`, and `motorwayProximityMeters = 150.0`
/// could become `149.5`, with all 39 tests green and no test red. A 300.4 m tunnel then took no penalty while
/// a test named *"a tunnel longer than 300 m costs 85 percent of the score"* passed, and a way 149.8 m from a
/// motorway took no x0.7 while a test named *"a road within 150 m of a motorway hears it"* passed. Each name
/// outran its own assertions by a whole metre.
///
/// The new probes are `(300.0).nextUp` and `(150.0).nextDown`: the nearest representable Doubles outside each
/// threshold, **a fact about IEEE 754 and not about the numbers under test**, so a probe computed this way
/// cannot cancel against the threshold it is measuring. With them, neither threshold can move at all in
/// either direction. This is the same instrument `validationWindowIsExactlyZeroToOne` uses on the `0...1`
/// window and `tunnelLengthIsValidated` on the guard floors - the last two of this file's five numeric
/// thresholds to get it.
@Suite("Segment score thresholds")
struct SegmentScoreThresholdTests {

    /// Terms where every `0...1` input takes the same value, so M == E == v and `uniform(0.5)` scores exactly
    /// 0.5 - which is what makes the multiplier arithmetic below readable.
    ///
    /// A local copy of the neighbouring suites' builder rather than a call into one, for the reason
    /// `SegmentScoreValidationTests` gives: `--prove-vacuity` empties every test file at once, and a
    /// cross-file helper turns that measurement into a build error, which proves nothing about the vacuity
    /// arm.
    static func uniform(_ v: Double) -> SegmentTerms {
        SegmentTerms(curvature: v, elevationGain: v, speedFit: v, sinuosity: v,
                     canopy: v, relief: v, impervious: 1 - v, pointsOfInterest: v, water: v,
                     furniture: 1 - v, highway: "tertiary")
    }

    @Test("a tunnel longer than 300 m costs 85 percent of the score, and 300 m exactly does not")
    func tunnelThresholdIsStrict() throws {
        var t = Self.uniform(0.5)
        t.tunnelMeters = 300
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5) < 1e-12, "300 m is not over 300 m")

        t.tunnelMeters = 301
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5 * 0.15) < 1e-12)

        // "longer than 300 m" is a claim about EVERY length past 300, and 301 left a metre of it unasserted:
        // with the threshold at 300.5 this assertion is the only one of the four that fails.
        t.tunnelMeters = (300.0).nextUp
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5 * 0.15) < 1e-12,
                "one Double past 300 m is already longer than 300 m")

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

        // The same claim on the other side: "within 150 m" is every distance below 150, and 149 left a metre
        // of it unasserted. With the threshold at 149.5 this assertion is the only one of the four that fails.
        t.metersToNearestMotorway = (150.0).nextDown
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5 * 0.7) < 1e-12,
                "one Double inside 150 m is already within 150 m")

        t.metersToNearestMotorway = .infinity
        #expect(abs(try #require(SegmentScore.score(for: t)) - 0.5) < 1e-12)
    }
}

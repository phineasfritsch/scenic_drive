import Foundation
import Testing
@testable import ScenicKit

/// What a literal pin on a weight cannot see, and what the byway bonus's two saturated fixtures could not see.
///
/// ## The weights are pinned twice over, and the two pins catch different things
///
/// `weightSetsSumToOne` writes all ten weights out as literals, so any edit to the DECLARATIONS is caught
/// whatever else is true. What a literal cannot see is the **effective** weight at the point of use: writing
/// `0.16 * t.curvature` into the sum leaves `curvatureWeight == 0.45` green and still changes every score the
/// formula produces. One such swap was pinned - `curvatureDominatesM` - and a reviewer then measured three
/// more that the whole suite passed: open ground with points of interest, canopy with water, elevation gain
/// with sinuosity. Each preserves its set's total of 1.00 exactly, so `weightSetsSumToOne` cannot object
/// either. Only the RANK, asserted through `SegmentScore.score(for:)`, can see them.
///
/// ## The byway bonus's value and form
///
/// `bywayBonusIsCapped` next door uses `uniform(0.9)` and `uniform(1.0)`, and both sit at or above
/// saturation, where the cap is the only thing visible. Measured by the same reviewer: `bywayBonus` could be
/// 0.25 or 0.11, and `e + bywayBonus` could become `e * (1 + bywayBonus)` - the bonus not being an addition
/// at all - with every test green. Only the sign (through `weightSetsSumToOne` step 3) and the cap were
/// pinned. The fixtures here sit **below** saturation, at two different levels, so the cap cannot be what
/// makes them pass.
///
/// Expected values are hand-computed from the stated weights, never read off a run. The fixture builders are
/// local copies rather than calls into the neighbouring suites on purpose: `--prove-vacuity` empties every
/// test file at once, and a cross-file helper turns that measurement into a build error, which proves nothing
/// about the vacuity arm.
@Suite("Segment score weights")
struct SegmentScoreWeightTests {

    /// Terms where every `0...1` input takes the same value, so M == E == v.
    static func uniform(_ v: Double) -> SegmentTerms {
        SegmentTerms(curvature: v, elevationGain: v, speedFit: v, sinuosity: v,
                     canopy: v, relief: v, impervious: 1 - v, pointsOfInterest: v, water: v,
                     furniture: 1 - v, highway: "tertiary")
    }

    // MARK: - the byway bonus, below the cap

    @Test("the byway bonus is exactly +0.15 added to E, not a scaling of it, at two levels below the cap")
    func bywayBonusIsExactlyFifteenHundredths() throws {
        // E = 0.4 + 0.15 = 0.55, M = 0.4, so the score is 0.4^0.35 * 0.55^0.65 = 0.4919905.
        // A bonus of 0.25 gives 0.5484218, one of 0.11 gives 0.4684267, and `e * 1.15` gives 0.4380398 -
        // none of them within 1e-5, and none of them reachable by the cap, which does not bite here.
        var low = Self.uniform(0.4)
        low.isByway = true
        let lowScore = try #require(SegmentScore.score(for: low))
        #expect(abs(lowScore - 0.4919905) < 1e-5, "got \(lowScore)")

        // A second level, because one point cannot separate "+0.15" from every other rule that passes
        // through it. E = 0.8 + 0.15 = 0.95, still under the cap: 0.8^0.35 * 0.95^0.65 = 0.8945443. Here a
        // bonus of 0.25 saturates and gives 0.9248717, 0.11 gives 0.8698781, `e * 1.15` gives 0.8760796.
        var high = Self.uniform(0.8)
        high.isByway = true
        let highScore = try #require(SegmentScore.score(for: high))
        #expect(abs(highScore - 0.8945443) < 1e-5, "got \(highScore)")

        // And a way that is not a byway gets nothing at either level: M == E == v gives exactly v.
        #expect(abs(try #require(SegmentScore.score(for: Self.uniform(0.4))) - 0.4) < 1e-12)
        #expect(abs(try #require(SegmentScore.score(for: Self.uniform(0.8))) - 0.8) < 1e-12)
    }

    // MARK: - the scenery weights, at the point of use

    /// Every E term at its scenic WORST, drive held level at 0.5 so M = 0.5. `impervious` and `furniture`
    /// enter the formula as `1 - x`, so their worst is 1.
    static func sceneryFloor() -> SegmentTerms {
        SegmentTerms(curvature: 0.5, elevationGain: 0.5, speedFit: 0.5, sinuosity: 0.5,
                     canopy: 0, relief: 0, impervious: 1, pointsOfInterest: 0, water: 0,
                     furniture: 1, highway: "tertiary")
    }

    /// The six E terms in their declared order, with the value each takes at its scenic BEST. Transcribed by
    /// hand from `SegmentScore`, never derived from it: a list read out of the code under test agrees with
    /// any code, including code whose order has been shuffled.
    static var sceneryTerms: [(name: String, path: WritableKeyPath<SegmentTerms, Double>, best: Double)] {
        [("canopy", \.canopy, 1), ("relief", \.relief, 1), ("openGround", \.impervious, 0),
         ("pointsOfInterest", \.pointsOfInterest, 1), ("water", \.water, 1),
         ("quietRoadside", \.furniture, 0)]
    }

    @Test("the scenery weights keep their declared rank at the point of use, where the literals cannot see it")
    func sceneryWeightsRankAtThePointOfUse() throws {
        // One E term at its best with the rest at their worst makes E exactly that term's weight, and M is
        // fixed at 0.5, so the six scores rank exactly as 0.24, 0.22, 0.16, 0.14, 0.12, 0.12 do.
        var scores: [(name: String, score: Double)] = []
        for (name, path, best) in Self.sceneryTerms {
            var t = Self.sceneryFloor()
            t[keyPath: path] = best
            scores.append((name, try #require(SegmentScore.score(for: t))))
        }
        // Without this the list could go to [] and the loops below would assert nothing at all.
        #expect(scores.count == 6, "a term added to E needs a line in sceneryTerms; walked \(scores.count)")

        // canopy > relief > openGround > pointsOfInterest > water.
        for i in 0..<4 {
            let (a, b) = (scores[i], scores[i + 1])
            #expect(a.score > b.score, "\(a.name) must outrank \(b.name); got \(a.score) vs \(b.score)")
        }
        // water and quiet roadside are both 0.12, and their EQUALITY is as much a claim as any ordering: a
        // swap that broke it would move real scores. Asserted against each other rather than against a
        // computed weight, so nothing here reads a constant back out of the formula.
        #expect(abs(scores[4].score - scores[5].score) < 1e-12,
                "water and quiet roadside carry the same weight; got \(scores[4].score) vs \(scores[5].score)")
    }

    // MARK: - the drive weights, at the point of use

    /// Every M term at 0, scenery held level at 0.5 so E = 0.5.
    static func driveFloor() -> SegmentTerms {
        SegmentTerms(canopy: 0.5, relief: 0.5, impervious: 0.5,
                     pointsOfInterest: 0.5, water: 0.5, furniture: 0.5, highway: "tertiary")
    }

    /// The four M terms in their declared order, transcribed by hand for the same reason as above.
    static var driveTerms: [(name: String, path: WritableKeyPath<SegmentTerms, Double>)] {
        [("curvature", \.curvature), ("elevationGain", \.elevationGain),
         ("speedFit", \.speedFit), ("sinuosity", \.sinuosity)]
    }

    @Test("the drive weights keep their declared rank at the point of use, where the literals cannot see it")
    func driveWeightsRankAtThePointOfUse() throws {
        var scores: [(name: String, score: Double)] = []
        for (name, path) in Self.driveTerms {
            var t = Self.driveFloor()
            t[keyPath: path] = 1
            scores.append((name, try #require(SegmentScore.score(for: t))))
        }
        #expect(scores.count == 4, "a term added to M needs a line in driveTerms; walked \(scores.count)")

        // 0.45, 0.20, 0.20, 0.15: curvature leads, elevation gain and speed fit are level, sinuosity trails.
        // `curvatureDominatesM` next door makes the first claim too; the other two are only made here.
        #expect(scores[0].score > scores[1].score,
                "curvature must outrank elevation gain; got \(scores[0].score) vs \(scores[1].score)")
        #expect(abs(scores[1].score - scores[2].score) < 1e-12,
                "elevation gain and speed fit are level; got \(scores[1].score) vs \(scores[2].score)")
        #expect(scores[2].score > scores[3].score,
                "speed fit must outrank sinuosity; got \(scores[2].score) vs \(scores[3].score)")
    }
}

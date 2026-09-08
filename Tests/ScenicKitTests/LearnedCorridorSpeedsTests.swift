import Foundation
import Testing
@testable import ScenicKit

/// Two of these tests are product invariants from CLAUDE.md rather than ordinary unit tests: the badge until
/// five samples (P-SAFE-07) and the absence of `Codable` (P-PRIV-05). Both are properties that a reasonable
/// future change would quietly remove - "just default the ratio to 1.0", "just add Codable so we can log it"
/// - and neither is something the compiler will complain about.
@Suite("Learned corridor speeds")
struct LearnedCorridorSpeedsTests {

    static let cell: UInt64 = 0x8829a1d_6fff_ffff
    static func key(_ hour: Int = 8) -> CorridorKey { CorridorKey(cell: cell, hourOfWeek: hour)! }

    // MARK: - the badge

    @Test("under five samples there is no ratio, and nil does not mean 1.0")
    func badgeUntilFiveSamples() {
        // FIVE, written out. CLAUDE.md names the number - "until a corridor has >= 5 learned samples" - so
        // it is a specified constant, not an implementation detail, and the assertion must not be derived
        // from it. The first draft looped `for n in 1..<LearnedCorridorSpeeds.confidenceThreshold`, which
        // becomes an empty range the moment the constant is lowered: the mutation harness dropped the
        // threshold to 1 and this test passed over zero iterations. That is this repository's signature
        // defect - a check whose expected value comes from the thing it checks - sitting in the test for a
        // product invariant.
        #expect(LearnedCorridorSpeeds.confidenceThreshold == 5)

        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        for n in 1...4 {
            learned.record(k, actual: 2400, freeFlow: 1800)
            #expect(learned.sampleCount(for: k) == n)
            #expect(!learned.isConfident(about: k))
            #expect(learned.ratio(for: k) == nil, "\(n) samples is not enough to claim knowledge")
            #expect(!learned.adjust(1800, for: k).learned)
        }
        learned.record(k, actual: 2400, freeFlow: 1800)
        #expect(learned.sampleCount(for: k) == 5)
        #expect(learned.isConfident(about: k))
        #expect(learned.ratio(for: k) != nil)
    }

    @Test("an unlearned corridor returns the free-flow duration and says it is unlearned")
    func unlearnedIsFlagged() {
        let learned = LearnedCorridorSpeeds()
        let (duration, isLearned) = learned.adjust(1800, for: Self.key())
        #expect(duration == 1800)
        #expect(!isLearned, "an unbadged free-flow ETA is the over-promise this type exists to prevent")
    }

    @Test("a learned corridor stretches the ETA and says it is learned")
    func learnedAdjusts() {
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        // Five drives that each took 40 minutes where free-flow says 30.
        for _ in 0..<5 { learned.record(k, actual: 2400, freeFlow: 1800) }
        let (duration, isLearned) = learned.adjust(1800, for: k)
        #expect(isLearned)
        #expect(duration > 1800, "rush hour is slower than free flow")
        #expect(abs(duration - 2400) < 1)
    }

    @Test("hours of the week are learned separately")
    func hoursAreSeparate() {
        var learned = LearnedCorridorSpeeds()
        let rush = Self.key(8 + 24)        // Tuesday 08:00
        let sunday = Self.key(6 * 24 + 8)  // Sunday 08:00
        for _ in 0..<5 { learned.record(rush, actual: 2700, freeFlow: 1800) }
        #expect(learned.ratio(for: rush) != nil)
        #expect(learned.ratio(for: sunday) == nil, "Sunday at 8am is not Tuesday at 8am")
    }

    @Test("cells are learned separately, so one road's traffic never speaks for another's")
    func cellsAreSeparate() throws {
        // There was a `hoursAreSeparate` and no `cellsAreSeparate`: every store-level test used ONE cell, so
        // a hand-written `Hashable` that combined only `hourOfWeek` — and `self.cell = cell & 0xFFFF` — both
        // left the whole suite green. The user-visible failure is the badge invariant defeated from the
        // inside: a back road nobody has ever driven inherits the freeway's five crawling samples, drops the
        // *estimate · no traffic data* badge, and doubles its own ETA on somebody else's evidence.
        //
        // The two ids differ only ABOVE the low sixteen bits, which is what makes a truncating key fail here.
        let freeway = try #require(CorridorKey(cell: 0x8829_a1d6_ffff_ffff, hourOfWeek: 32))
        let backRoad = try #require(CorridorKey(cell: 0x8829_a1d7_ffff_ffff, hourOfWeek: 32))

        var learned = LearnedCorridorSpeeds()
        for _ in 0..<5 { learned.record(freeway, actual: 3600, freeFlow: 1800) }
        #expect(learned.sampleCount(for: freeway) == 5)
        #expect(learned.isConfident(about: freeway))

        #expect(learned.sampleCount(for: backRoad) == 0,
                "the back road has never been driven; its count must still be zero")
        #expect(learned.ratio(for: backRoad) == nil, "and nil means show the badge")
        let (duration, isLearned) = learned.adjust(1800, for: backRoad)
        #expect(duration == 1800, "an untravelled corridor keeps its free-flow ETA; got \(duration)")
        #expect(!isLearned, "and it must still be badged as an estimate")
    }

    // MARK: - the privacy invariant

    @Test("nothing here is Codable, and that is a privacy property not an oversight")
    func notCodable() {
        // P-PRIV-05. This is a record of when and where one person drives. Conformance is the mechanism by
        // which it leaks - one JSONEncoder in a diagnostics payload and a commute pattern is on a server.
        // The compiler will not warn when somebody adds `: Codable` later, so the absence is asserted here.
        let learned = LearnedCorridorSpeeds()
        #expect(!(learned is any Encodable))
        #expect(!(learned is any Decodable))
        let k = Self.key()
        #expect(!(k is any Encodable))
        #expect(!(k is any Decodable))
    }

    // MARK: - the learning

    @Test("the ratio stays inside its bounds however wild the sample")
    func ratioIsBounded() throws {
        // Both halves of this test used to be stated in terms of the constant they check -
        // `#expect(r2 <= LearnedCorridorSpeeds.maxRatio)` - which is true for ANY value the constant takes.
        // A reviewer mutated maxRatio to 3.0 and the whole suite stayed green.
        //
        // This is the repository's signature defect, and it was sitting thirty lines below the place where
        // the same Log entry describes catching and fixing it for `confidenceThreshold`. Finding the defect
        // once plainly does not inoculate a file against it.
        #expect(LearnedCorridorSpeeds.minRatio == 0.3)
        #expect(LearnedCorridorSpeeds.maxRatio == 1.0)

        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        // A drive that took twenty times free-flow: a closure, not congestion.
        for _ in 0..<5 { learned.record(k, actual: 36000, freeFlow: 1800) }
        let r = try #require(learned.ratio(for: k))
        #expect(r >= 0.3)
        #expect(abs(r - 0.3) < 1e-9, "clamped to the floor, not merely above it")

        // And one that claims to have beaten free-flow by 3x: a GPS glitch or a skipped corridor.
        var fast = LearnedCorridorSpeeds()
        let k2 = Self.key(9)
        for _ in 0..<5 { fast.record(k2, actual: 600, freeFlow: 1800) }
        let r2 = try #require(fast.ratio(for: k2))
        #expect(r2 <= 1.0, "nothing is faster than free flow")

        // The property, not just the number. This is what the constant is FOR: a learned corridor may never
        // return an ETA shorter than the free-flow duration it was handed. Stated this way it survives any
        // refactor of the clamp, and it is what actually failed under the reviewer's mutation - 1800 s in,
        // 600 s out, badge on.
        let adjusted = fast.adjust(1800, for: k2)
        #expect(adjusted.learned)
        #expect(adjusted.duration >= 1800,
                "a learned ETA below free-flow is the over-promise from the other direction; got \(adjusted.duration)")
    }

    @Test("a learned corridor still refuses a free-flow duration that is not a duration",
          arguments: [TimeInterval(0), -600, .nan, .infinity, -.infinity])
    func adjustRejectsUnusableFreeFlow(freeFlow: TimeInterval) {
        // `record` has six parameterised cases for exactly this input class and `adjust` had none, so both
        // reductions of its guard were uncaught: `guard let r = ratio(for: key)` and the weaker
        // `guard freeFlow.isFinite, let r = ...`. Under either, a corridor learned at ratio 0.75 turns
        // freeFlow = -600 into (-800.0, learned: true) and freeFlow = nan into (nan, learned: true) — a
        // nonsense number wearing the badge that means "we checked".
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        for _ in 0..<5 { learned.record(k, actual: 2400, freeFlow: 1800) }   // ratio 0.75, confident
        #expect(learned.isConfident(about: k))

        let (duration, isLearned) = learned.adjust(freeFlow, for: k)
        #expect(!isLearned, "an unusable input cannot produce a learned ETA; got \(duration)")
        if freeFlow.isNaN {
            #expect(duration.isNaN, "and it is handed back untouched")
        } else {
            #expect(duration == freeFlow, "and it is handed back untouched; got \(duration)")
        }
    }

    @Test("one unusual day cannot move the estimate far")
    func ewmaResistsOutliers() {
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        for _ in 0..<10 { learned.record(k, actual: 1980, freeFlow: 1800) }   // ratio ~0.91
        let before = try! #require(learned.ratio(for: k))
        learned.record(k, actual: 7200, freeFlow: 1800)                        // one dreadful Tuesday
        let after = try! #require(learned.ratio(for: k))
        #expect(after < before, "a bad day should move it")
        #expect(before - after < 0.25, "but one day must not redefine the corridor")
    }

    @Test("the second sample blends with the first rather than replacing it")
    func laterSamplesBlend() throws {
        // Structural gap a reviewer found: every multi-sample test here feeds IDENTICAL values, so "blend
        // the new sample in" and "replace the estimate with the new sample" produce the same number and are
        // indistinguishable. Widening `if n == 0` to `if n <= 1` - so drive #2 discards drive #1 - passed
        // the whole suite.
        //
        // The block that used to sit below this one was the signature defect again: its comment claimed
        // "two samples only, so the value is exactly the blend or exactly the replacement" while recording
        // five, and its `#expect(r2 > 0.5)` was true under BOTH hypotheses (0.94855 blended, 0.8285
        // replaced). A reviewer deleted this first block, left that one standing, and `if n <= 1` sailed
        // through. So the expectation below is a WRITTEN-OUT LITERAL, arithmetic done by hand at smoothing
        // 0.3 for the sequence 1.0, 0.5, 0.5, 0.5, 0.5:
        //
        //   r1 = 1.0                          (first sample at face value)
        //   r2 = 0.3*0.5 + 0.7*1.0     = 0.85
        //   r3 = 0.15   + 0.7*0.85     = 0.745
        //   r4 = 0.15   + 0.7*0.745    = 0.6715
        //   r5 = 0.15   + 0.7*0.6715   = 0.62005
        //
        // Under "replace the estimate with the newest sample" every step after the first lands on 0.5.
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        learned.record(k, actual: 1800, freeFlow: 1800)      // ratio 1.0
        for _ in 0..<4 { learned.record(k, actual: 3600, freeFlow: 1800) }   // ratio 0.5, four times
        let r = try #require(learned.ratio(for: k))
        #expect(r > 0.5, "the first drive must still be visible in the estimate; got \(r)")
        #expect(abs(r - 0.62005) < 1e-9, "expected exactly the blend, 0.62005; got \(r)")

        // The same five ratios in the opposite order must land somewhere else, which is what "history is
        // retained" MEANS. Sequence 0.5, 1.0, 1.0, 1.0, 1.0, again by hand:
        //
        //   r1 = 0.5 ; r2 = 0.65 ; r3 = 0.755 ; r4 = 0.8285 ; r5 = 0.87995
        //
        // Cross-check that costs nothing: the EWMA is affine, so swapping 0.5 and 1.0 throughout maps a
        // result r to 1.5 - r. 1.5 - 0.62005 = 0.87995, so the two literals were not transcribed twice from
        // the same slip. Under "replace" this run ends on 1.0 — free-flow — instead.
        var reversed = LearnedCorridorSpeeds()
        let k2 = Self.key(11)
        reversed.record(k2, actual: 3600, freeFlow: 1800)    // ratio 0.5
        for _ in 0..<4 { reversed.record(k2, actual: 1800, freeFlow: 1800) }  // ratio 1.0, four times
        let r2 = try #require(reversed.ratio(for: k2))
        #expect(abs(r2 - 0.87995) < 1e-9, "expected exactly the blend, 0.87995; got \(r2)")
        #expect(r2 < 1.0, "the slow first drive must still be visible; got \(r2)")
    }

    @Test("a corridor that is consistently slow is actually learned, not merely nudged")
    func consistentlySlowCorridorIsLearned() throws {
        // `smoothing` was constrained from above (0.7 fails ewmaResistsOutliers) and at exactly 0.0, and
        // nowhere else: 0.4, 0.15 and 0.001 all passed. At 0.001 the suite is green while the model is
        // inert — forty drives at three times free-flow still report a 31-minute ETA for a 90-minute drive,
        // with `learned == true` and the badge off. That is the headline over-promise reached through the
        // one constant the suite left loose, so here is the floor, stated as a product claim.
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        for _ in 0..<10 { learned.record(k, actual: 1800, freeFlow: 1800) }   // ten free-flow drives
        for _ in 0..<10 { learned.record(k, actual: 3600, freeFlow: 1800) }   // then ten that took an hour

        let (duration, isLearned) = learned.adjust(1800, for: k)
        #expect(isLearned)
        // The drive really takes 3600 s. After ten consecutive hours-long drives the estimate must be at
        // least 55 minutes — 3300 s, written out. At smoothing 0.3 it is 3501 s; at 0.15, 3008 s; at 0.001,
        // 1809 s, which is the free-flow number the badge was supposed to protect the user from.
        #expect(duration >= 3300, "ten identical slow drives must move the estimate; got \(duration)")
        #expect(duration <= 3600, "and never past what was actually observed; got \(duration)")
    }

    @Test("the first sample is taken at face value, not blended with a default")
    func firstSampleIsTheEstimate() {
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        learned.record(k, actual: 3600, freeFlow: 1800)     // ratio 0.5
        // Not yet confident, so no ratio is published - but four more identical drives must land on 0.5,
        // which they cannot if the first sample was blended against an assumed 1.0.
        for _ in 0..<4 { learned.record(k, actual: 3600, freeFlow: 1800) }
        let r = try! #require(learned.ratio(for: k))
        #expect(abs(r - 0.5) < 1e-9)
    }

    @Test("an unusable sample is rejected and does not count toward confidence",
          arguments: [(TimeInterval(0), TimeInterval(1800)), (1800, 0), (-1, 1800),
                      (.nan, 1800), (1800, .nan), (.infinity, 1800)])
    func rejectsBadSamples(actual: TimeInterval, freeFlow: TimeInterval) {
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        #expect(learned.record(k, actual: actual, freeFlow: freeFlow) == false)
        #expect(learned.sampleCount(for: k) == 0,
                "a rejected sample that still counted would let five bad drives drop the badge")
    }

    @Test("a usable sample is accepted, and says so")
    func acceptedSampleSaysSo() {
        // `rejectsBadSamples` pins `== false` for six unusable inputs and nothing pinned `== true` for a
        // good one, so `return true` -> `return false` on the accepted path was uncaught. A caller that
        // branches on the result would then treat every recorded drive as discarded.
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        #expect(learned.record(k, actual: 2400, freeFlow: 1800) == true)
        #expect(learned.sampleCount(for: k) == 1)
    }
}

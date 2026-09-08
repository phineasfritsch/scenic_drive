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
    func ratioIsBounded() {
        var learned = LearnedCorridorSpeeds()
        let k = Self.key()
        // A drive that took twenty times free-flow: a closure, not congestion.
        for _ in 0..<5 { learned.record(k, actual: 36000, freeFlow: 1800) }
        let r = try! #require(learned.ratio(for: k))
        #expect(r >= LearnedCorridorSpeeds.minRatio)

        // And one that claims to have beaten free-flow by 3x: a GPS glitch or a skipped corridor.
        var fast = LearnedCorridorSpeeds()
        let k2 = Self.key(9)
        for _ in 0..<5 { fast.record(k2, actual: 600, freeFlow: 1800) }
        let r2 = try! #require(fast.ratio(for: k2))
        #expect(r2 <= LearnedCorridorSpeeds.maxRatio, "nothing is faster than free flow")
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

    // MARK: - the key

    @Test("an hour outside the week is not a key")
    func rejectsBadHours() {
        #expect(CorridorKey(cell: 1, hourOfWeek: -1) == nil)
        #expect(CorridorKey(cell: 1, hourOfWeek: 168) == nil)
        #expect(CorridorKey(cell: 1, hourOfWeek: 0) != nil)
        #expect(CorridorKey(cell: 1, hourOfWeek: 167) != nil)
    }

    @Test("Monday is bucket zero regardless of what the calendar calls the first weekday")
    func mondayIsZero() throws {
        // The bug this pins: Calendar.firstWeekday is 1 (Sunday) in en_US and 2 (Monday) in most of Europe.
        // Deriving the bucket from it would bucket the same drive differently for two users, and would
        // re-bucket a user's own history when they travelled.
        var us = Calendar(identifier: .gregorian)
        us.firstWeekday = 1
        us.timeZone = TimeZone(identifier: "UTC")!
        var eu = Calendar(identifier: .gregorian)
        eu.firstWeekday = 2
        eu.timeZone = TimeZone(identifier: "UTC")!

        // 2026-09-07 is a Monday.
        var comps = DateComponents()
        comps.year = 2026; comps.month = 9; comps.day = 7; comps.hour = 9
        comps.timeZone = TimeZone(identifier: "UTC")!
        let monday9am = try #require(us.date(from: comps))

        let a = try #require(CorridorKey(cell: 1, date: monday9am, calendar: us))
        let b = try #require(CorridorKey(cell: 1, date: monday9am, calendar: eu))
        #expect(a.hourOfWeek == 9)
        #expect(a == b)
    }

    @Test("Sunday is the last day of the week, not the first")
    func sundayIsSix() throws {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "UTC")!
        var comps = DateComponents()
        comps.year = 2026; comps.month = 9; comps.day = 13; comps.hour = 0   // Sunday
        comps.timeZone = TimeZone(identifier: "UTC")!
        let sunday = try #require(cal.date(from: comps))
        let k = try #require(CorridorKey(cell: 1, date: sunday, calendar: cal))
        #expect(k.hourOfWeek == 6 * 24)
    }
}

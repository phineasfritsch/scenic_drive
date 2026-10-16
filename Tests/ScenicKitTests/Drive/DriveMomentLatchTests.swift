@testable import ScenicKit
import Testing

/// T-0361 R6: drive_started and drive_completed / drive_abandoned fire at most once each, the end only after the
/// start, and the end carries the shipping DriveSession's numbers WHOLE (memory full-equality-oracle).
@Suite("DriveMomentLatchTests")
struct DriveMomentLatchTests {
    /// A session 3 of 5 segments in, once off-route (rerouting): fraction 0.6, count 1.
    static func session() -> DriveSession {
        let line = DriveFixtures.line(latitude: 34.0, firstLongitude: -118.50, count: 6)
        var s = DriveSession(line: line, waypoints: [], lambda: 0.35, online: true)!
        for k in 0...3 { _ = s.observe(DriveFixtures.fix(DriveFixtures.on(line, segment: k), at: Double(k))) }
        let off = DriveFixtures.away(from: DriveFixtures.on(line, segment: 3))
        _ = s.observe(DriveFixtures.fix(off, at: 4))
        _ = s.observe(DriveFixtures.fix(off, at: 9))
        return s
    }

    @Test("T-0361 R6: begin is guidanceBegan once, then nothing")
    func beginsOnce() {
        var latch = DriveMomentLatch()
        let first = latch.begin()
        let second = latch.begin()
        #expect(first == .guidanceBegan)
        #expect(second == nil)
        #expect(latch.hasBegun)
    }

    @Test("T-0361 R6: an end with no begin is nothing, and does not use up the end")
    func noEndBeforeBegin() {
        let s = Self.session()
        var latch = DriveMomentLatch()
        let early = latch.end(s, arrived: true)
        #expect(early == nil)
        #expect(!latch.hasEnded)
        let began = latch.begin()
        let ended = latch.end(s, arrived: true)
        #expect(began == .guidanceBegan)
        #expect(ended == .guidanceEnded(arrived: true, fractionDriven: s.fractionDriven, offRouteCount: 1))
    }

    @Test("T-0361 R6: the end is the session's fraction and off-route count with the arrival, once",
          arguments: [true, false])
    func endsOnceWithTheSession(arrived: Bool) {
        let s = Self.session()
        #expect(abs(s.fractionDriven - 0.6) < 1e-12)
        #expect(s.offRouteCount == 1)
        var latch = DriveMomentLatch()
        _ = latch.begin()
        let end = latch.end(s, arrived: arrived)
        let again = latch.end(s, arrived: arrived)
        let flipped = latch.end(s, arrived: !arrived)
        let restart = latch.begin()
        #expect(end == .guidanceEnded(arrived: arrived, fractionDriven: s.fractionDriven, offRouteCount: s.offRouteCount))
        #expect(again == nil)
        #expect(flipped == nil)
        #expect(restart == nil)
    }
}

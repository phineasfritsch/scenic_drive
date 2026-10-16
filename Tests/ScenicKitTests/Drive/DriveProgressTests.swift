@testable import ScenicKit
import Testing

/// T-0361 R6: what drive_completed / drive_abandoned carry - DriveSession's off-route count and the fraction driven,
/// through the shipping `observe`, `connectivity` and `rerouteArrived`. The lines are along one latitude; lineA and
/// lineB have a vertex every 0.01 degree, shortB every 0.004 degree (the reroute's other shape, rv1-t0361 B1).
@Suite("DriveProgressTests")
struct DriveProgressTests {
    static let lineA = DriveFixtures.line(latitude: 34.0, firstLongitude: -118.50, count: 6)
    static let lineB = DriveFixtures.line(latitude: 34.0, firstLongitude: -118.40, count: 4)
    /// rv1-t0361 B1: 2 segments of 0.004 degree (~369 m) - fewer than lineA's progress 3, shorter than its ~922 m.
    static let shortB = (0..<3).map { Coordinate(latitude: 34.0, longitude: -118.40 + Double($0) * 0.004) }

    static func session(online: Bool = true) -> DriveSession {
        DriveSession(line: lineA, waypoints: [], lambda: 0.35, online: online)!
    }

    /// Drives segments 0...segment of `line` from time `t`, one fix a second; returns the next time.
    static func drive(_ s: inout DriveSession, _ line: [Coordinate], through segment: Int, from t: Double) -> Double {
        for k in 0...segment { _ = s.observe(DriveFixtures.fix(DriveFixtures.on(line, segment: k), at: t + Double(k))) }
        return t + Double(segment + 1)
    }

    /// Leaves the line at `t` and stays away until `t + seconds`.
    static func leave(_ s: inout DriveSession, _ line: [Coordinate], segment: Int, at t: Double, for seconds: Double) {
        let off = DriveFixtures.away(from: DriveFixtures.on(line, segment: segment))
        _ = s.observe(DriveFixtures.fix(off, at: t))
        _ = s.observe(DriveFixtures.fix(off, at: t + seconds))
    }

    @Test("T-0361 R6: the fraction driven is the progress vertex's share of the line, k of 5 segments")
    func fractionOnOneLine() {
        var s = Self.session()
        #expect(s.fractionDriven == 0)
        for segment in 0...4 {
            _ = Self.drive(&s, Self.lineA, through: segment, from: 0)
            #expect(abs(s.fractionDriven - Double(segment) / 5) < 1e-12)
        }
    }

    /// The metres along `c` to `vertex`, recomputed here segment by segment (the oracle; not the shipping sum).
    static func length(_ c: [Coordinate], to vertex: Int) -> Double {
        (0..<vertex).reduce(0) { $0 + Geo.distanceMeters(c[$1], c[$1 + 1]) }
    }

    /// rv1-t0361 B1: the shape that tells the old line's progress from the new line's. The new line has FEWER
    /// segments (2) than the old progress (3), and its segments are another length - so the metres read on the new
    /// line for the old progress (RV-A) differ from the old line's, and a mis-read past its end would trap.
    @Test("T-0361 R6: a taken reroute keeps the old line's metres to its progress - 3 of 5 segments, then a shorter 2-segment line with other segment lengths, compared whole")
    func fractionAcrossAReroute() {
        let a = Self.lineA, b = Self.shortB
        #expect(b.count - 1 < 3)
        #expect(abs(Self.length(b, to: 1) - Self.length(a, to: 1)) > 100)
        let before = Self.length(a, to: 3)
        let misread = Self.length(b, to: 2)
        #expect(abs(before / (before + Self.length(b, to: 2)) - misread / (misread + Self.length(b, to: 2))) > 0.1)
        var s = Self.session()
        let t = Self.drive(&s, a, through: 3, from: 0)
        Self.leave(&s, a, segment: 3, at: t, for: 5)
        #expect(s.mode == .rerouting && s.progressSegment == 3)
        #expect(s.fractionDriven == before / Self.length(a, to: 5))
        let taken = s.rerouteArrived(line: b, waypoints: [])
        #expect(taken)
        #expect(s.line == DriveLine(b)! && s.progressSegment == 0 && s.mode == .guiding)
        #expect(s.fractionDriven == before / (before + Self.length(b, to: 2)))
        _ = Self.drive(&s, b, through: 1, from: t + 10)
        #expect(s.progressSegment == 1)
        #expect(s.fractionDriven == (before + Self.length(b, to: 1)) / (before + Self.length(b, to: 2)))
    }

    @Test("T-0361 R6: a refused reroute adds nothing to the metres driven")
    func refusedRerouteKeepsTheFraction() {
        var s = Self.session()
        let t = Self.drive(&s, Self.lineA, through: 2, from: 0)
        Self.leave(&s, Self.lineA, segment: 2, at: t, for: 5)
        let taken = s.rerouteArrived(line: [Self.lineB[0]], waypoints: [])
        #expect(!taken)
        #expect(abs(s.fractionDriven - 2.0 / 5) < 1e-12)
    }

    @Test("T-0361 R6: the meters along a line are the sum of its segments up to the vertex")
    func metersAlong() {
        let line = DriveLine(Self.lineA)!
        let one = Geo.distanceMeters(Self.lineA[0], Self.lineA[1])
        #expect(one > 900)
        for vertex in 0...5 {
            #expect(abs(DriveSession.meters(along: line, to: vertex) - Double(vertex) * one) < 1e-6)
        }
        for vertex in 6...8 {
            #expect(DriveSession.meters(along: line, to: vertex) == DriveSession.meters(along: line, to: 5))
        }
    }

    @Test("T-0361 R6: off-route counts each declaration - not the dwell, not the wait, not a reconnect")
    func offRouteCount() {
        var s = Self.session(online: false)
        #expect(s.offRouteCount == 0)
        var t = Self.drive(&s, Self.lineA, through: 1, from: 0)
        Self.leave(&s, Self.lineA, segment: 1, at: t, for: 4.9)
        #expect(s.offRouteCount == 0)
        _ = s.observe(DriveFixtures.fix(DriveFixtures.away(from: DriveFixtures.on(Self.lineA, segment: 1)), at: t + 5))
        #expect(s.mode == .rejoining)
        #expect(s.offRouteCount == 1)
        _ = s.observe(DriveFixtures.fix(DriveFixtures.away(from: DriveFixtures.on(Self.lineA, segment: 1)), at: t + 9))
        let asked = s.connectivity(online: true)
        #expect(asked != nil)
        #expect(s.mode == .rerouting)
        #expect(s.offRouteCount == 1)
        let taken = s.rerouteArrived(line: Self.lineB, waypoints: [])
        #expect(taken)
        t += 20
        t = Self.drive(&s, Self.lineB, through: 0, from: t)
        Self.leave(&s, Self.lineB, segment: 0, at: t, for: 5)
        #expect(s.mode == .rerouting)
        #expect(s.offRouteCount == 2)
        s.rerouteFailed()
        _ = Self.drive(&s, Self.lineB, through: 1, from: t + 10)
        #expect(s.mode == .guiding)
        Self.leave(&s, Self.lineB, segment: 1, at: t + 20, for: 5)
        #expect(s.offRouteCount == 3)
    }
}

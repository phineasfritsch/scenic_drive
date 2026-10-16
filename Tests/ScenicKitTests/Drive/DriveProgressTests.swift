@testable import ScenicKit
import Testing

/// T-0361 R6: what drive_completed / drive_abandoned carry - DriveSession's off-route count and the fraction driven,
/// through the shipping `observe`, `connectivity` and `rerouteArrived`. The lines are along one latitude with a vertex
/// every 0.01 degree, so every segment has the same length and each fraction is a ratio of whole segments.
@Suite("DriveProgressTests")
struct DriveProgressTests {
    static let lineA = DriveFixtures.line(latitude: 34.0, firstLongitude: -118.50, count: 6)
    static let lineB = DriveFixtures.line(latitude: 34.0, firstLongitude: -118.40, count: 4)

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

    @Test("T-0361 R6: a taken reroute keeps the metres already driven - 3 of 5, then 0 of 3 and 2 of 3 on the new line")
    func fractionAcrossAReroute() {
        var s = Self.session()
        let t = Self.drive(&s, Self.lineA, through: 3, from: 0)
        Self.leave(&s, Self.lineA, segment: 3, at: t, for: 5)
        #expect(s.mode == .rerouting)
        #expect(abs(s.fractionDriven - 3.0 / 5) < 1e-12)
        let taken = s.rerouteArrived(line: Self.lineB, waypoints: [])
        #expect(taken)
        #expect(abs(s.fractionDriven - 3.0 / 6) < 1e-12)
        _ = Self.drive(&s, Self.lineB, through: 2, from: t + 10)
        #expect(abs(s.fractionDriven - 5.0 / 6) < 1e-12)
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

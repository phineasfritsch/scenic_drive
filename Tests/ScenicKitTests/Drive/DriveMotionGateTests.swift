@testable import ScenicKit
import Testing

/// T-0317 R6 (P-SAFE-09, the plan's P-SAFE-06 row): above 4.5 m/s the drive shows only the one large action and
/// voice. Every bound of the speed, through the session's own entry point, compared whole; no hysteresis is ruled.
@Suite("DriveMotionGateTests")
struct DriveMotionGateTests {
    static let line = [DriveFixtures.probeStart, DriveFixtures.probeEnd]
    static let onLine = Coordinate(latitude: 0, longitude: 0.005)
    static let away = Coordinate(latitude: 0.002, longitude: 0.005)

    static let rows: [(speed: Double, surface: DriveSurface)] = [
        (0, .full), (-0.0, .full), (Double.leastNonzeroMagnitude, .full), (3, .full),
        ((4.5).nextDown, .full), (4.5, .full), ((4.5).nextUp, .minimal), (30, .minimal),
        (Double.greatestFiniteMagnitude, .minimal), (Double.infinity, .minimal),
        (-Double.leastNonzeroMagnitude, .minimal), (-1, .minimal), (-Double.infinity, .minimal), (Double.nan, .minimal),
    ]

    static func session(online: Bool = true) -> DriveSession {
        DriveSession(line: line, waypoints: [], lambda: 0.5, online: online)!
    }

    @Test("P-SAFE-09: above 4.5 m/s, or at an unknown speed, the drive shows only the one large action and voice")
    func surfaceAtEverySpeedBound() {
        #expect(DriveSurface.motionGateMetersPerSecond == 4.5)
        let seen = Self.rows.map { row -> DriveSurface in
            var s = Self.session()
            _ = s.observe(DriveFixtures.fix(Self.onLine, at: 0, speed: row.speed))
            return s.surface
        }
        #expect(seen == Self.rows.map(\.surface))
        #expect(Self.rows.map { DriveSurface(speedMetersPerSecond: $0.speed) } == Self.rows.map(\.surface))
    }

    @Test("P-SAFE-09: before the first fix the drive shows the minimal surface")
    func minimalBeforeAnyFix() {
        #expect(Self.session().surface == .minimal)
        #expect(Self.session(online: false).surface == .minimal)
    }

    @Test("P-SAFE-09: each fix sets the surface by itself - no hysteresis is ruled")
    func eachFixSetsTheSurface() {
        let speeds: [Double] = [10, 4.5, (4.5).nextUp, 0, 20, -1, 3, (4.5).nextUp, (4.5).nextDown]
        var s = Self.session()
        let seen = speeds.enumerated().map { i, v -> DriveSurface in
            _ = s.observe(DriveFixtures.fix(Self.onLine, at: Double(i), speed: v))
            return s.surface
        }
        #expect(seen == [.minimal, .full, .minimal, .full, .minimal, .minimal, .full, .minimal, .full])
    }

    @Test("P-SAFE-09: the bound is the same off the line, offline in rejoin mode and while a reroute is out")
    func gateHoldsInEveryMode() {
        var rejoining = Self.session(online: false)
        var rerouting = Self.session()
        for t in 0...5 {
            _ = rejoining.observe(DriveFixtures.fix(Self.away, at: Double(t)))
            _ = rerouting.observe(DriveFixtures.fix(Self.away, at: Double(t)))
        }
        #expect(rejoining.mode == .rejoining)
        #expect(rerouting.mode == .rerouting)
        for (speed, surface) in [(4.5, DriveSurface.full), ((4.5).nextUp, .minimal), (0, .full), (.nan, .minimal)] {
            _ = rejoining.observe(DriveFixtures.fix(Self.away, at: 9, speed: speed))
            _ = rerouting.observe(DriveFixtures.fix(Self.away, at: 9, speed: speed))
            #expect(rejoining.surface == surface)
            #expect(rerouting.surface == surface)
        }
    }

    /// Every way a fix is unusable, each one ulp past its bound or not a number.
    static let unusable: [(Coordinate, Double)] = [
        (Coordinate(latitude: .nan, longitude: 0), 1), (Coordinate(latitude: 0, longitude: .infinity), 1),
        (Coordinate(latitude: (90.0).nextUp, longitude: 0), 1), (Coordinate(latitude: 0, longitude: (-180.0).nextDown), 1),
        (onLine, .nan), (onLine, .infinity),
    ]

    @Test("P-SAFE-09: an unusable fix is an unknown speed - the minimal surface, whatever it carries or followed")
    func unusableFixIsMinimal() {
        // Rows: the surface before it (a known 0 m/s or 20 m/s fix) x every unusable kind x the speed it carries.
        for before in [0.0, 20] {
            for (point, time) in Self.unusable {
                for carried in [0.0, 4.5, 20, Double.nan] {
                    var s = Self.session()
                    _ = s.observe(DriveFixtures.fix(Self.onLine, at: 0, speed: before))
                    #expect(s.surface == DriveSurface(speedMetersPerSecond: before))
                    let mode = s.mode
                    #expect(s.observe(DriveFixtures.fix(point, at: time, speed: carried)) == nil)
                    #expect(s.surface == .minimal, "before \(before) carried \(carried) at \(point) t \(time)")
                    #expect(s.mode == mode)
                }
            }
        }
    }
}

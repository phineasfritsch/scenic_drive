@testable import ScenicKit
import Testing

/// T-0317 R3/R5: the off-route bounds (50 m exact, 5 s exact) and the online/offline request counts, every request
/// compared WHOLE against a RerouteRequest typed here.
@Suite("DriveSessionTests")
struct DriveSessionTests {
    static let start = DriveFixtures.probeStart
    static let end = DriveFixtures.probeEnd
    static let onLine = Coordinate(latitude: 0, longitude: 0.005)
    static let away = Coordinate(latitude: 0.002, longitude: 0.005)
    static let lambda = 0.5

    static func session(online: Bool = true) -> DriveSession {
        DriveSession(line: [start, end], waypoints: [], lambda: lambda, online: online)!
    }

    static func request(from origin: Coordinate) -> RerouteRequest {
        RerouteRequest(origin: origin, remainingWaypoints: [], firstRemainingWaypoint: 0, destination: end,
                       lambda: lambda)
    }

    static func fix(_ point: Coordinate, _ t: Double) -> DriveFix { DriveFixtures.fix(point, at: t) }

    @Test("P-NAV-01: 50 m exactly is on the line; the smallest distance above 50 m is away")
    func awayThresholdIsExact() throws {
        let at = try #require(DriveFixtures.latitude(measuring: DriveSession.awayThresholdMeters))
        let above = try #require(DriveFixtures.latitude(above: DriveSession.awayThresholdMeters))
        #expect(DriveSession.awayThresholdMeters == 50)
        #expect(DriveFixtures.probeDistance(at) == 50)
        #expect(DriveFixtures.probeDistance(above) > 50)
        let exact = Coordinate(latitude: at, longitude: 0)
        var held = Self.session()
        let asked = (0...60).map { held.observe(Self.fix(exact, Double($0))) }
        #expect(asked.allSatisfy { $0 == nil })
        #expect(held.mode == .guiding)
        let beyond = Coordinate(latitude: above, longitude: 0)
        var left = Self.session()
        let seen = [0.0, 4.0, 5.0].map { left.observe(Self.fix(beyond, $0)) }
        #expect(seen == [nil, nil, Self.request(from: beyond)])
        #expect(left.mode == .rerouting)
    }

    @Test("P-NAV-01: against a north-south segment at latitude 34, 50 m east is on, the next distance up is away, 42 m east is on")
    func eastThresholdAtLatitude34() throws {
        let at = try #require(DriveFixtures.longitude(measuring: DriveSession.awayThresholdMeters))
        let above = try #require(DriveFixtures.longitude(above: DriveSession.awayThresholdMeters))
        let guess = DriveSession.awayThresholdMeters * DriveFixtures.eastDegreesPerMeter
        #expect(abs(at - guess) <= 256 * guess.ulp)
        #expect(DriveFixtures.eastDistance(at) == 50)
        #expect(DriveFixtures.eastDistance(above) > 50)
        let start = DriveFixtures.northStart, end = DriveFixtures.northEnd
        func north() -> DriveSession { DriveSession(line: [start, end], waypoints: [], lambda: Self.lambda, online: true)! }
        // 42 m east: a missing cosine measures it 42 / cos(34 deg) ~ 50.7 m, away.
        for east in [at, 42 * DriveFixtures.eastDegreesPerMeter] {
            var held = north()
            let fix = Coordinate(latitude: 34, longitude: east)
            let asked = (0...60).map { held.observe(Self.fix(fix, Double($0))) }
            #expect(asked.allSatisfy { $0 == nil }, "east \(east)")
            #expect(held.mode == .guiding)
        }
        let beyond = Coordinate(latitude: 34, longitude: above)
        var left = north()
        let seen = [0.0, (5.0).nextDown, 5.0].map { left.observe(Self.fix(beyond, $0)) }
        #expect(seen == [nil, nil, RerouteRequest(origin: beyond, remainingWaypoints: [], firstRemainingWaypoint: 0,
                                                  destination: end, lambda: Self.lambda)])
        #expect(left.mode == .rerouting)
    }

    @Test("P-NAV-01: off-route needs 5 s away exactly; one ulp less is not; an on-line fix restarts the dwell")
    func dwellBoundIsExact() {
        #expect(DriveSession.offRouteDwellSeconds == 5)
        var s = Self.session()
        let seen = [0.0, (5.0).nextDown, 5.0].map { s.observe(Self.fix(Self.away, $0)) }
        #expect(seen == [nil, nil, Self.request(from: Self.away)])
        var r = Self.session()
        let steps: [(Coordinate, Double)] = [(Self.away, 0), (Self.away, 4), (Self.onLine, 4.5), (Self.away, 5),
                                             (Self.away, (10.0).nextDown), (Self.away, 10)]
        let restarted = steps.map { r.observe(Self.fix($0.0, $0.1)) }
        #expect(restarted == [nil, nil, nil, nil, nil, Self.request(from: Self.away)])
    }

    @Test("P-NAV-01: online off-route asks exactly once; nothing more while the reroute is out")
    func reroutingAsksOnce() {
        var s = Self.session()
        let asked = (0...60).map { s.observe(Self.fix(Self.away, Double($0))) }
        #expect(asked[5] == Self.request(from: Self.away))
        #expect(asked.compactMap { $0 } == [Self.request(from: Self.away)])
        #expect(s.connectivity(online: true) == nil)
        #expect(s.mode == .rerouting)
    }

    @Test("P-NAV-01: connectivity lost while a reroute is out is rejoin mode; the next online edge asks exactly once")
    func lostConnectionWhileReroutingRejoins() {
        var guiding = Self.session()
        _ = guiding.observe(Self.fix(Self.onLine, 0))
        #expect(guiding.connectivity(online: false) == nil)
        #expect(guiding.mode == .guiding)
        var s = Self.session()
        let asked = (0...5).map { s.observe(Self.fix(Self.away, Double($0))) }
        #expect(asked.compactMap { $0 } == [Self.request(from: Self.away)])
        #expect(s.connectivity(online: false) == nil)
        #expect(s.mode == .rejoining)
        let quiet = (6...30).map { s.observe(Self.fix(Self.away, Double($0))) } + [s.connectivity(online: false)]
        #expect(quiet.allSatisfy { $0 == nil })
        #expect(s.mode == .rejoining)
        let latest = Coordinate(latitude: 0.004, longitude: 0.001)
        _ = s.observe(Self.fix(latest, 31))
        #expect([s.connectivity(online: true), s.connectivity(online: true)] == [Self.request(from: latest), nil])
        #expect(s.mode == .rerouting)
    }

    @Test("P-NAV-01: offline off-route is rejoin mode with zero requests, for as long as it lasts")
    func offlineRejoinsWithZeroRequests() {
        var s = Self.session(online: false)
        let first = (0...120).map { s.observe(Self.fix(Self.away, Double($0))) }
        #expect(first.allSatisfy { $0 == nil })
        #expect(s.mode == .rejoining)
        #expect(s.observe(Self.fix(Self.onLine, 121)) == nil)
        #expect(s.mode == .guiding)
        let again = (122...200).map { s.observe(Self.fix(Self.away, Double($0))) }
        #expect(again.allSatisfy { $0 == nil })
        #expect(s.mode == .rejoining)
        #expect(s.connectivity(online: false) == nil)
        #expect(s.mode == .rejoining)
    }

    @Test("P-NAV-01: back online from rejoin mode asks exactly once, from the latest fix")
    func backOnlineAsksOnce() {
        var s = Self.session(online: false)
        for t in 0...10 { _ = s.observe(Self.fix(Self.away, Double(t))) }
        let latest = Coordinate(latitude: 0.003, longitude: 0.006)
        #expect(s.observe(Self.fix(latest, 11)) == nil)
        #expect(s.connectivity(online: false) == nil)
        #expect(s.connectivity(online: true) == Self.request(from: latest))
        #expect(s.mode == .rerouting)
        let after = [s.connectivity(online: true)]
            + (12...40).map { s.observe(Self.fix(Self.away, Double($0))) }
        #expect(after.allSatisfy { $0 == nil })
    }

    @Test("P-NAV-01: back online while guiding asks nothing")
    func backOnlineWhileGuidingAsksNothing() {
        var s = Self.session(online: false)
        #expect(s.observe(Self.fix(Self.onLine, 0)) == nil)
        #expect(s.connectivity(online: true) == nil)
        #expect(s.mode == .guiding)
        #expect(s.isOnline)
    }

    @Test("P-NAV-01: a failed reroute is rejoin mode, not retried until the next offline-to-online edge")
    func failedRerouteRejoins() {
        var s = Self.session()
        let asked = (0...5).map { s.observe(Self.fix(Self.away, Double($0))) }
        #expect(asked.compactMap { $0 } == [Self.request(from: Self.away)])
        s.rerouteFailed()
        #expect(s.mode == .rejoining)
        let quiet = (6...30).map { s.observe(Self.fix(Self.away, Double($0))) } + [s.connectivity(online: true)]
        #expect(quiet.allSatisfy { $0 == nil })
        let latest = Coordinate(latitude: 0.004, longitude: 0.001)
        _ = s.observe(Self.fix(latest, 31))
        #expect(s.connectivity(online: false) == nil)
        #expect(s.connectivity(online: true) == Self.request(from: latest))
        #expect(s.mode == .rerouting)
    }

    @Test("a fix that is not a real position or a real time changes nothing; each bound itself is a fix")
    func unusableFixIsIgnored() {
        var s = Self.session()
        for t in 0...2 { _ = s.observe(Self.fix(Self.away, Double(t))) }
        let before = s
        let bad = [DriveFixtures.fix(Coordinate(latitude: .nan, longitude: 0), at: 9),
                   DriveFixtures.fix(Coordinate(latitude: 0, longitude: .infinity), at: 9),
                   DriveFixtures.fix(Coordinate(latitude: (90.0).nextUp, longitude: 0), at: 9),
                   DriveFixtures.fix(Coordinate(latitude: (-90.0).nextDown, longitude: 0), at: 9),
                   DriveFixtures.fix(Coordinate(latitude: 0, longitude: (180.0).nextUp), at: 9),
                   DriveFixtures.fix(Coordinate(latitude: 0, longitude: (-180.0).nextDown), at: 9),
                   DriveFixtures.fix(Self.away, at: .nan), DriveFixtures.fix(Self.away, at: .infinity)]
        for b in bad {
            #expect(s.observe(b) == nil)
            #expect(s == before)
        }
        let edges = [Coordinate(latitude: 90, longitude: 0), Coordinate(latitude: -90, longitude: 0),
                     Coordinate(latitude: 0, longitude: 180), Coordinate(latitude: 0, longitude: -180)]
        for e in edges {
            var c = before
            #expect(c.observe(DriveFixtures.fix(e, at: 9)) == Self.request(from: e))
        }
    }
}

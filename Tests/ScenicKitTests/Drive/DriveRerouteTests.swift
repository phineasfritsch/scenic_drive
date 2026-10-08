@testable import ScenicKit
import Testing

/// T-0317 R4 (P-NAV-01): what a reroute asks for - exactly the pins not yet passed, in order, and the plan's own
/// lambda - over TWO variants whose expected requests differ in every row (memory table-rows-as-functions-of-input),
/// each compared WHOLE (memory full-equality-oracle).
@Suite("DriveRerouteTests")
struct DriveRerouteTests {
    struct Variant {
        let line: [Coordinate]
        let pinVertices: [Int]
        let lambda: Double
        var pins: [Coordinate] { pinVertices.map { line[$0] } }
    }

    static let variantA = Variant(line: DriveFixtures.line(latitude: 34.0, firstLongitude: -118.50, count: 6),
                                  pinVertices: [1, 3], lambda: 0.35)
    static let variantB = Variant(line: DriveFixtures.line(latitude: 34.2, firstLongitude: -118.70, count: 6),
                                  pinVertices: [2, 3, 4], lambda: 0.8)

    /// (the last segment driven on the line, pins passed in A, pins passed in B). A pin at vertex v is passed once
    /// the driver is on segment v - the row with the driver on the pin's own segment is the bound.
    static let rows: [(segment: Int, passedA: Int, passedB: Int)] = [
        (0, 0, 0), (1, 1, 0), (2, 1, 1), (3, 2, 2), (4, 2, 3),
    ]

    static func session(_ v: Variant, online: Bool = true) -> DriveSession {
        DriveSession(line: v.line, waypoints: v.pins, lambda: v.lambda, online: online)!
    }

    static func expected(_ v: Variant, passed: Int, from origin: Coordinate, lambda: Double? = nil) -> RerouteRequest {
        RerouteRequest(origin: origin, remainingWaypoints: Array(v.pins[passed...]), firstRemainingWaypoint: passed,
                       destination: v.line[v.line.count - 1], lambda: lambda ?? v.lambda)
    }

    /// Drive segments 0...segment on the line, then leave it for 5 s: the request the session asks for.
    static func drive(_ s: inout DriveSession, line: [Coordinate], through segment: Int) -> (RerouteRequest?, Coordinate) {
        for k in 0...segment { _ = s.observe(DriveFixtures.fix(DriveFixtures.on(line, segment: k), at: Double(k))) }
        let off = DriveFixtures.away(from: DriveFixtures.on(line, segment: segment))
        let t = Double(segment + 1)
        #expect(s.observe(DriveFixtures.fix(off, at: t)) == nil)
        return (s.observe(DriveFixtures.fix(off, at: t + 5)), off)
    }

    @Test("P-NAV-01: the reroute carries exactly the pins not yet passed and the same lambda, over both variants")
    func rerouteCarriesRemainingPinsAndLambda() {
        for row in Self.rows {
            for (v, passed) in [(Self.variantA, row.passedA), (Self.variantB, row.passedB)] {
                var s = Self.session(v)
                let (asked, off) = Self.drive(&s, line: v.line, through: row.segment)
                #expect(asked == Self.expected(v, passed: passed, from: off), "segment \(row.segment)")
                #expect(s.mode == .rerouting)
            }
        }
    }

    @Test("P-NAV-01: offline, the same drive asks nothing; back online it asks for the same remaining pins")
    func offlineThenOnlineCarriesRemainingPins() {
        for row in Self.rows {
            for (v, passed) in [(Self.variantA, row.passedA), (Self.variantB, row.passedB)] {
                var s = Self.session(v, online: false)
                let (asked, off) = Self.drive(&s, line: v.line, through: row.segment)
                #expect(asked == nil)
                #expect(s.mode == .rejoining)
                #expect(s.connectivity(online: true) == Self.expected(v, passed: passed, from: off))
            }
        }
    }

    @Test("no row passes by ignoring its variant: every row's two expected requests differ, and so do the columns")
    func noRowIgnoresItsVariant() {
        let origin = Coordinate(latitude: 34.1, longitude: -118.6)
        for row in Self.rows {
            #expect(Self.expected(Self.variantA, passed: row.passedA, from: origin)
                    != Self.expected(Self.variantB, passed: row.passedB, from: origin))
        }
        #expect(Self.rows.map(\.passedA) != Self.rows.map(\.passedB))
        #expect(Self.variantA.lambda != Self.variantB.lambda)
    }

    @Test("P-NAV-01: a landed reroute replaces the line and pins and keeps the lambda; the next reroute carries them")
    func arrivalReplacesLineKeepsLambda() {
        let a = Self.variantA, b = Self.variantB
        var guiding = Self.session(a)
        let fresh = guiding
        #expect(guiding.rerouteArrived(line: b.line, waypoints: b.pins) == false)
        #expect(guiding == fresh)
        var s = Self.session(a)
        let (asked, _) = Self.drive(&s, line: a.line, through: 2)
        #expect(asked != nil)
        let landed = s.rerouteArrived(line: b.line, waypoints: b.pins)
        #expect(landed)
        #expect(s.mode == .guiding)
        #expect(s.line.coordinates == b.line)
        #expect(s.waypoints == b.pins)
        #expect(s.lambda == a.lambda)
        #expect(s.progressSegment == 0)
        let (next, off) = Self.drive(&s, line: b.line, through: 3)
        #expect(next == Self.expected(b, passed: 2, from: off, lambda: a.lambda))
    }

    @Test("P-NAV-01: an unusable reroute reply is a failure - rejoin mode, line and pins kept")
    func unusableArrivalRejoins() {
        let a = Self.variantA, b = Self.variantB
        var s = Self.session(a)
        _ = Self.drive(&s, line: a.line, through: 1)
        #expect(s.rerouteArrived(line: b.line, waypoints: [b.line[3], b.line[2]]) == false)
        #expect(s.mode == .rejoining)
        #expect(s.line.coordinates == a.line)
        #expect(s.waypoints == a.pins)
    }

    @Test("a session is built only over a real line whose pins are its vertices, in order, with a finite lambda")
    func pinsMustBeVerticesInOrder() {
        let v = Self.variantA, line = v.line
        #expect(DriveSession(line: line, waypoints: v.pins, lambda: v.lambda, online: true) != nil)
        #expect(DriveSession(line: line, waypoints: [], lambda: v.lambda, online: true) != nil)
        #expect(DriveSession(line: line, waypoints: [line[5]], lambda: v.lambda, online: true) != nil)
        #expect(DriveSession(line: line, waypoints: [line[3], line[1]], lambda: v.lambda, online: true) == nil)
        #expect(DriveSession(line: line, waypoints: [line[1], line[1]], lambda: v.lambda, online: true) == nil)
        let offLine = Coordinate(latitude: 34.0005, longitude: -118.49)
        #expect(DriveSession(line: line, waypoints: [offLine], lambda: v.lambda, online: true) == nil)
        #expect(DriveSession(line: [line[0]], waypoints: [], lambda: v.lambda, online: true) == nil)
        #expect(DriveSession(line: line, waypoints: v.pins, lambda: .nan, online: true) == nil)
        #expect(DriveSession(line: line, waypoints: v.pins, lambda: .infinity, online: true) == nil)
        let bent = [line[0], Coordinate(latitude: (90.0).nextUp, longitude: 0)]
        #expect(DriveSession(line: bent, waypoints: [], lambda: v.lambda, online: true) == nil)
        let notANumber = [line[0], Coordinate(latitude: 34, longitude: .nan)]
        #expect(DriveSession(line: notANumber, waypoints: [], lambda: v.lambda, online: true) == nil)
    }

    @Test("P-NAV-01: a loop's closing leg beside its start does not count the pins as passed")
    func loopClosingLegDoesNotJumpProgress() {
        let loop = [Coordinate(latitude: 34.0, longitude: -118.50), Coordinate(latitude: 34.0, longitude: -118.49),
                    Coordinate(latitude: 34.01, longitude: -118.49), Coordinate(latitude: 34.01, longitude: -118.50),
                    Coordinate(latitude: 34.0, longitude: -118.50)]
        let pins = [loop[1], loop[2]]
        var s = DriveSession(line: loop, waypoints: pins, lambda: 0.4, online: true)!
        let nearStart = Coordinate(latitude: 34.0001, longitude: -118.4999)
        let line = DriveLine(loop)!
        #expect(line.distanceMeters(from: nearStart, toSegment: 3) < line.distanceMeters(from: nearStart, toSegment: 0))
        _ = s.observe(DriveFixtures.fix(nearStart, at: 0))
        #expect(s.progressSegment == 0)
        let off = Coordinate(latitude: 33.997, longitude: -118.495)
        _ = s.observe(DriveFixtures.fix(off, at: 1))
        let asked = s.observe(DriveFixtures.fix(off, at: 6))
        #expect(asked == RerouteRequest(origin: off, remainingWaypoints: pins, firstRemainingWaypoint: 0,
                                        destination: loop[4], lambda: 0.4))
    }
}

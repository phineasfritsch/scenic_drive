import Foundation
import Testing
@testable import ScenicKit

/// T-0325 R3: a drive through the shipped DriveSession, observed by CorridorClock after every fix; each row's answer
/// is the learner's WHOLE slot table, written out per row.
@Suite("completed corridor edges teach the learner (T-0325)") struct CorridorClockTests {
    static let utc = TimeZone(secondsFromGMT: 0)!
    /// Monday 2026-10-05 08:59:00Z: the first edge is entered in hour 8, the rest in hour 9.
    static let start = Date(timeIntervalSince1970: 1_791_190_740)
    static let v = CorridorRouteTests.v
    static let c = CorridorRouteTests.c
    /// Optional so a refused route fails the tests by name instead of trapping the run.
    static let route = CorridorRoute(route: v, timeRuns: CorridorRouteTests.runs)
    static let far = Coordinate(latitude: 34.2, longitude: -118.9)
    /// A reroute's line: from off the route back onto the plan's vertices 2, 3 and 4.
    static let rejoining = [far, Coordinate(latitude: 34.3, longitude: -118.8), v[2], v[3], v[4]]

    /// A point `fraction` of the way along segment `segment`.
    static func on(_ segment: Int, _ fraction: Double) -> Coordinate {
        let a = v[segment], b = v[segment + 1]
        return Coordinate(latitude: a.latitude + fraction * (b.latitude - a.latitude),
                          longitude: a.longitude + fraction * (b.longitude - a.longitude))
    }

    enum Step {
        case fix(Coordinate, TimeInterval)
        case reroute([Coordinate])
    }

    /// Drives `steps` through a fresh session and clock; the learner after the last step.
    static func drive(_ steps: [Step], online: Bool = false,
                      into speeds: LearnedCorridorSpeeds? = nil) -> LearnedCorridorSpeeds {
        var speeds = speeds ?? LearnedCorridorSpeeds(timeZone: utc)
        guard let route else {
            Issue.record("the reference route is refused")
            return speeds
        }
        var session = DriveSession(line: v, waypoints: [], lambda: 0, online: online)!
        var clock = CorridorClock(route: route)
        for step in steps {
            switch step {
            case let .fix(at, t):
                _ = session.observe(DriveFix(coordinate: at, speedMetersPerSecond: 20, timestamp: t))
                clock.observe(session, at: start.addingTimeInterval(t), into: &speeds)
            case let .reroute(line):
                let taken = session.rerouteArrived(line: line, waypoints: [])
                #expect(taken)
            }
        }
        return speeds
    }

    static func slot(_ edge: Int, _ hour: Int) -> CorridorSlot {
        CorridorSlot(cell: c[edge], hour: HourOfWeek(hour)!)
    }

    /// Edge g's slot after one clean drive: free flow 80 / 90 / 40 / 100 s over actual 100 / 150 / 50 / 100 s.
    static let taught: [Int: (CorridorSlot, CorridorRatio)] = [
        0: (slot(0, 8), CorridorRatio(ratio: 0.8, samples: 1)), 1: (slot(1, 9), CorridorRatio(ratio: 0.6, samples: 1)),
        2: (slot(2, 9), CorridorRatio(ratio: 0.8, samples: 1)), 3: (slot(3, 9), CorridorRatio(ratio: 1.0, samples: 1)),
    ]

    static func slots(_ edges: [Int]) -> [CorridorSlot: CorridorRatio] {
        Dictionary(uniqueKeysWithValues: edges.map { taught[$0]! })
    }

    static let f0 = Step.fix(on(0, 0.5), 0), f1 = Step.fix(on(1, 0.5), 100), f2 = Step.fix(on(2, 0.5), 250)
    static let f3 = Step.fix(on(3, 0.5), 300), arrive = Step.fix(v[4], 400)

    /// The arrival bound: 45 m short of the destination along the last segment arrives, 55 m short does not.
    static func short(_ meters: Double) -> Coordinate {
        on(3, 1 - meters / Geo.distanceMeters(v[3], v[4]))
    }

    @Test("a clean drive teaches every edge once; a skip, a detour, a late start, no arrival and a reroute do not")
    func transitionTable() {
        let off1 = Step.fix(Self.far, 150), back1 = Step.fix(Self.on(1, 0.6), 200)
        let rows: [(String, [Step], Bool, [Int])] = [
            ("clean", [Self.f0, Self.f1, Self.f2, Self.f3, Self.arrive], false, [0, 1, 2, 3]),
            ("edge 2 skipped", [Self.f0, Self.f1, Self.f3, Self.arrive], false, [0]),
            ("off the line inside edge 1", [Self.f0, Self.f1, off1, back1, Self.f2, Self.f3, Self.arrive], false,
             [0, 2, 3]),
            ("first fix in edge 1", [Self.f1, Self.f2, Self.f3, Self.arrive], false, [2, 3]),
            ("never arrives", [Self.f0, Self.f1, Self.f2, Self.f3], false, [0, 1, 2]),
            ("arrives 45 m short", [Self.f0, Self.f1, Self.f2, Self.f3, .fix(Self.short(45), 400)], false,
             [0, 1, 2, 3]),
            ("stops 55 m short", [Self.f0, Self.f1, Self.f2, Self.f3, .fix(Self.short(55), 400)], false, [0, 1, 2]),
            ("rerouted after edge 0", [Self.f0, Self.f1, .fix(Self.far, 110), .fix(Self.far, 116),
                                       .reroute([Self.far, Self.v[4]]), .fix(Self.on(2, 0.5), 250), Self.f3,
                                       Self.arrive], true, [0]),
            // pre-review M56: a reroute whose line rejoins the plan's last three vertices, five vertices like it -
            // read against the plan's edges it would teach edge 3 on arrival; after a reroute nothing is taught.
            ("rerouted onto a line that rejoins the plan", [Self.f0, Self.f1, .fix(Self.far, 110),
                                                            .fix(Self.far, 116), .reroute(Self.rejoining),
                                                            .fix(Self.on(2, 0.5), 250), Self.f3, Self.arrive],
             true, [0]),
            // pre-review M51: off the line in edge 1, back on it already in edge 2 - edge 2's entry was not seen.
            ("off the line in edge 1, back on it in edge 2", [Self.f0, Self.f1, off1, Self.f2, Self.f3, Self.arrive],
             false, [0, 3]),
            ("no fix at all", [], false, []),
        ]
        for (name, steps, online, edges) in rows {
            #expect(Self.drive(steps, online: online).slots == Self.slots(edges), "\(name)")
        }
        #expect(Geo.distanceMeters(Self.short(45), Self.v[4]) < DriveSession.awayThresholdMeters)
        #expect(Geo.distanceMeters(Self.short(55), Self.v[4]) > DriveSession.awayThresholdMeters)
    }

    @Test("a fix after arrival teaches nothing more, and observe answers how many edges each fix taught")
    func countsAndFinish() {
        var speeds = LearnedCorridorSpeeds(timeZone: Self.utc)
        var session = DriveSession(line: Self.v, waypoints: [], lambda: 0, online: false)!
        guard let route = Self.route else {
            Issue.record("the reference route is refused")
            return
        }
        var clock = CorridorClock(route: route)
        var counts: [Int] = []
        for (at, t) in [(Self.on(0, 0.5), 0.0), (Self.on(1, 0.5), 100), (Self.on(2, 0.5), 250), (Self.on(3, 0.5), 300),
                        (Self.v[4], 400), (Self.v[4], 500)] {
            _ = session.observe(DriveFix(coordinate: at, speedMetersPerSecond: 20, timestamp: t))
            counts.append(clock.observe(session, at: Self.start.addingTimeInterval(t), into: &speeds))
        }
        #expect(counts == [0, 1, 1, 1, 1, 0])
        #expect(speeds.slots == Self.slots([0, 1, 2, 3]))
    }
}

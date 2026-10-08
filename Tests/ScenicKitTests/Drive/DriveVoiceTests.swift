@testable import ScenicKit
import Foundation
import Testing

/// T-0329 (P-SAFE-09's voice half): what the drive says and when, compared WHOLE - the mode-change table over every
/// pair, the leg cue over every bound on both kinds of leg, and scenarios through DriveSession + DriveVoice the way
/// NavAdapter calls them, one whole [String] per input.
@Suite("DriveVoiceTests")
struct DriveVoiceTests {
    static let next = "Your next scenic stop is coming up."
    static let destination = "Your destination is coming up."
    static let arrived = "You have arrived. Take your time."
    static let leftOnline = "You left the route. Finding a new way."
    static let leftOffline = "You left the route and are offline. Head back to it."
    static let newWay = "Here is a new way."
    static let noNewWay = "No new way for now. Head back to your route."
    static let back = "You are back on your route."

    /// Typed, never derived from the type under test: one row per (from, to) pair.
    static let transitions: [(from: DriveMode, to: DriveMode, said: String?)] = [
        (.guiding, .guiding, nil), (.guiding, .rerouting, leftOnline), (.guiding, .rejoining, leftOffline),
        (.rerouting, .guiding, newWay), (.rerouting, .rerouting, nil), (.rerouting, .rejoining, noNewWay),
        (.rejoining, .guiding, back), (.rejoining, .rerouting, nil), (.rejoining, .rejoining, nil),
    ]

    /// Each bound just outside, exactly on, and just inside, plus the non-finite values; the expected line is a
    /// FUNCTION of the variant (a pin's leg or the last leg).
    static let cues: [(meters: Double, said: @Sendable (Bool) -> String?)] = [
        (0, { $0 ? arrived : next }),
        (30.0.nextDown, { $0 ? arrived : next }),
        (30, { $0 ? arrived : next }),
        (30.0.nextUp, { $0 ? destination : next }),
        (400.0.nextDown, { $0 ? destination : next }),
        (400, { $0 ? destination : next }),
        (400.0.nextUp, { _ in nil }),
        (1000, { _ in nil }),
        (.infinity, { _ in nil }),
        (.nan, { _ in nil }),
    ]

    @Test("P-SAFE-09: every mode change says the typed line or nothing, compared whole")
    func everyTransition() {
        for from in DriveMode.allCases {
            for to in DriveMode.allCases {
                let row = Self.transitions.first { $0.from == from && $0.to == to }
                #expect(row != nil, "\(from) -> \(to) has no row")
                #expect(DriveVoice.transition(from: from, to: to) == row?.said, "\(from) -> \(to)")
            }
        }
    }

    @Test("P-SAFE-09: the transition table is the cross product, each pair once")
    func transitionTableIsTheCrossProduct() {
        #expect(DriveMode.allCases.count == 3)
        #expect(Set(Self.transitions.map { "\($0.from) \($0.to)" }).count == 9 && Self.transitions.count == 9)
    }

    @Test("P-SAFE-09: the leg cue at every distance bound, on a pin's leg and on the last leg, compared whole")
    func cueAtEveryBound() {
        for row in Self.cues {
            for last in [false, true] {
                #expect(DriveVoice.cue(metersToLegEnd: row.meters, lastLeg: last) == row.said(last),
                        "\(row.meters) m, last leg \(last)")
            }
        }
        #expect(DriveVoice.approachMeters == 400 && DriveVoice.arrivalMeters == 30)
    }

    @Test("P-SAFE-09: every cue row within 400 m depends on the kind of leg; none beyond it speaks")
    func cueRowsAreFunctionsOfTheLeg() {
        for row in Self.cues {
            if row.meters <= 400 {
                #expect(row.said(false) != row.said(true), "\(row.meters) m ignores the kind of leg")
            } else {
                #expect(row.said(false) == nil && row.said(true) == nil, "\(row.meters) m")
            }
        }
    }

    // MARK: through the session, as NavAdapter calls it

    /// Five vertices east along the equator, ~1112 m apart, a pin at vertex 2: two legs.
    static let line = DriveFixtures.line(latitude: 0, firstLongitude: 0, count: 5)
    static func east(_ longitude: Double, north: Double = 0) -> Coordinate {
        Coordinate(latitude: north, longitude: longitude)
    }

    /// Feeds each fix (or a closure acting on the session) and returns what was said after each, whole.
    static func run(_ session: inout DriveSession, _ steps: [(inout DriveSession) -> Void]) -> [[String]] {
        var voice = DriveVoice(session: session)
        return steps.map { step in
            step(&session)
            return voice.utterances(after: session)
        }
    }

    static func at(_ point: Coordinate, _ t: Double) -> (inout DriveSession) -> Void {
        { _ = $0.observe(DriveFixtures.fix(point, at: t)) }
    }

    @Test("P-SAFE-09: the leg end is the next pin past the progress, else the last vertex, measured along the line")
    func legEndAlongTheLine() throws {
        let v = Self.line
        var session = try #require(DriveSession(line: v, waypoints: [v[0], v[2], v[4]], lambda: 0.5, online: true))
        #expect(session.legEnd == nil)
        let cases: [(Coordinate, Int, Double)] = [
            (Self.east(0.003), 2, Geo.distanceMeters(Self.east(0.003), v[1]) + Geo.distanceMeters(v[1], v[2])),
            (Self.east(0.017), 2, Geo.distanceMeters(Self.east(0.017), v[2])),
            (Self.east(0.025), 4, Geo.distanceMeters(Self.east(0.025), v[3]) + Geo.distanceMeters(v[3], v[4])),
            (Self.east(0.039), 4, Geo.distanceMeters(Self.east(0.039), v[4])),
        ]
        for (t, (point, vertex, meters)) in cases.enumerated() {
            _ = session.observe(DriveFixtures.fix(point, at: Double(t)))
            let end = try #require(session.legEnd)
            #expect(end.vertex == vertex && end.meters == meters, "\(point)")
        }
    }

    @Test("P-SAFE-09: a drive says each leg's approach once, the destination's approach, then the arrival - nothing else")
    func aDriveAlongTheLine() throws {
        var session = try #require(DriveSession(line: Self.line, waypoints: [Self.line[2]], lambda: 0.5, online: true))
        let said = Self.run(&session, [
            Self.at(Self.east(0.001), 0), Self.at(Self.east(0.017), 1), Self.at(Self.east(0.018), 2),
            Self.at(Self.east(0.025), 3), Self.at(Self.east(0.037), 4), Self.at(Self.east(0.0398), 5),
            Self.at(Self.east(0.0399), 6),
        ])
        #expect(said == [[], [Self.next], [], [], [Self.destination], [Self.arrived], []])
    }

    @Test("P-SAFE-09: arriving first says only the arrival, and nothing after it")
    func arrivalSupersedesTheApproach() throws {
        let short = Array(Self.line[0...1])
        var session = try #require(DriveSession(line: short, waypoints: [], lambda: 0.5, online: true))
        let said = Self.run(&session, [Self.at(Self.east(0.0099), 0), Self.at(Self.east(0.0095), 1)])
        #expect(said == [[Self.arrived], []])
    }

    @Test("P-SAFE-09: off the route the leg is quiet; leaving, failing and coming back each say their line once")
    func quietOffTheRoute() throws {
        var session = try #require(DriveSession(line: Self.line, waypoints: [Self.line[2]], lambda: 0.5, online: true))
        let near = Self.east(0.018, north: 0.002)
        let said = Self.run(&session, [
            Self.at(Self.east(0.012), 0), Self.at(near, 1), Self.at(near, 6), Self.at(Self.east(0.017), 7),
            { $0.rerouteFailed() }, Self.at(near, 8), Self.at(Self.east(0.018), 9), Self.at(Self.east(0.019), 10),
        ])
        #expect(said == [[], [], [Self.leftOnline], [], [Self.noNewWay], [], [Self.back, Self.next], []])
    }

    @Test("P-SAFE-09: a fix exactly 50 m from the line is on a leg; the next distance above it is on none")
    func legEndOnlyOnTheLine() throws {
        let probe = [DriveFixtures.probeStart, DriveFixtures.probeEnd]
        let onLat = try #require(DriveFixtures.latitude(measuring: 50))
        let offLat = try #require(DriveFixtures.latitude(above: 50))
        var on = try #require(DriveSession(line: probe, waypoints: [], lambda: 0.5, online: true))
        _ = on.observe(DriveFixtures.fix(Coordinate(latitude: onLat, longitude: 0), at: 0))
        let end = try #require(on.legEnd)
        #expect(end.vertex == 1
                && end.meters == Geo.distanceMeters(Coordinate(latitude: onLat, longitude: 0), DriveFixtures.probeEnd))
        var off = try #require(DriveSession(line: probe, waypoints: [], lambda: 0.5, online: true))
        _ = off.observe(DriveFixtures.fix(Coordinate(latitude: offLat, longitude: 0), at: 0))
        #expect(off.legEnd == nil)
    }

    @Test("P-SAFE-09: offline says head back; the reconnect is quiet; a landed reroute is a new line with its own cues")
    func offlineThenANewWay() throws {
        let short = Array(Self.line[0...1])
        var session = try #require(DriveSession(line: short, waypoints: [], lambda: 0.5, online: false))
        let away = Self.east(0.007, north: 0.002)
        let rerouted = [away, Self.east(0.017, north: 0.002)]
        let said = Self.run(&session, [
            Self.at(Self.east(0.007), 0), Self.at(away, 1), Self.at(away, 6),
            { _ = $0.connectivity(online: true) }, { $0.rerouteArrived(line: rerouted, waypoints: []) },
            Self.at(Self.east(0.0135, north: 0.002), 7),
        ])
        #expect(said == [[Self.destination], [], [Self.leftOffline], [], [Self.newWay], [Self.destination]])
    }
}

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
        let away = Self.east(0.006, north: 0.002)
        // What the shipping request makes: from the fix it was asked at to the SAME destination, ~497 m along it.
        let rerouted = [away, short[1]]
        var asked: RerouteRequest?
        let said = Self.run(&session, [
            Self.at(Self.east(0.007), 0), Self.at(away, 1), Self.at(away, 6),
            { asked = $0.connectivity(online: true) }, { $0.rerouteArrived(line: rerouted, waypoints: []) },
            Self.at(Self.east(0.008, north: 0.001), 7), Self.at(Self.east(0.0098, north: 0.0001), 8),
        ])
        #expect(asked?.destination == rerouted.last && rerouted.last == short.last && rerouted != short)
        #expect(said == [[Self.destination], [], [Self.leftOffline], [], [Self.newWay], [Self.destination],
                         [Self.arrived]])
    }

    /// Each cue state the voice can be in before leaving: the longitude it is said at, what is said there, and the
    /// longitude the driver comes back to, still inside that cue's bound. A pin at vertex 2.
    static let cueStates: [(at: Double, said: String, back: Double)] = [
        (0.017, next, 0.018), (0.037, destination, 0.038), (0.0398, arrived, 0.0399),
    ]

    @Test("P-SAFE-09: a mode round trip on the same line repeats no cue - after a pin's approach, the destination's, or the arrival, online or offline")
    func roundTripRepeatsNothing() throws {
        for state in Self.cueStates {
            for online in [true, false] {
                var session = try #require(
                    DriveSession(line: Self.line, waypoints: [Self.line[2]], lambda: 0.5, online: online))
                let away = Self.east(state.back, north: 0.002)
                var steps: [(inout DriveSession) -> Void] = [Self.at(Self.east(state.at), 0), Self.at(away, 1),
                                                             Self.at(away, 6)]
                if online { steps.append { $0.rerouteFailed() } }
                steps.append(Self.at(Self.east(state.back), 7))
                let left: [[String]] = online ? [[Self.leftOnline], [Self.noNewWay]] : [[Self.leftOffline]]
                #expect(Self.run(&session, steps) == [[state.said], []] + left + [[Self.back]],
                        "\(state.said) online \(online)")
            }
        }
    }

    @Test("P-SAFE-09: with a pin at every interior vertex, or none, only the pin's leg says the next stop and only the last says the destination")
    func pinAtEveryVertex() throws {
        let last = Self.line.count - 1
        for pin in [nil] + Array(1..<last) {
            let waypoints = pin.map { [Self.line[$0]] } ?? []
            var session = try #require(DriveSession(line: Self.line, waypoints: waypoints, lambda: 0.5, online: true))
            let steps = (1...last).map { Self.at(Self.east(0.01 * Double($0) - 0.003), Double($0)) }
            let expected: [[String]] = (1...last).map { $0 == pin ? [Self.next] : $0 == last ? [Self.destination] : [] }
            #expect(Self.run(&session, steps) == expected, "pin \(String(describing: pin))")
        }
    }

    /// A landed reroute as the shipping request makes it: to the SAME destination (DriveSession.request sends
    /// line.destination), five vertices with the pin at v2 so the old state's vertex numbers collide; crossed over
    /// which part of the line changed, so no partial "is this a new line" key passes.
    static let reroutes: [(name: String, line: [Coordinate])] = [
        ("the start moved", [east(0, north: 0.002)] + Array(line[1...])),
        ("the middle moved", [line[0], east(0.01, north: 0.0003), line[2], east(0.03, north: 0.0003), line[4]]),
    ]

    @Test("P-SAFE-09: a landed reroute after a pin's approach, the destination's, or the arrival says the new line's cues, online or offline")
    func landedRerouteSaysTheNewLine() throws {
        let (start, middle) = (Self.reroutes[0].line, Self.reroutes[1].line)
        #expect(start[0] != Self.line[0] && Array(start[1...]) == Array(Self.line[1...]))
        #expect(middle.first == Self.line.first && middle.last == Self.line.last && middle != Self.line)
        var before: [(row: String, said: [[String]])] = []
        for reroute in Self.reroutes {
            for state in Self.cueStates {
                for online in [true, false] {
                    var session = try #require(
                        DriveSession(line: Self.line, waypoints: [Self.line[2]], lambda: 0.5, online: online))
                    let away = Self.east(state.at, north: 0.002)
                    var asked: RerouteRequest?
                    var steps: [(inout DriveSession) -> Void] = [Self.at(Self.east(state.at), 0), Self.at(away, 1),
                                                                 { asked = $0.observe(DriveFixtures.fix(away, at: 6)) }]
                    if !online { steps.append { asked = $0.connectivity(online: true) } }
                    let landing = steps.count
                    steps.append { _ = $0.rerouteArrived(line: reroute.line, waypoints: [reroute.line[2]]) }
                    for (t, ahead) in [0.017, 0.037, 0.0398].enumerated() {
                        steps.append(Self.at(Self.east(ahead), Double(7 + t)))
                    }
                    let left: [[String]] = online ? [[Self.leftOnline]] : [[Self.leftOffline], []]
                    let said = Self.run(&session, steps)
                    let row = "\(reroute.name) \(state.said) online \(online)"
                    #expect(asked?.destination == reroute.line.last && reroute.line.last == Self.line.last
                            && reroute.line.count == Self.line.count && reroute.line[2] == Self.line[2], "\(row)")
                    #expect(said == [[state.said], []] + left + [[Self.newWay], [Self.next], [Self.destination],
                                                                 [Self.arrived]], "\(row)")
                    before.append(("\(reroute.name) \(online)", Array(said.prefix(landing))))
                }
            }
        }
        for key in Set(before.map(\.row)) {
            let rows = before.filter { $0.row == key }.map { "\($0.said)" }
            #expect(rows.count == Self.cueStates.count && Set(rows).count == rows.count, "\(key)")
        }
    }

    /// An L: east along the equator to a corner, then north; one leg, no pin.
    static let bent = [Coordinate(latitude: 0, longitude: 0), Coordinate(latitude: 0, longitude: 0.003),
                       Coordinate(latitude: 0.003, longitude: 0.003)]

    @Test("P-SAFE-09: on a bent line the approach is measured along the line - quiet just above 400 m along it, though the crow flies under 400")
    func bentLineMeasuresAlongTheLine() throws {
        let corner = Self.bent[1], end = Self.bent[2]
        let along = { (at: Coordinate) in Geo.distanceMeters(at, corner) + Geo.distanceMeters(corner, end) }
        let above = Self.east(0.00237), below = Self.east(0.00246)
        let bound = DriveVoice.approachMeters
        #expect(along(above) > bound && along(above) < bound + 10 && Geo.distanceMeters(above, end) < bound - 50)
        #expect(along(below) <= bound && along(below) > bound - 15 && Geo.distanceMeters(below, end) < bound - 50)
        var probe = try #require(DriveSession(line: Self.bent, waypoints: [], lambda: 0.5, online: true))
        _ = probe.observe(DriveFixtures.fix(above, at: 0))
        let end2 = try #require(probe.legEnd)
        #expect(end2.vertex == 2 && end2.meters == along(above))
        var session = try #require(DriveSession(line: Self.bent, waypoints: [], lambda: 0.5, online: true))
        let said = Self.run(&session, [
            Self.at(Self.east(0.0005), 0), Self.at(above, 1), Self.at(below, 2),
            Self.at(Coordinate(latitude: 0.0029, longitude: 0.003), 3),
        ])
        #expect(said == [[], [], [Self.destination], [Self.arrived]])
    }
}

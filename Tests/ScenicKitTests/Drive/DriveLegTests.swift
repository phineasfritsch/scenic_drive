@testable import ScenicKit
import Testing

/// T-0321 R4: the steps NavAdapter hands Ferrostar, through the shipping symbol DriveSession.legs. Each expected
/// value is the whole leg list, written out from the line it ranges over.
@Suite("DriveLegTests")
struct DriveLegTests {
    static let line = DriveFixtures.line(latitude: 34.0, firstLongitude: -118.50, count: 6)

    static func legs(pinVertices: [Int]) -> [DriveLeg] {
        DriveSession(line: line, waypoints: pinVertices.map { line[$0] }, lambda: 0.5, online: true)!.legs
    }

    static func leg(_ range: ClosedRange<Int>, _ maneuver: GuidanceManeuver) -> DriveLeg {
        DriveLeg(coordinates: Array(line[range]), maneuver: maneuver)
    }

    @Test("T-0321: the legs cut the line at each inner pin, end at each pin, and the last arrives")
    func innerPinsCut() {
        #expect(Self.legs(pinVertices: [1, 3]) == [Self.leg(0...1, .reachedWaypoint), Self.leg(1...3, .reachedWaypoint),
                                                    Self.leg(3...5, .arrive)])
        #expect(Self.legs(pinVertices: [2]) == [Self.leg(0...2, .reachedWaypoint), Self.leg(2...5, .arrive)])
        #expect(Self.legs(pinVertices: [4]) == [Self.leg(0...4, .reachedWaypoint), Self.leg(4...5, .arrive)])
    }

    @Test("T-0321: no pin, or a pin on the first or last vertex, cuts nothing - no leg is a single point")
    func endPinsCutNothing() {
        let whole = [Self.leg(0...5, .arrive)]
        #expect(Self.legs(pinVertices: []) == whole)
        #expect(Self.legs(pinVertices: [0]) == whole)
        #expect(Self.legs(pinVertices: [5]) == whole)
        #expect(Self.legs(pinVertices: [0, 5]) == whole)
        #expect(Self.legs(pinVertices: [0, 2, 5]) == [Self.leg(0...2, .reachedWaypoint), Self.leg(2...5, .arrive)])
    }

    @Test("T-0321: a landed reroute's legs are cut at its own pins")
    func rerouteLegs() {
        let next = DriveFixtures.line(latitude: 34.1, firstLongitude: -118.60, count: 4)
        var s = DriveSession(line: Self.line, waypoints: [Self.line[1]], lambda: 0.5, online: true)!
        let off = DriveFixtures.away(from: DriveFixtures.on(Self.line, segment: 0))
        _ = s.observe(DriveFixtures.fix(off, at: 0))
        _ = s.observe(DriveFixtures.fix(off, at: 5))
        let r1 = s.rerouteArrived(line: next, waypoints: [next[2]])
        #expect(r1)
        #expect(s.legs == [DriveLeg(coordinates: Array(next[0...2]), maneuver: .reachedWaypoint),
                           DriveLeg(coordinates: Array(next[2...3]), maneuver: .arrive)])
    }

    @Test("T-0321: a leg's length is the sum of Geo's distances between its consecutive vertices")
    func legLength() {
        let leg = Self.leg(0...3, .arrive)
        let expected = Geo.distanceMeters(Self.line[0], Self.line[1]) + Geo.distanceMeters(Self.line[1], Self.line[2])
            + Geo.distanceMeters(Self.line[2], Self.line[3])
        #expect(leg.lengthMeters == expected)
        #expect(Self.leg(4...5, .arrive).lengthMeters == Geo.distanceMeters(Self.line[4], Self.line[5]))
    }
}

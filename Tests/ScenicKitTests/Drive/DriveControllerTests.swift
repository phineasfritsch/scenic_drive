@testable import ScenicKit
import Testing

/// T-0321 R2/R3 (rv2-t0317's recordable 4): the reroute in flight, by ticket. Every expectation is a whole value -
/// the command list, or the whole controller before and after (memory full-equality-oracle).
@Suite("DriveControllerTests")
struct DriveControllerTests {
    static let line = DriveFixtures.line(latitude: 34.0, firstLongitude: -118.50, count: 6)
    static let pins = [line[1], line[3]]
    static let lambda = 0.35
    static let replyLine = DriveFixtures.line(latitude: 34.1, firstLongitude: -118.60, count: 4)
    static let reply = RerouteReply(line: replyLine, waypoints: [replyLine[2]])
    static let start = DriveFixtures.on(line, segment: 0)
    static let off = DriveFixtures.away(from: start)
    static let fixes = [DriveFixtures.fix(start, at: 0), DriveFixtures.fix(off, at: 1), DriveFixtures.fix(off, at: 6)]

    static func session() -> DriveSession {
        DriveSession(line: line, waypoints: pins, lambda: lambda, online: true)!
    }

    /// The request the session asks for from `origin` with no pin passed.
    static func request(from origin: Coordinate) -> RerouteRequest {
        RerouteRequest(origin: origin, remainingWaypoints: pins, firstRemainingWaypoint: 0, destination: line[5],
                       lambda: lambda)
    }

    /// On the line at t=0, away at t=1 and t=6: a controller with reroute ticket 1 out.
    static func leaving() -> DriveController {
        var c = DriveController(session: session())
        for fix in fixes { _ = c.observe(fix) }
        return c
    }

    /// leaving(), then the connection drops and comes back: ticket 1 cancelled, ticket 2 out.
    static func reconnected() -> DriveController {
        var c = leaving()
        let r1 = c.connectivity(online: false)
        #expect(r1 == [.cancel(ticket: 1)])
        let r2 = c.connectivity(online: true)
        #expect(r2 == [.send(request(from: off), ticket: 2)])
        #expect(c.inFlight == 2)
        return c
    }

    @Test("T-0321: every fix reaches the session whole; off-route online is one send under ticket 1")
    func everyFixReachesTheSession() {
        var c = DriveController(session: Self.session())
        var bare = Self.session()
        var commands: [[DriveCommand]] = []
        for fix in Self.fixes {
            commands.append(c.observe(fix))
            _ = bare.observe(fix)
        }
        #expect(commands == [[], [], [.send(Self.request(from: Self.off), ticket: 1)]])
        #expect(c.session == bare)
        #expect(c.inFlight == 1)
        #expect(c.session.mode == .rerouting)
    }

    @Test("T-0321: losing the connection with a reroute out cancels its ticket; with none out it cancels nothing")
    func lostEdgeCancels() {
        var c = Self.leaving()
        let r3 = c.connectivity(online: false)
        #expect(r3 == [.cancel(ticket: 1)])
        #expect(c.inFlight == nil)
        #expect(c.session.mode == .rejoining)
        var idle = DriveController(session: Self.session())
        let r4 = idle.connectivity(online: false)
        #expect(r4 == [])
        #expect(idle.inFlight == nil)
    }

    @Test("T-0321: a late reply from before the drop is dropped; the reconnect's own reply is taken")
    func lateReplyDropped() {
        let c = Self.reconnected()
        var late = c
        let r5 = late.rerouteArrived(ticket: 1, reply: Self.reply)
        #expect(r5 == false)
        #expect(late == c)
        let r6 = late.rerouteArrived(ticket: 2, reply: Self.reply)
        #expect(r6 == true)
        #expect(late.session.line.coordinates == Self.replyLine)
        #expect(late.inFlight == nil)
        #expect(late.session.mode == .guiding)
    }

    @Test("T-0321: a late failure from before the drop is dropped; the reconnect's own failure is rejoin mode")
    func lateFailureDropped() {
        let c = Self.reconnected()
        var late = c
        let r7 = late.rerouteFailed(ticket: 1)
        #expect(r7 == false)
        #expect(late == c)
        let r8 = late.rerouteFailed(ticket: 2)
        #expect(r8 == true)
        #expect(late.inFlight == nil)
        #expect(late.session.mode == .rejoining)
    }

    @Test("T-0321: an answer with nothing in flight changes nothing, and a ticket is answered once")
    func answerWithNothingInFlight() {
        let idle = DriveController(session: Self.session())
        var c = idle
        let r9 = c.rerouteArrived(ticket: 0, reply: Self.reply)
        #expect(r9 == false)
        let r10 = c.rerouteFailed(ticket: 0)
        #expect(r10 == false)
        #expect(c == idle)
        var taken = Self.leaving()
        let r11 = taken.rerouteArrived(ticket: 1, reply: Self.reply)
        #expect(r11 == true)
        let after = taken
        let r12 = taken.rerouteArrived(ticket: 1, reply: Self.reply)
        #expect(r12 == false)
        let r13 = taken.rerouteFailed(ticket: 1)
        #expect(r13 == false)
        #expect(taken == after)
    }

    @Test("T-0321: until T-0319 the sender asks nothing and fails, so an online off-route drive rejoins")
    func senderUntilWireFails() async {
        await #expect(throws: RerouteUnavailable()) {
            _ = try await RerouteUnavailable().reroute(Self.request(from: Self.off))
        }
        var c = Self.leaving()
        let r14 = c.rerouteFailed(ticket: 1)
        #expect(r14 == true)
        #expect(c.session.mode == .rejoining)
    }
}

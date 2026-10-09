@testable import ScenicKit
import Foundation
import Testing

/// T-0328 (rv1-t0328): an answer's line, pins and token are taken together or none. Every row runs the shipping entry
/// point - DriveController under its ticket, as NavAdapter does; the session directly only for the one refusal the
/// controller cannot reach - over {answer token present, nil} x {taken, each refusal}, and compares the whole session
/// after the answer AND the next RerouteRequest it sends, both against values recomputed here from the row's inputs.
@Suite struct DriveTokenTakeTests {
    static let planToken = "0f1e2d3c-4b5a-4968-8776-655443322110"
    static let answerToken = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
    /// The plan: six vertices along 34.05, pins at vertices 1, 2, 3. The answer: five along 34.03, pins at 2 and 3.
    /// From segment 1 the plan's first remaining pin is index 1, the answer's index 0 - so a token sent with the
    /// other plan's pins differs from the right request in its pins, its first pin, its destination and its token.
    static let line = DriveFixtures.line(latitude: 34.05, firstLongitude: -118.70, count: 6)
    static let pins = [line[1], line[2], line[3]]
    static let answerLine = DriveFixtures.line(latitude: 34.03, firstLongitude: -118.70, count: 5)
    static let answerPins = [answerLine[2], answerLine[3]]
    static let tokens: [String?] = [answerToken, nil]

    enum Outcome: CaseIterable {
        case taken, lineNotADriveLine, pinsNotVertices, notRerouting, staleTicket
    }

    /// The session after the answer, whole, and the next request it sends.
    struct State: Equatable {
        let taken: Bool
        let line: [Coordinate]
        let waypoints: [Coordinate]
        let token: String?
        let mode: DriveMode
        let next: [RerouteRequest]
    }

    /// The answer the row hands back: the good one, or one refused for the row's reason, carrying `token`.
    static func reply(_ outcome: Outcome, _ token: String?) -> RerouteReply {
        switch outcome {
        case .lineNotADriveLine: RerouteReply(line: [answerLine[0]], waypoints: answerPins, planToken: token)
        case .pinsNotVertices: RerouteReply(line: answerLine, waypoints: [pins[0]], planToken: token)
        default: RerouteReply(line: answerLine, waypoints: answerPins, planToken: token)
        }
    }

    /// The one request the probe must produce on `line` with `pins`, from segment 1, carrying `token`.
    static func request(_ line: [Coordinate], _ pins: [Coordinate], first: Int, _ token: String?) -> RerouteRequest {
        RerouteRequest(origin: DriveFixtures.away(from: DriveFixtures.on(line, segment: 1)),
                       remainingWaypoints: Array(pins[first...]), firstRemainingWaypoint: first,
                       destination: line[line.count - 1], lambda: 7.75, planToken: token)
    }

    /// What the row must leave, as a function of its outcome and its answer's token.
    static func expected(_ outcome: Outcome, _ token: String?) -> State {
        let kept = request(line, pins, first: 1, planToken)
        switch outcome {
        case .taken:
            return State(taken: true, line: answerLine, waypoints: answerPins, token: token, mode: .guiding,
                         next: [request(answerLine, answerPins, first: 0, token)])
        case .lineNotADriveLine, .pinsNotVertices, .notRerouting:
            return State(taken: false, line: line, waypoints: pins, token: planToken, mode: .rejoining, next: [kept])
        case .staleTicket:
            return State(taken: false, line: line, waypoints: pins, token: planToken, mode: .rerouting, next: [kept])
        }
    }

    /// The next request, by one probe that works from every mode: offline (a reroute out is lost), back on the
    /// current line at segment 1, away for the dwell (rejoin mode, offline), then the online edge asks once.
    static func probe(_ session: DriveSession) -> [RerouteRequest] {
        var s = session
        let on = DriveFixtures.on(s.line.coordinates, segment: 1)
        var asked = [s.connectivity(online: false)]
        asked.append(s.observe(DriveFixtures.fix(on, at: 100)))
        for t in 1...6 { asked.append(s.observe(DriveFixtures.fix(DriveFixtures.away(from: on), at: 100 + Double(t)))) }
        asked.append(s.connectivity(online: true))
        return asked.compactMap { $0 }
    }

    /// One row: the plan drive goes off-route online (ticket 1 out), then the answer arrives as the outcome says.
    static func run(_ outcome: Outcome, _ token: String?) -> State {
        var controller = DriveController(session: DriveSession(line: line, waypoints: pins, lambda: 7.75,
                                                               online: true, planToken: planToken)!)
        let start = DriveFixtures.on(line, segment: 0)
        var sent = controller.observe(DriveFixtures.fix(start, at: 0))
        for t in 1...6 { sent += controller.observe(DriveFixtures.fix(DriveFixtures.away(from: start), at: Double(t))) }
        #expect(sent.count == 1, "the off-route drive sends ticket 1")
        let taken: Bool
        var session: DriveSession
        switch outcome {
        case .notRerouting:
            _ = controller.connectivity(online: false)
            session = controller.session
            taken = session.rerouteArrived(line: reply(outcome, token).line, waypoints: reply(outcome, token).waypoints,
                                           planToken: token)
        case .staleTicket:
            _ = controller.connectivity(online: false)
            #expect(controller.connectivity(online: true).count == 1, "the reconnect sends ticket 2")
            taken = controller.rerouteArrived(ticket: 1, reply: reply(outcome, token))
            session = controller.session
        default:
            taken = controller.rerouteArrived(ticket: 1, reply: reply(outcome, token))
            session = controller.session
        }
        return State(taken: taken, line: session.line.coordinates, waypoints: session.waypoints,
                     token: session.planToken, mode: session.mode, next: probe(session))
    }

    @Test("T-0328: an answer's line, pins and token are taken together or none, whole, and the next request agrees")
    func takenTogetherOrNone() {
        for outcome in Outcome.allCases {
            for token in Self.tokens {
                #expect(Self.run(outcome, token) == Self.expected(outcome, token),
                        "\(outcome), answer token \(token ?? "nil")")
            }
        }
    }

    @Test("T-0328: no take-or-refuse row ignores its token variant, and no refused row could be met by taking it")
    func noRowIgnoresItsTokenVariant() {
        #expect(!Self.tokens.contains(Self.planToken))
        #expect(Set(Self.tokens.map { $0 ?? "" }).count == Self.tokens.count)
        for outcome in Outcome.allCases {
            let rows = Self.tokens.map { Self.expected(outcome, $0) }
            for (token, row) in zip(Self.tokens, rows) {
                // The reply really carries the variant, and the next request's token is the session's.
                #expect(Self.reply(outcome, token).planToken == token)
                #expect(row.next.map(\.planToken) == [row.token])
                if outcome == .taken {
                    #expect(row.token == token && row.next[0].firstRemainingWaypoint == 0)
                } else {
                    #expect(row.token == Self.planToken && row.token != token)
                    #expect(row.next[0].firstRemainingWaypoint == 1)
                }
            }
            // Taken: the variant changes the expectation; refused: it must not, and the plan's state is kept whole.
            #expect((rows[0] != rows[1]) == (outcome == .taken), "\(outcome)")
        }
    }
}

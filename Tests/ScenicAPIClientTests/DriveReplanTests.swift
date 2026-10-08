import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0328: the app reroutes through the plan token. Every case runs the shipping chain NavAdapter runs - fixes into
/// DriveController, each `.send` through PlanRerouter (PlanClient.reroute over a recording transport), each answer
/// back under its ticket - and compares what reached the wire and what the session took WHOLE against values
/// recomputed here from the row's inputs.
@Suite struct DriveReplanTests {
    static let planToken = "0f1e2d3c-4b5a-4968-8776-655443322110"
    static let answerToken = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
    /// Six vertices along latitude 34.05, 0.01 degree apart; the three pins are vertices 1, 2 and 3.
    static let line = (0..<6).map { Coordinate(latitude: 34.05, longitude: -118.70 + Double($0) * 0.01) }
    static let pins = [line[1], line[2], line[3]]
    static let answerLine = [Coordinate(latitude: 34.05, longitude: -118.69),
                             Coordinate(latitude: 34.06, longitude: -118.66),
                             Coordinate(latitude: 34.05, longitude: -118.65)]
    static let answerPins = [answerLine[1]]

    /// Where the driver is last seen on the line (a segment midpoint), the pin index the reroute must name, and the
    /// 2-dp origin longitude the wire must carry for the fix 0.002 deg north and 0.001 deg east of that midpoint.
    struct PinRow { let label: String; let segment: Int; let first: Int; let lon: String }
    static let pinRows = [PinRow(label: "first pin 0", segment: 0, first: 0, lon: "-118.69"),
                          PinRow(label: "first pin last", segment: 2, first: 2, lon: "-118.67"),
                          PinRow(label: "first pin past last", segment: 3, first: 3, lon: "-118.66")]
    static let tokens: [String?] = [planToken, nil]
    /// Where the away fix sits: off the 0.01-degree grid (PlanClient must round it), or ON it, 0.01 deg north at the
    /// row's 2-dp longitude - a fix PlanRequestBody.validated() passes as it is, so with no token a sender that asked
    /// anything at all (a fresh origin-to-place /plan, R5) would reach the wire instead of refusing before it.
    static let grids = [false, true]

    static func midpoint(_ segment: Int) -> Coordinate {
        Coordinate(latitude: 34.05, longitude: -118.70 + Double(segment) * 0.01 + 0.005)
    }

    static func away(_ segment: Int, onGrid: Bool = false) -> Coordinate {
        let lon = midpoint(segment).longitude + 0.001
        return onGrid ? Coordinate(latitude: 34.06, longitude: (lon * 100).rounded() / 100)
            : Coordinate(latitude: 34.052, longitude: lon)
    }

    static func fix(_ point: Coordinate, _ t: Double) -> DriveFix {
        DriveFix(coordinate: point, speedMetersPerSecond: 12, timestamp: t)
    }

    /// The Worker's 200 for a reroute, spelled out: the answer line as [lon, lat] pairs, its one pin, its own token.
    static func reply(token: String? = answerToken, route: [Coordinate] = answerLine,
                      waypoints: [Coordinate] = answerPins) -> PlanHTTPReply {
        let pairs = route.map { "[\($0.longitude),\($0.latitude)]" }.joined(separator: ",")
        let points = waypoints.map { "{\"lat\":\($0.latitude),\"lon\":\($0.longitude)}" }.joined(separator: ",")
        let tokenField = token.map { ",\"plan_token\":\"\($0)\"" } ?? ""
        let body = "{\"route\":{\"coordinates\":[\(pairs)],\"distance_m\":4000},\"eta_s\":900,\"fastest_eta_s\":800,"
            + "\"ceiling_s\":2300,\"budget_s\":1500,\"lambda\":7.75,\"evaluations\":1,\"used_budget\":false,"
            + "\"eta_is_estimate\":true,\"hazards\":[],\"waypoints\":[\(points)],"
            + "\"apple_maps_url\":\"https://maps.apple.com/?saddr=34.05,-118.69\"\(tokenField)}"
        return PlanHTTPReply(status: 200, body: Data(body.utf8))
    }

    /// The one request a reroute may make, recomputed: sorted keys, the origin at 2 dp as typed here.
    static func wire(lat: String = "34.05", lon: String, first: Int, token: String) -> PlanHTTPRequest {
        let body = "{\"budget_minutes\":25,\"destination\":{\"place\":\"42\"},"
            + "\"origin\":{\"lat\":\(lat),\"lon\":\(lon)},"
            + "\"reroute\":{\"first_pin\":\(first),\"token\":\"\(token)\"},\"vehicle\":\"standard\"}"
        return PlanHTTPRequest(url: PlanWire.base.appendingPathComponent("plan"), method: "POST",
                               headers: ["content-type": "application/json", "x-scenic-device": PlanWire.deviceHeader],
                               body: Data(body.utf8))
    }

    /// What the row must produce: the controller's commands, the wire, and the session after the answer.
    struct Expected: Equatable {
        let commands: [DriveCommand]
        let requests: [PlanHTTPRequest]
        let line: [Coordinate]
        let waypoints: [Coordinate]
        let token: String?
        let mode: DriveMode
    }

    static func expected(_ row: PinRow, _ token: String?, onGrid: Bool = false) -> Expected {
        let request = RerouteRequest(origin: away(row.segment, onGrid: onGrid), remainingWaypoints: Array(pins[row.first...]),
                                     firstRemainingWaypoint: row.first, destination: line[5], lambda: 7.75,
                                     planToken: token)
        guard let token else {
            return Expected(commands: [.send(request, ticket: 1)], requests: [], line: line, waypoints: pins,
                            token: nil, mode: .rejoining)
        }
        return Expected(commands: [.send(request, ticket: 1)],
                        requests: [wire(lat: onGrid ? "34.06" : "34.05", lon: row.lon, first: row.first,
                                        token: token)],
                        line: answerLine, waypoints: answerPins, token: answerToken, mode: .guiding)
    }

    static func rerouter(_ transport: CountingPlanTransport) -> PlanRerouter {
        PlanRerouter(client: PlanClient(base: PlanWire.base, transport: transport, installID: PlanWire.install,
                                        accountToken: nil), place: 42, budgetMinutes: 25)
    }

    /// Carries out `commands` as DriveNavigator does: each send through the sender, its answer back under its ticket.
    static func carryOut(_ commands: [DriveCommand], _ controller: inout DriveController,
                         _ sender: PlanRerouter) async {
        for case let .send(request, ticket) in commands {
            do {
                controller.rerouteArrived(ticket: ticket, reply: try await sender.reroute(request))
            } catch {
                controller.rerouteFailed(ticket: ticket)
            }
        }
    }

    /// One row through the shipping chain: on the line at `row.segment`, then away for the 5 s dwell.
    static func run(_ row: PinRow, _ token: String?, onGrid: Bool = false) async -> Expected {
        let transport = CountingPlanTransport(reply: reply())
        var controller = DriveController(session: DriveSession(line: line, waypoints: pins, lambda: 7.75, online: true,
                                                               planToken: token)!)
        var commands = controller.observe(fix(midpoint(row.segment), 0))
        for t in 1...6 { commands += controller.observe(fix(away(row.segment, onGrid: onGrid), Double(t))) }
        await carryOut(commands, &controller, rerouter(transport))
        let session = controller.session
        return Expected(commands: commands, requests: await transport.requests, line: session.line.coordinates,
                        waypoints: session.waypoints, token: session.planToken, mode: session.mode)
    }

    @Test("T-0328: token x first pin - the one 2-dp request and the taken answer, whole; no token, no request")
    func tokenByFirstPin() async {
        for row in Self.pinRows {
            for token in Self.tokens {
                for onGrid in Self.grids {
                    let got = await Self.run(row, token, onGrid: onGrid)
                    #expect(got == Self.expected(row, token, onGrid: onGrid),
                            "\(row.label), token \(token ?? "nil"), on grid \(onGrid)")
                }
            }
        }
    }

    @Test("T-0328: no row ignores its variant - every pin row and every token row expects something different")
    func noRowIgnoresItsVariant() {
        let all = Self.pinRows.flatMap { row in
            Self.tokens.flatMap { token in Self.grids.map { Self.expected(row, token, onGrid: $0) } }
        }
        for (i, a) in all.enumerated() {
            for b in all[(i + 1)...] { #expect(a != b) }
        }
        for row in Self.pinRows {
            #expect(Self.away(row.segment, onGrid: true) == Coordinate(latitude: 34.06, longitude: Double(row.lon)!))
            for onGrid in Self.grids {
                #expect(Self.expected(row, Self.planToken, onGrid: onGrid).requests.count == 1)
                #expect(Self.expected(row, nil, onGrid: onGrid).requests.isEmpty)
            }
        }
    }

    @Test("T-0328: the answer DriveController takes is the Worker's line, pins and token, and the map draws it")
    func answerBecomesTheDrawnLine() async throws {
        let response = try await PlanWire.plan(answering: Self.reply()).outcome.get()
        #expect(PlanRerouter.reply(of: response)
            == RerouteReply(line: Self.answerLine, waypoints: Self.answerPins, planToken: Self.answerToken))
        let untokened = try await PlanWire.plan(answering: Self.reply(token: nil)).outcome.get()
        #expect(PlanRerouter.reply(of: untokened) == RerouteReply(line: Self.answerLine, waypoints: Self.answerPins))
        let transport = CountingPlanTransport(reply: Self.reply())
        var controller = DriveController(session: DriveSession(line: Self.line, waypoints: Self.pins, lambda: 7.75,
                                                               online: true, planToken: Self.planToken)!)
        #expect(DriveDisplay(session: controller.session).line == Self.line)
        var commands = controller.observe(Self.fix(Self.midpoint(0), 0))
        for t in 1...6 { commands += controller.observe(Self.fix(Self.away(0), Double(t))) }
        await Self.carryOut(commands, &controller, Self.rerouter(transport))
        #expect(DriveDisplay(session: controller.session)
            == DriveDisplay(surface: .minimal, mode: .guiding, line: Self.answerLine))
    }

    @Test("T-0328: the offline edge mid-flight cancels; the late answer is dropped by ticket and its token never taken")
    func lateAnswerDroppedByTicket() async {
        let transport = CountingPlanTransport(reply: Self.reply())
        let sender = Self.rerouter(transport)
        var controller = DriveController(session: DriveSession(line: Self.line, waypoints: Self.pins, lambda: 7.75,
                                                               online: true, planToken: Self.planToken)!)
        var first = controller.observe(Self.fix(Self.midpoint(0), 0))
        for t in 1...6 { first += controller.observe(Self.fix(Self.away(0), Double(t))) }
        let asked = Self.expected(Self.pinRows[0], Self.planToken).commands
        #expect(first == asked)
        let dropped = controller.connectivity(online: false)
        #expect(dropped == [.cancel(ticket: 1)])
        guard case let .send(request, _) = first.first, let late = try? await sender.reroute(request) else {
            Issue.record("no send to answer late")
            return
        }
        let taken = controller.rerouteArrived(ticket: 1, reply: late)
        #expect(!taken)
        #expect(controller.session.line.coordinates == Self.line && controller.session.planToken == Self.planToken)
        #expect(controller.session.mode == .rejoining)
        let again = controller.connectivity(online: true)
        let resend = RerouteRequest(origin: Self.away(0), remainingWaypoints: Self.pins, firstRemainingWaypoint: 0,
                                    destination: Self.line[5], lambda: 7.75, planToken: Self.planToken)
        #expect(again == [.send(resend, ticket: 2)])
        await Self.carryOut(again, &controller, sender)
        let one = Self.wire(lon: "-118.69", first: 0, token: Self.planToken)
        #expect(await transport.requests == [one, one])
        #expect(controller.session.line.coordinates == Self.answerLine)
        #expect(controller.session.planToken == Self.answerToken && controller.session.mode == .guiding)
    }

    @Test("T-0328: offline, an off-route drive sends nothing - zero commands, zero requests")
    func offlineSendsNothing() async {
        let transport = CountingPlanTransport(reply: Self.reply())
        var controller = DriveController(session: DriveSession(line: Self.line, waypoints: Self.pins, lambda: 7.75,
                                                               online: false, planToken: Self.planToken)!)
        var commands = controller.observe(Self.fix(Self.midpoint(0), 0))
        for t in 1...6 { commands += controller.observe(Self.fix(Self.away(0), Double(t))) }
        await Self.carryOut(commands, &controller, Self.rerouter(transport))
        #expect(commands.isEmpty)
        #expect(await transport.count == 0)
        #expect(controller.session.mode == .rejoining && controller.session.planToken == Self.planToken)
    }

    @Test("T-0328: the preview keeps /plan's token with the ticket's place and budget, only when sent, never saved")
    func previewKeepsTheToken() async {
        for token in Self.tokens {
            let transport = CountingPlanTransport(reply: Self.reply(token: token))
            var sheet = PlanSheetGateTests.ready(accepted: true, budget: 25)
            await PlanSheetGateTests.drive(&sheet, PlanSheetGateTests.planner(transport))
            let want = PlanPreview(route: Self.answerLine, etaSeconds: 900, fastestEtaSeconds: 800, etaIsEstimate: true,
                                   hazards: [], waypoints: Self.answerPins, lambda: 7.75, continuation: token.map {
                                       PlanContinuation(token: $0, place: 42, budgetMinutes: 25)
                                   })
            guard case let .preview(_, got) = sheet.state else {
                Issue.record("token \(token ?? "nil"): the sheet is \(sheet.state), not a preview")
                continue
            }
            #expect(got == want, "token \(token ?? "nil")")
            // Read back field by field against literals too: `want` is built by the same inits it checks.
            let kept = got.continuation.map { [$0.token, String($0.place), String($0.budgetMinutes)] }
            #expect(kept == token.map { [$0, "42", "25"] }, "token \(token ?? "nil")")
            let bare = PlanPreview(route: want.route, etaSeconds: 900, fastestEtaSeconds: 800, etaIsEstimate: true,
                                   hazards: [], waypoints: want.waypoints, lambda: 7.75)
            #expect(SavedDraft.of(want, budgetMinutes: 25, name: "x", createdAt: 1)
                == SavedDraft.of(bare, budgetMinutes: 25, name: "x", createdAt: 1))
        }
    }
}

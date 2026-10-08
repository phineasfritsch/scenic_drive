import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0319 R9: DriveSession's RerouteRequest leaves the device through `PlanClient.reroute` - the entry point NavAdapter
/// calls - as ONE coordinate rounded to 2 dp here, the place id, the budget and {token, first_pin}. The remaining
/// pins, the destination coordinate and lambda never leave: the Worker remembered them under the token. Every case
/// compares what reached the counting fake whole against a request recomputed here from the same inputs.
@Suite struct PlanRerouteWireTests {
    static let token = "0f1e2d3c-4b5a-4968-8776-655443322110"

    static func reroute(lat: Double = 34.0212345, lon: Double = -118.4987654, first: Int = 1) -> RerouteRequest {
        RerouteRequest(origin: Coordinate(latitude: lat, longitude: lon),
                       remainingWaypoints: [Coordinate(latitude: 34.0412345, longitude: -118.5612345),
                                            Coordinate(latitude: 34.0612345, longitude: -118.5812345)],
                       firstRemainingWaypoint: first,
                       destination: Coordinate(latitude: 34.0676, longitude: -118.5957), lambda: 7.75)
    }

    /// One reroute through a fresh counting fake answering the recorded 200: what reached it, the refusal if any,
    /// and the response if one came back.
    static func send(_ request: RerouteRequest, token: String = token, budget: Int = 25,
                     installID: (any InstallIDProvider)? = PlanWire.install, account: (any AccountTokenProvider)? = nil,
                     session: (any PlanSessionProvider)? = nil,
                     reply: PlanHTTPReply? = nil)
        async throws -> (requests: [PlanHTTPRequest], refusal: PlanRefusal?, response: PlanResponse?) {
        let fake = CountingPlanTransport(reply: try reply ?? PlanWire.recordedReply("200-plan"))
        let client = PlanClient(base: PlanWire.base, transport: fake, installID: installID, accountToken: account, session: session)
        var refusal: PlanRefusal?
        var response: PlanResponse?
        do {
            response = try await client.reroute(request, token: token, place: 42, budgetMinutes: budget)
        } catch {
            if case .refusedOnDevice(let why) = error { refusal = why }
        }
        return (await fake.requests, refusal, response)
    }

    /// The request for these inputs, spelled out: sorted keys, the place as a string, the origin as typed here.
    static func recomputed(lat: String, lon: String, first: Int, budget: Int = 25,
                           account: String? = nil) -> PlanHTTPRequest {
        let body = "{\"budget_minutes\":\(budget),\"destination\":{\"place\":\"42\"},"
            + "\"origin\":{\"lat\":\(lat),\"lon\":\(lon)},"
            + "\"reroute\":{\"first_pin\":\(first),\"token\":\"\(token)\"},\"vehicle\":\"standard\"}"
        var headers = ["content-type": "application/json", "x-scenic-device": PlanWire.deviceHeader]
        if let account { headers["x-scenic-account-token"] = account }
        return PlanHTTPRequest(url: PlanWire.base.appendingPathComponent("plan"), method: "POST", headers: headers,
                               body: Data(body.utf8))
    }

    @Test("a reroute leaves as ONE 2-dp origin, the place, the budget and {token, first_pin}, whole")
    func rerouteRequestWhole() async throws {
        let sent = try await Self.send(Self.reroute())
        #expect(sent.refusal == nil)
        #expect(sent.requests == [Self.recomputed(lat: "34.02", lon: "-118.5", first: 1)])
        let paid = try await Self.send(Self.reroute(), account: FixedAccountToken("0A1B2C3D-4E5F-4061-8273-94A5B6C7D8E9"))
        #expect(paid.requests == [Self.recomputed(lat: "34.02", lon: "-118.5", first: 1,
                                                  account: "0a1b2c3d-4e5f-4061-8273-94a5b6c7d8e9")])
    }

    @Test("the reroute origin is rounded on the device at every bound")
    func rerouteOriginRounded() async throws {
        let rows: [(Double, Double, (String, String)?)] = [
            (34.0249, -118.4951, ("34.02", "-118.5")),
            (34.0251, -118.4949, ("34.03", "-118.49")),
            (34.02, -118.49, ("34.02", "-118.49")),
            (89.996, 179.996, ("90", "180")),
            (-89.996, -179.996, ("-90", "-180")),
            (90.004, -180.004, ("90", "-180")),
            (90.006, 0.5, nil),
            (-90.006, 0.5, nil),
            (0.5, 180.006, nil),
            (0.5, -180.006, nil),
            (.nan, 0.5, nil),
            (0.5, .infinity, nil),
        ]
        for (lat, lon, wire) in rows {
            let sent = try await Self.send(Self.reroute(lat: lat, lon: lon, first: 2))
            if let wire {
                #expect(sent.requests == [Self.recomputed(lat: wire.0, lon: wire.1, first: 2)], "\(lat), \(lon)")
                #expect(sent.refusal == nil, "\(lat), \(lon)")
            } else {
                #expect(sent.requests.isEmpty, "\(lat), \(lon)")
                #expect(sent.refusal == .originOutOfRange, "\(lat), \(lon)")
            }
        }
    }

    @Test("a reroute is refused on the device with zero requests")
    func rerouteRefusals() async throws {
        let upper = Self.token.uppercased()
        let rows: [(String, Int, Int, Bool, PlanRefusal?)] = [
            (Self.token, 0, 25, true, nil),
            (Self.token, 9, 25, true, nil),
            (Self.token, -1, 25, true, .firstPinOutOfRange),
            (Self.token, 10, 25, true, .firstPinOutOfRange),
            (String(Self.token.dropFirst()), 1, 25, true, .rerouteTokenMalformed),
            (Self.token + "0", 1, 25, true, .rerouteTokenMalformed),
            (upper, 1, 25, true, .rerouteTokenMalformed),
            ("g" + Self.token.dropFirst(), 1, 25, true, .rerouteTokenMalformed),
            (Self.token.replacingOccurrences(of: "-", with: "0"), 1, 25, true, .rerouteTokenMalformed),
            (Self.token, 1, 0, true, nil),
            (Self.token, 1, 180, true, nil),
            (Self.token, 1, -1, true, .budgetOutOfRange),
            (Self.token, 1, 181, true, .budgetOutOfRange),
            (Self.token, 1, 25, false, .noInstallID),
        ]
        for (token, first, budget, identified, refusal) in rows {
            let sent = try await Self.send(Self.reroute(first: first), token: token, budget: budget,
                                           installID: identified ? PlanWire.install : nil)
            #expect(sent.refusal == refusal, "\(token) \(first) \(budget) \(identified)")
            #expect(sent.requests.count == (refusal == nil ? 1 : 0), "\(token) \(first) \(budget) \(identified)")
            if refusal == nil {
                #expect(sent.requests == [Self.recomputed(lat: "34.02", lon: "-118.5", first: first, budget: budget)])
            }
        }
    }

    @Test("plan_token decodes, and absent or null decodes nil")
    func planTokenDecodes() async throws {
        let recorded = String(decoding: try PlanWire.fixture("200-plan"), as: UTF8.self)
        #expect(recorded.hasSuffix(",\"plan_token\":null}"))
        let named = recorded.replacingOccurrences(of: "\"plan_token\":null", with: "\"plan_token\":\"\(Self.token)\"")
        let absent = recorded.replacingOccurrences(of: ",\"plan_token\":null", with: "")
        let cases: [(String, String?)] = [(recorded, nil), (named, Self.token), (absent, nil)]
        for (text, token) in cases {
            let sent = try await Self.send(Self.reroute(), reply: PlanHTTPReply(status: 200, body: Data(text.utf8)))
            let response = try #require(sent.response)
            #expect(response.planToken == token)
            let plain = try JSONDecoder().decode(PlanResponse.self, from: Data(recorded.utf8))
            #expect(response == PlanResponse(route: plain.route, distanceMeters: plain.distanceMeters,
                                             etaSeconds: plain.etaSeconds, fastestEtaSeconds: plain.fastestEtaSeconds,
                                             ceilingSeconds: plain.ceilingSeconds, budgetSeconds: plain.budgetSeconds,
                                             lambda: plain.lambda, evaluations: plain.evaluations,
                                             usedBudget: plain.usedBudget, etaIsEstimate: plain.etaIsEstimate,
                                             hazards: plain.hazards, waypoints: plain.waypoints,
                                             appleMapsURL: plain.appleMapsURL, planToken: token))
        }
    }
}

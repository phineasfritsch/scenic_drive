import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0333 R3, R4: a plan-family 401 (`session_rejected` - the Worker cannot verify the Bearer, e.g. after a
/// SESSION_JWT_SECRET rotation) through the SHIPPING PlanClient (plan and reroute), TripClient and LoopClient over a
/// REAL SessionStore and ONE scripted transport, as the cross product route x held {Keychain session - this launch's
/// acquisition unspent; a session acquired this launch - spent; no App Attest} x Worker {answers, rejects once, rejects
/// always}, two user actions each. The WHOLE ordered request list - App Attest and route alike - EQUALS the list
/// recomputed here from the variant: a 401 to a request that carried a Bearer hands the token back, the store acquires
/// once more, and the byte-identical body is resent ONCE; a second 401 hands that token back too but is final - never
/// a third request, never a second re-acquisition; a request with no Bearer is never resent.
@Suite("PlanSessionRetryTests")
struct PlanSessionRetryTests {
    enum Route: String, CaseIterable, Sendable {
        case plan, reroute, trip, loop
    }

    enum Held: String, CaseIterable, Sendable {
        /// A live Keychain session with no act: this launch's one acquisition is unspent.
        case keychain
        /// Nothing stored: the first request attests a key, spending this launch's acquisition.
        case acquired
        /// No App Attest on this device: never a session, never a Bearer.
        case noSession
    }

    enum Worker: String, CaseIterable, Sendable {
        /// Every request answered with a non-401 status.
        case answers
        /// The first request 401, every later one answered.
        case rejectsOnce
        /// Every request 401.
        case rejectsAlways
    }

    struct Row: Sendable, CustomTestStringConvertible {
        let route: Route
        let held: Held
        let worker: Worker
        var testDescription: String { "\(route) \(held) \(worker)" }
    }

    static let rows: [Row] = Route.allCases.flatMap { route in
        Held.allCases.flatMap { held in Worker.allCases.map { Row(route: route, held: held, worker: $0) } }
    }

    /// The token /attest/assert answers - distinct from both the stored and the attested one, so a resend is seen.
    static let freshToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ZnJlc2g.c2lnLWZyZXNo"
    static let rejected = AttestWire.reply(401, #"{"error":"session_rejected"}"#)
    static let answered = PlanHTTPReply(status: 503, body: Data())

    static func path(_ route: Route) -> String {
        switch route {
        case .plan, .reroute: return "/plan"
        case .trip: return "/trip"
        case .loop: return "/loop"
        }
    }

    static func transport(_ row: Row) -> ScriptedTransport {
        let replies: [PlanHTTPReply]
        switch row.worker {
        case .answers: replies = [answered]
        case .rejectsOnce: replies = [rejected, answered]
        case .rejectsAlways: replies = [rejected]
        }
        let assert = AttestWire.reply(200, "{\"token\":\"\(freshToken)\",\"expires_at\":\"2026-10-08T03:00:00.000Z\"}")
        return ScriptedTransport(["POST /attest/challenge": [AttestWire.challengeReply],
                                  "POST /attest": [AttestWire.sessionReply], "POST /attest/assert": [assert],
                                  "POST " + path(row.route): replies])
    }

    static func store(_ held: Held, _ transport: ScriptedTransport) -> SessionStore {
        let stored: KeychainRead<SessionRecord> = held == .keychain ? .valid(SessionAccountTests.held(nil)) : .absent
        return SessionStore(client: AttestWire.client(transport), attester: FakeAttester(isSupported: held != .noSession),
                            storage: MemorySessionStorage(stored), account: nil, now: { AttestWire.now })
    }

    static func body(_ route: Route) -> Data {
        switch route {
        case .plan: return Data(AccountTokenHeaderTests.planBody.utf8)
        case .trip: return Data(AccountTokenHeaderTests.tripBody.utf8)
        case .loop: return Data(AccountTokenHeaderTests.loopBody.utf8)
        case .reroute: return PlanRerouteWireTests.recomputed(lat: "34.02", lon: "-118.5", first: 1).body
        }
    }

    /// The route request with `bearer` (or none), spelled out: one header set, the same bytes every time.
    static func request(_ route: Route, _ bearer: String?) -> PlanHTTPRequest {
        var headers = ["content-type": "application/json", "x-scenic-device": "6f9619ff-8b86-4d01-b42d-00c04fc964ff"]
        if let bearer { headers["authorization"] = "Bearer \(bearer)" }
        return PlanHTTPRequest(url: URL(string: "https://scenic-api.test\(path(route))")!, method: "POST",
                               headers: headers, body: body(route))
    }

    /// Every request of TWO user actions, in order - recomputed from the variant, never read from the store.
    static func expected(_ row: Row) -> [PlanHTTPRequest] {
        let send = { (bearer: String?) in request(row.route, bearer) }
        var list: [PlanHTTPRequest]
        let first: String
        switch row.held {
        case .noSession: return [send(nil), send(nil)]
        case .keychain: (list, first) = ([], AttestWire.oldToken)
        case .acquired: (list, first) = ([AttestWire.challengeRequest(), AttestWire.attestRequest()], AttestWire.newToken)
        }
        list.append(send(first))
        if row.worker == .answers { return list + [send(first)] }
        let key = row.held == .keychain ? AttestWire.oldKey : AttestWire.newKey
        list += [AttestWire.challengeRequest(), AttestWire.renewRequest(key), send(freshToken)]
        return list + [send(row.worker == .rejectsOnce ? freshToken : nil)]
    }

    /// One user action of `route` through its shipping client.
    static func act(_ route: Route, _ transport: ScriptedTransport, _ session: SessionStore) async {
        switch route {
        case .plan:
            _ = await PlanWire.plan(through: transport, session: session)
        case .reroute:
            let client = PlanClient(base: PlanWire.base, transport: transport, installID: PlanWire.install,
                                    accountToken: nil, session: session)
            _ = try? await client.reroute(PlanRerouteWireTests.reroute(), token: PlanRerouteWireTests.token, place: 42,
                                          budgetMinutes: 25)
        case .trip:
            _ = await TripWire.trip(through: transport, days: 2, session: session)
        case .loop:
            _ = await LoopWire.loop(through: transport, minutes: 45, session: session)
        }
    }

    @Test("a 401 hands the session back, re-acquires once and resends the same bytes once; never a third request",
          arguments: rows)
    func rejectedSessionRecovers(_ row: Row) async {
        let transport = Self.transport(row)
        let session = Self.store(row.held, transport)
        await Self.act(row.route, transport, session)
        await Self.act(row.route, transport, session)
        #expect(await transport.requests == Self.expected(row))
    }

    @Test("the resend carries the same purchase: the renewal names it and the Bearer is the renewed session's",
          arguments: Route.allCases)
    func resendKeepsThePurchase(_ route: Route) async {
        let row = Row(route: route, held: .keychain, worker: .rejectsOnce)
        let transport = Self.transport(row)
        let live = SessionAccountTests.Purchase.live
        let session = SessionStore(client: AttestWire.client(transport), attester: FakeAttester(isSupported: true),
                                   storage: MemorySessionStorage(.valid(SessionAccountTests.held(live.wire))),
                                   account: nil, now: { AttestWire.now })
        let account = FixedAccountToken(live.uuid?.uuidString)
        switch route {
        case .plan: _ = await PlanWire.plan(through: transport, account: account, session: session)
        case .reroute:
            let client = PlanClient(base: PlanWire.base, transport: transport, installID: PlanWire.install,
                                    accountToken: account, session: session)
            _ = try? await client.reroute(PlanRerouteWireTests.reroute(), token: PlanRerouteWireTests.token, place: 42,
                                          budgetMinutes: 25)
        case .trip: _ = await TripWire.trip(through: transport, days: 2, account: account, session: session)
        case .loop: _ = await LoopWire.loop(through: transport, minutes: 45, account: account, session: session)
        }
        func send(_ bearer: String) -> PlanHTTPRequest {
            let plain = Self.request(route, bearer)
            var headers = plain.headers
            headers["x-scenic-account-token"] = "0e6b9a4c-5f1d-4c2b-9a8e-3d7f1b2c4a5e"
            return PlanHTTPRequest(url: plain.url, method: "POST", headers: headers, body: plain.body)
        }
        #expect(await transport.requests == [send(AttestWire.oldToken), AttestWire.challengeRequest(),
                                             SessionAccountTests.renewRequest(AttestWire.oldKey, act: live.wire),
                                             send(Self.freshToken)])
    }

    @Test("no row ignores its variant: held and Worker each change some row's requests, and every action is bounded")
    func rowsFollowTheirVariant() {
        for route in Route.allCases {
            let mine = Self.rows.filter { $0.route == route }
            let lists = mine.map { Self.expected($0) }
            #expect(lists.indices.filter { i in !lists[..<i].contains(lists[i]) }.count == 7)
            #expect(mine.contains { a in mine.contains { b in
                a.held != b.held && a.worker == b.worker && Self.expected(a) != Self.expected(b) } })
            #expect(mine.contains { a in mine.contains { b in
                a.held == b.held && a.worker != b.worker && Self.expected(a) != Self.expected(b) } })
        }
        let routeRequests = { (row: Row) in Self.expected(row).filter { $0.url.path == Self.path(row.route) }.count }
        let challenges = { (row: Row) in Self.expected(row).filter { $0.url.path == "/attest/challenge" }.count }
        #expect(Self.rows.allSatisfy { routeRequests($0) <= 4 && challenges($0) <= 2 })
        #expect(Self.rows.filter { routeRequests($0) == 3 }.allSatisfy { $0.worker != .answers && $0.held != .noSession })
        #expect(Self.rows.count == 36)
    }
}

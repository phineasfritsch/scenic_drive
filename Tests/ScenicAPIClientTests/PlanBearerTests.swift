import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0322 R4, R5: every plan-family request - /plan, /trip, /loop - through the shipping clients over a REAL
/// SessionStore, as the cross product {session with act, session without act, no session} x {no purchase, live,
/// expired} x {attest server answers, down}. Each row's whole request (and the store's App Attest requests) EQUALS the
/// value recomputed here from the row's variant: the Bearer rides exactly when the session's act is the purchase the
/// request names, renewed first when it is not; the x-scenic-account-token header rides beside it all the same; a
/// session for another purchase is never sent. The client only names credentials - the Worker decides the tier.
@Suite("PlanBearerTests")
struct PlanBearerTests {
    typealias Purchase = SessionAccountTests.Purchase

    enum Held: String, CaseIterable, Sendable {
        /// A live Keychain session issued for the LIVE purchase.
        case withAct
        /// A live Keychain session issued with no act.
        case withoutAct
        /// No App Attest on this device: never a session.
        case noSession
    }

    enum Server: String, CaseIterable, Sendable {
        case answers, down
    }

    enum Route: String, CaseIterable, Sendable {
        case plan, trip, loop
    }

    struct Row: Sendable, CustomTestStringConvertible {
        let route: Route
        let held: Held
        let purchase: Purchase
        let server: Server
        var testDescription: String { "\(route) \(held) \(purchase) \(server)" }
    }

    static let rows: [Row] = Route.allCases.flatMap { route in
        Held.allCases.flatMap { held in
            Purchase.allCases.flatMap { purchase in
                Server.allCases.map { Row(route: route, held: held, purchase: purchase, server: $0) }
            }
        }
    }

    static func heldAct(_ held: Held) -> String? { held == .withAct ? Purchase.live.wire : nil }

    /// The Bearer the row must carry: the held token when its act is the purchase, the renewed one when the server
    /// renews it, else none - recomputed from the variant, never read from the store.
    static func bearer(_ row: Row) -> String? {
        if row.held == .noSession { return nil }
        if heldAct(row.held) == row.purchase.wire { return AttestWire.oldToken }
        return row.server == .answers ? AttestWire.newToken : nil
    }

    static func attestRequests(_ row: Row) -> [PlanHTTPRequest] {
        if row.held == .noSession || heldAct(row.held) == row.purchase.wire { return [] }
        let renew = SessionAccountTests.renewRequest(AttestWire.oldKey, act: row.purchase.wire)
        return row.server == .answers ? [AttestWire.challengeRequest(), renew] : [AttestWire.challengeRequest()]
    }

    static func headers(_ row: Row) -> [String: String] {
        var headers = ["content-type": "application/json", "x-scenic-device": "6f9619ff-8b86-4d01-b42d-00c04fc964ff"]
        if let wire = row.purchase.wire { headers["x-scenic-account-token"] = wire }
        if let token = bearer(row) { headers["authorization"] = "Bearer \(token)" }
        return headers
    }

    static func expected(_ row: Row) -> PlanHTTPRequest {
        let body: String
        switch row.route {
        case .plan: body = AccountTokenHeaderTests.planBody
        case .trip: body = AccountTokenHeaderTests.tripBody
        case .loop: body = AccountTokenHeaderTests.loopBody
        }
        return PlanHTTPRequest(url: URL(string: "https://scenic-api.test/\(row.route.rawValue)")!, method: "POST",
                               headers: headers(row), body: Data(body.utf8))
    }

    static func store(_ held: Held, _ server: Server) -> (SessionStore, ScriptedTransport) {
        let transport = ScriptedTransport(server == .answers ? SessionAccountTests.ok : [:])
        let stored: KeychainRead<SessionRecord> = held == .noSession ? .absent
            : .valid(SessionAccountTests.held(heldAct(held)))
        let store = SessionStore(client: AttestWire.client(transport),
                                 attester: FakeAttester(isSupported: held != .noSession),
                                 storage: MemorySessionStorage(stored), account: nil, now: { AttestWire.now })
        return (store, transport)
    }

    /// One request of `route` through its shipping client, with the purchase and the session store given.
    static func send(_ route: Route, through fake: CountingPlanTransport, account: FixedAccountToken,
                     session: SessionStore, invalid: Bool = false) async {
        switch route {
        case .plan:
            _ = await PlanWire.plan(through: fake, from: Coordinate(latitude: invalid ? 34.021 : 34.02, longitude: -118.49),
                                    account: account, session: session)
        case .trip:
            _ = await TripWire.trip(through: fake, days: invalid ? 0 : 2, account: account, session: session)
        case .loop:
            _ = await LoopWire.loop(through: fake, minutes: invalid ? 0 : 45, account: account, session: session)
        }
    }

    @Test("every plan-family request names the purchase and carries the Bearer exactly when its act is that purchase",
          arguments: rows)
    func requestCarriesTheMatchingSession(_ row: Row) async {
        let (session, attest) = Self.store(row.held, row.server)
        let fake = CountingPlanTransport(reply: PlanHTTPReply(status: 503, body: Data()))
        await Self.send(row.route, through: fake, account: FixedAccountToken(row.purchase.uuid?.uuidString),
                        session: session)
        #expect(await fake.requests == [Self.expected(row)])
        #expect(await attest.requests == Self.attestRequests(row))
    }

    @Test("a session issued before the purchase is never sent: the header alone rides until it is renewed",
          arguments: Route.allCases)
    func staleSessionNeverSent(_ route: Route) async {
        let row = Row(route: route, held: .withoutAct, purchase: .live, server: .down)
        #expect(Self.headers(row) == ["content-type": "application/json",
                                      "x-scenic-device": "6f9619ff-8b86-4d01-b42d-00c04fc964ff",
                                      "x-scenic-account-token": "0e6b9a4c-5f1d-4c2b-9a8e-3d7f1b2c4a5e"])
        let (session, _) = Self.store(row.held, row.server)
        let fake = CountingPlanTransport(reply: PlanHTTPReply(status: 503, body: Data()))
        await Self.send(route, through: fake, account: FixedAccountToken(Purchase.live.uuid?.uuidString), session: session)
        #expect(await fake.requests == [Self.expected(row)])
    }

    @Test("a request refused on the device acquires no session", arguments: Route.allCases)
    func refusalAcquiresNothing(_ route: Route) async {
        // Nothing stored and App Attest supported: ANY ask of this store, for any purchase, would attest a key.
        let (session, attest, _) = SessionAccountTests.store(.absent)
        let fake = CountingPlanTransport(reply: PlanHTTPReply(status: 503, body: Data()))
        await Self.send(route, through: fake, account: FixedAccountToken(Purchase.live.uuid?.uuidString),
                        session: session, invalid: true)
        #expect(await fake.count == 0)
        #expect(await attest.requests == [])
    }

    @Test("no row ignores its variant: each of held, purchase and server changes some row's request")
    func rowsFollowTheirVariant() {
        func differ(_ a: Row, _ b: Row) -> Bool {
            Self.headers(a) != Self.headers(b) || Self.attestRequests(a) != Self.attestRequests(b)
        }
        for route in Route.allCases {
            let mine = Self.rows.filter { $0.route == route }
            #expect(Set(mine.map { Self.headers($0) }).count == 8)
            #expect(mine.contains { a in mine.contains { b in
                a.held != b.held && a.purchase == b.purchase && a.server == b.server && differ(a, b) } })
            #expect(mine.contains { a in mine.contains { b in
                a.held == b.held && a.purchase != b.purchase && a.server == b.server && differ(a, b) } })
            #expect(mine.contains { a in mine.contains { b in
                a.held == b.held && a.purchase == b.purchase && a.server != b.server && differ(a, b) } })
        }
        #expect(Self.rows.filter { Self.bearer($0) == nil && $0.purchase != .none && $0.held != .noSession }
            .allSatisfy { $0.server == .down && Self.headers($0)["x-scenic-account-token"] != nil })
        #expect(Self.rows.count == 54)
    }
}

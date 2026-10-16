import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0362 A4 (R2): SearchClient.search sends EXACTLY /plan's identity - the request equals one rebuilt here from
/// IdentityHeaders.json over the same install id, purchase and Bearer - re-sends once after a 401 to that Bearer, and
/// sends nothing without an install id.
@Suite("SearchClientIdentityTests") struct SearchClientIdentityTests {
    static let base = URL(string: "https://scenic-api.test")!
    static let device = UUID(uuidString: "0F8B6D5E-1A2B-4C3D-8E9F-0123456789AB")!
    static let purchase = "6F9619FF-8B86-4D01-B42D-00C04FC964FF"
    static let body = Data(#"{"near":{"lat":34.13,"lon":-118.45},"q":"Mulholland Drive"}"#.utf8)
    static let near = Coordinate(latitude: 34.1349, longitude: -118.4512)

    static func expected(account: String?, bearer: String?) -> PlanHTTPRequest {
        PlanHTTPRequest(url: base.appendingPathComponent("search"), method: "POST",
                        headers: IdentityHeaders.json(device: device, account: account.map { UUID(uuidString: $0)! },
                                                      bearer: bearer),
                        body: body)
    }

    static func sent(account: String?, session: FixedPlanSession?, status: Int = 200,
                     installID: (any InstallIDProvider)? = FixedInstallID("0F8B6D5E-1A2B-4C3D-8E9F-0123456789AB"))
        async -> (requests: [PlanHTTPRequest], outcome: SearchOutcome) {
        let fake = CountingPlanTransport(reply: PlanHTTPReply(status: status, body: Data(#"{"results":[]}"#.utf8)))
        let client = SearchClient(base: base, transport: fake, installID: installID,
                                  accountToken: FixedAccountToken(account), session: session)
        let outcome = await client.search("Mulholland Drive", near: near)
        return (await fake.requests, outcome)
    }

    @Test("no purchase and no session: the device header alone")
    func deviceOnly() async {
        let answer = await Self.sent(account: nil, session: nil)
        #expect(answer.requests == [Self.expected(account: nil, bearer: nil)])
        #expect(answer.outcome == .results([]))
    }

    @Test("a purchase and no session: the account token rides beside the device")
    func account() async {
        let answer = await Self.sent(account: Self.purchase, session: FixedPlanSession([]))
        #expect(answer.requests == [Self.expected(account: Self.purchase, bearer: nil)])
    }

    @Test("a purchase and its session: the Bearer too, asked for that purchase")
    func bearer() async {
        let session = FixedPlanSession(["jwt-1"])
        let answer = await Self.sent(account: Self.purchase, session: session)
        #expect(answer.requests == [Self.expected(account: Self.purchase, bearer: "jwt-1")])
        #expect(await session.asked == [UUID(uuidString: Self.purchase)!])
    }

    @Test("a 401 to the Bearer hands it back and re-sends the same bytes ONCE with the renewed one")
    func rejectedBearer() async {
        let session = FixedPlanSession(["jwt-1", "jwt-2"])
        let answer = await Self.sent(account: Self.purchase, session: session, status: 401)
        #expect(answer.requests == [Self.expected(account: Self.purchase, bearer: "jwt-1"),
                                    Self.expected(account: Self.purchase, bearer: "jwt-2")])
        #expect(await session.rejected == ["jwt-1", "jwt-2"])
        #expect(answer.outcome == .unauthorized)
    }

    @Test("a 401 to a request with no Bearer is never re-sent")
    func rejectedWithoutBearer() async {
        let answer = await Self.sent(account: nil, session: FixedPlanSession([]), status: 401)
        #expect(answer.requests == [Self.expected(account: nil, bearer: nil)])
    }

    @Test("no install id: refused on the device, zero requests")
    func noInstallID() async {
        let answer = await Self.sent(account: Self.purchase, session: FixedPlanSession(["jwt-1"]), installID: nil)
        #expect(answer.requests.isEmpty)
        #expect(answer.outcome == .refusedOnDevice)
    }
}

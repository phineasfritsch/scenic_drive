import Foundation
import ScenicAPIClient
import Testing

/// T-0322 R1-R3: the session carries the purchase. /attest and /attest/assert name the device's appAccountToken -
/// live or expired alike, the Worker tells them apart - as the body's sorted-first key, or name none; the Keychain
/// record remembers the act it was issued for; and a session is used only while its act is the device's current token,
/// renewed once per token value per launch otherwise. Every request and write is compared WHOLE against a literal built
/// here by string interpolation (memory full-equality-oracle), every row a function of its variant.
@Suite("SessionAccountTests")
struct SessionAccountTests {
    enum Purchase: String, CaseIterable, Sendable {
        case none, live, expired

        /// Written UPPERCASE, as Foundation's uuidString prints them.
        var uuid: UUID? {
            switch self {
            case .none: return nil
            case .live: return UUID(uuidString: "0E6B9A4C-5F1D-4C2B-9A8E-3D7F1B2C4A5E")!
            case .expired: return UUID(uuidString: "A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")!
            }
        }

        /// The lowercased literal the Worker's UUID pattern reads, typed out - never computed from `uuid`.
        var wire: String? {
            switch self {
            case .none: return nil
            case .live: return "0e6b9a4c-5f1d-4c2b-9a8e-3d7f1b2c4a5e"
            case .expired: return "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
            }
        }
    }

    enum Call: String, CaseIterable, Sendable {
        case attest, renew
    }

    static func lead(_ act: String?) -> String { act.map { "\"appAccountToken\":\"\($0)\"," } ?? "" }

    static func attestRequest(_ keyId: String, act: String?) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/attest")!, method: "POST",
                        headers: ["content-type": "application/json"],
                        body: Data(("{\(lead(act))\"attestation\":\"\(AttestWire.attestation)\",\"challenge\":\""
                                    + "\(AttestWire.challenge)\",\"device\":\"\(AttestWire.deviceWire)\",\"keyId\":\""
                                    + "\(keyId)\"}").utf8))
    }

    static func renewRequest(_ keyId: String, act: String?) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/attest/assert")!, method: "POST",
                        headers: ["content-type": "application/json"],
                        body: Data(("{\(lead(act))\"assertion\":\"\(AttestWire.assertion)\",\"challenge\":\""
                                    + "\(AttestWire.challenge)\",\"keyId\":\"\(keyId)\"}").utf8))
    }

    static let ok: [String: [PlanHTTPReply]] = ["POST /attest/challenge": [AttestWire.challengeReply],
                                                "POST /attest": [AttestWire.sessionReply],
                                                "POST /attest/assert": [AttestWire.sessionReply]]

    static func held(_ act: String?, _ seconds: TimeInterval = 1800) -> SessionRecord {
        SessionRecord(keyId: AttestWire.oldKey, token: AttestWire.oldToken,
                      expiresAt: AttestWire.now.addingTimeInterval(seconds), act: act)
    }

    static func renewed(_ act: String?) -> SessionRecord {
        SessionRecord(keyId: AttestWire.oldKey, token: AttestWire.newToken, expiresAt: AttestWire.expires, act: act)
    }

    static func store(_ stored: KeychainRead<SessionRecord>, replies: [String: [PlanHTTPReply]] = ok,
                      account: (any AccountTokenProvider)? = nil)
        -> (SessionStore, ScriptedTransport, MemorySessionStorage) {
        let transport = ScriptedTransport(replies)
        let storage = MemorySessionStorage(stored)
        let store = SessionStore(client: AttestWire.client(transport), attester: FakeAttester(isSupported: true),
                                 storage: storage, account: account, now: { AttestWire.now })
        return (store, transport, storage)
    }

    @Test("attest and assert carry exactly the purchase's token, live or expired, or none",
          arguments: Purchase.allCases, Call.allCases)
    func bodyCarriesThePurchase(_ purchase: Purchase, _ call: Call) async {
        let transport = ScriptedTransport(Self.ok)
        let client = AttestWire.client(transport)
        let outcome: AttestOutcome
        switch call {
        case .attest:
            outcome = await client.attest(keyId: AttestWire.newKey, attestation: AttestWire.attestation,
                                          challenge: AttestWire.challenge, account: purchase.uuid)
        case .renew:
            outcome = await client.renew(keyId: AttestWire.oldKey, assertion: AttestWire.assertion,
                                         challenge: AttestWire.challenge, account: purchase.uuid)
        }
        let expected = call == .attest ? Self.attestRequest(AttestWire.newKey, act: purchase.wire)
            : Self.renewRequest(AttestWire.oldKey, act: purchase.wire)
        #expect(await transport.requests == [expected])
        #expect(outcome == .session(token: AttestWire.newToken, expiresAt: AttestWire.expires))
    }

    @Test("the session record keeps its act on the wire, and an empty or null act is malformed",
          arguments: Purchase.allCases)
    func recordKeepsAct(_ purchase: Purchase) {
        let record = Self.held(purchase.wire)
        let seconds = Int64(AttestWire.now.addingTimeInterval(1800).timeIntervalSince1970)
        let act = purchase.wire.map { "\"act\":\"\($0)\"," } ?? ""
        let bytes = "{\(act)\"expires_at\":\(seconds),\"key_id\":\"\(AttestWire.oldKey)\",\"token\":\"\(AttestWire.oldToken)\"}"
        #expect(String(decoding: record.data, as: UTF8.self) == bytes)
        #expect(SessionRecord(data: Data(bytes.utf8)) == record)
        let tail = "\"expires_at\":\(seconds),\"key_id\":\"\(AttestWire.oldKey)\",\"token\":\"\(AttestWire.oldToken)\"}"
        #expect(SessionRecord(data: Data("{\"act\":\"\",\(tail)".utf8)) == nil)
        #expect(SessionRecord(data: Data("{\"act\":null,\(tail)".utf8)) == nil)
    }

    @Test("a live session is used only while its act is the device's purchase", arguments: Purchase.allCases,
          Purchase.allCases)
    func stepFollowsTheAct(_ stored: Purchase, _ device: Purchase) {
        let read = KeychainRead<SessionRecord>.valid(Self.held(stored.wire))
        let same = stored == device
        #expect(SessionStep.next(stored: read, now: AttestWire.now, spent: false, act: device.wire)
                == (same ? .use(AttestWire.oldToken) : .renew(keyId: AttestWire.oldKey)))
        #expect(SessionStep.next(stored: read, now: AttestWire.now, spent: true, act: device.wire)
                == (same ? .use(AttestWire.oldToken) : .none))
    }

    @Test("a session issued before the purchase renews once to carry it, then is used with no request",
          arguments: [Purchase.live, Purchase.expired])
    func purchaseAfterIssue(_ purchase: Purchase) async {
        let (store, transport, storage) = Self.store(.valid(Self.held(nil)))
        #expect(await store.planSession(account: nil) == AttestWire.oldToken)
        #expect(await transport.requests == [])
        #expect(await store.planSession(account: purchase.uuid) == AttestWire.newToken)
        #expect(await store.planSession(account: purchase.uuid) == AttestWire.newToken)
        #expect(await transport.requests == [AttestWire.challengeRequest(),
                                             Self.renewRequest(AttestWire.oldKey, act: purchase.wire)])
        #expect(storage.writes == [.init(record: Self.renewed(purchase.wire), write: .update)])
    }

    @Test("a purchase made after the launch's first acquisition gets its own one try", arguments: [Purchase.live,
                                                                                                    Purchase.expired])
    func purchaseAfterSpentAcquisition(_ purchase: Purchase) async {
        let (store, transport, _) = Self.store(.absent)
        #expect(await store.planSession(account: nil) == AttestWire.newToken)
        #expect(await store.planSession(account: purchase.uuid) == AttestWire.newToken)
        #expect(await transport.requests == [AttestWire.challengeRequest(), Self.attestRequest(AttestWire.newKey, act: nil),
                                             AttestWire.challengeRequest(),
                                             Self.renewRequest(AttestWire.newKey, act: purchase.wire)])
    }

    @Test("the ledger's acquisition carries the store's purchase, and the plan family then uses that session",
          arguments: Purchase.allCases)
    func ledgerAcquisitionCarriesAct(_ purchase: Purchase) async {
        let (store, transport, storage) = Self.store(.absent, account: FixedAccountToken(purchase.uuid?.uuidString))
        #expect(await store.sessionToken() == AttestWire.newToken)
        #expect(await store.planSession(account: purchase.uuid) == AttestWire.newToken)
        #expect(await transport.requests == [AttestWire.challengeRequest(),
                                             Self.attestRequest(AttestWire.newKey, act: purchase.wire)])
        let fresh = SessionRecord(keyId: AttestWire.newKey, token: AttestWire.newToken, expiresAt: AttestWire.expires,
                                  act: purchase.wire)
        #expect(storage.writes == [.init(record: fresh, write: .add)])
    }

    @Test("a failed renewal for the purchase is that token's one try: never the stale session, which still serves its own act")
    func failedRenewalNeverStale() async {
        let down = ["POST /attest/challenge": [AttestWire.reply(503, "{\"error\":\"attest_unavailable\"}")]]
        let (store, transport, storage) = Self.store(.valid(Self.held(nil)), replies: down)
        #expect(await store.planSession(account: Purchase.live.uuid) == nil)
        #expect(await store.planSession(account: Purchase.live.uuid) == nil)
        #expect(await store.planSession(account: nil) == AttestWire.oldToken)
        #expect(await transport.requests == [AttestWire.challengeRequest()])
        #expect(storage.writes == [])
    }
}

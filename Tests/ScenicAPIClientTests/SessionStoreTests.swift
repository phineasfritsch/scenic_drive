import Foundation
import ScenicAPIClient
import Testing

/// T-0310 acceptance 2 (R3, R4): the session decision as a pure table, then `SessionStore` - production's
/// LedgerSessionProvider - over each stored state: the whole request list, the token and the Keychain writes by
/// full equality, and at most ONE acquisition (a challenge plus an attest or an assert) per launch.
@Suite("SessionStoreTests") struct SessionStoreTests {
    struct StepRow: Sendable, CustomTestStringConvertible {
        let label: String
        let stored: KeychainRead<SessionRecord>
        let unspent: SessionStep
        let spent: SessionStep
        var testDescription: String { label }
    }

    static let justOver = Date(timeIntervalSinceReferenceDate:
        AttestWire.now.addingTimeInterval(SessionStep.margin).timeIntervalSinceReferenceDate.nextUp)

    static let steps: [StepRow] = [
        StepRow(label: "absent", stored: .absent, unspent: .attest, spent: .none),
        StepRow(label: "malformed", stored: .malformed, unspent: .attest, spent: .none),
        StepRow(label: "read failure", stored: .failed(-25308), unspent: .none, spent: .none),
        StepRow(label: "an hour left", stored: .valid(AttestWire.stored(3600)), unspent: .use(AttestWire.oldToken),
                spent: .use(AttestWire.oldToken)),
        StepRow(label: "just over the margin",
                stored: .valid(SessionRecord(keyId: AttestWire.oldKey, token: AttestWire.oldToken, expiresAt: justOver)),
                unspent: .use(AttestWire.oldToken), spent: .use(AttestWire.oldToken)),
        StepRow(label: "inside the margin", stored: .valid(AttestWire.stored(59)),
                unspent: .renew(keyId: AttestWire.oldKey), spent: .none),
        StepRow(label: "expired", stored: .valid(AttestWire.stored(-1)), unspent: .renew(keyId: AttestWire.oldKey),
                spent: .none),
    ]

    @Test("The session step over every stored state, spent and unspent", arguments: steps)
    func step(_ row: StepRow) {
        #expect(SessionStep.next(stored: row.stored, now: AttestWire.now, spent: false) == row.unspent)
        #expect(SessionStep.next(stored: row.stored, now: AttestWire.now, spent: true) == row.spent)
    }

    struct FlowRow: Sendable, CustomTestStringConvertible {
        let label: String
        let stored: KeychainRead<SessionRecord>
        let supported: Bool
        let replies: [String: [PlanHTTPReply]]
        let token: String?
        let requests: [PlanHTTPRequest]
        let writes: [MemorySessionStorage.Write]
        let removes: Int
        var testDescription: String { label }
    }

    static let fresh = SessionRecord(keyId: AttestWire.newKey, token: AttestWire.newToken, expiresAt: AttestWire.expires)
    static let renewed = SessionRecord(keyId: AttestWire.oldKey, token: AttestWire.newToken, expiresAt: AttestWire.expires)
    static let ok: [String: [PlanHTTPReply]] = ["POST /attest/challenge": [AttestWire.challengeReply],
                                                "POST /attest": [AttestWire.sessionReply],
                                                "POST /attest/assert": [AttestWire.sessionReply]]
    static let rejected = AttestWire.reply(400, "{\"error\":\"invalid_assertion\"}")

    static let flows: [FlowRow] = [
        FlowRow(label: "a live token is used and nothing is sent", stored: .valid(AttestWire.stored(1800)),
                supported: true, replies: ok, token: AttestWire.oldToken, requests: [], writes: [], removes: 0),
        FlowRow(label: "nothing stored attests a new key and adds the item", stored: .absent, supported: true,
                replies: ok, token: AttestWire.newToken,
                requests: [AttestWire.challengeRequest(), AttestWire.attestRequest()],
                writes: [.init(record: fresh, write: .add)], removes: 0),
        FlowRow(label: "a malformed item attests a new key and replaces the item", stored: .malformed, supported: true,
                replies: ok, token: AttestWire.newToken,
                requests: [AttestWire.challengeRequest(), AttestWire.attestRequest()],
                writes: [.init(record: fresh, write: .update)], removes: 0),
        FlowRow(label: "an expired session renews by assertion and replaces the item",
                stored: .valid(AttestWire.stored(-1)), supported: true, replies: ok, token: AttestWire.newToken,
                requests: [AttestWire.challengeRequest(), AttestWire.renewRequest(AttestWire.oldKey)],
                writes: [.init(record: renewed, write: .update)], removes: 0),
        FlowRow(label: "a session inside the margin renews", stored: .valid(AttestWire.stored(59)), supported: true,
                replies: ok, token: AttestWire.newToken,
                requests: [AttestWire.challengeRequest(), AttestWire.renewRequest(AttestWire.oldKey)],
                writes: [.init(record: renewed, write: .update)], removes: 0),
        FlowRow(label: "a failed read sends nothing", stored: .failed(-25308), supported: true, replies: ok,
                token: nil, requests: [], writes: [], removes: 0),
        FlowRow(label: "no App Attest on this device sends nothing", stored: .absent, supported: false, replies: ok,
                token: nil, requests: [], writes: [], removes: 0),
        FlowRow(label: "a rate-limited challenge is the launch's one try", stored: .absent, supported: true,
                replies: ["POST /attest/challenge": [AttestWire.reply(429, "{\"error\":\"challenge_rate_limited\"}")]],
                token: nil, requests: [AttestWire.challengeRequest()], writes: [], removes: 0),
        FlowRow(label: "a rejected attestation is the launch's one try", stored: .absent, supported: true,
                replies: ["POST /attest/challenge": [AttestWire.challengeReply],
                          "POST /attest": [AttestWire.reply(400, "{\"error\":\"invalid_attestation\"}")]],
                token: nil, requests: [AttestWire.challengeRequest(), AttestWire.attestRequest()], writes: [], removes: 0),
        FlowRow(label: "a rejected assertion forgets the key", stored: .valid(AttestWire.stored(-1)), supported: true,
                replies: ["POST /attest/challenge": [AttestWire.challengeReply], "POST /attest/assert": [rejected]],
                token: nil, requests: [AttestWire.challengeRequest(), AttestWire.renewRequest(AttestWire.oldKey)],
                writes: [], removes: 1),
        FlowRow(label: "offline is the launch's one try", stored: .absent, supported: true, replies: [:], token: nil,
                requests: [AttestWire.challengeRequest()], writes: [], removes: 0),
    ]

    static func store(_ stored: KeychainRead<SessionRecord>, supported: Bool = true,
                      replies: [String: [PlanHTTPReply]]) -> (SessionStore, ScriptedTransport, MemorySessionStorage) {
        let transport = ScriptedTransport(replies)
        let storage = MemorySessionStorage(stored)
        let store = SessionStore(client: AttestWire.client(transport), attester: FakeAttester(isSupported: supported),
                                 storage: storage, now: { AttestWire.now })
        return (store, transport, storage)
    }

    @Test("Each stored state's token, requests and Keychain writes - and a second call adds no request", arguments: flows)
    func flow(_ row: FlowRow) async {
        let (store, transport, storage) = Self.store(row.stored, supported: row.supported, replies: row.replies)
        #expect(await store.sessionToken() == row.token)
        #expect(await store.sessionToken() == row.token)
        #expect(await transport.requests == row.requests)
        #expect(storage.writes == row.writes)
        #expect(storage.removes == row.removes)
    }

    @Test("A rejected token is dropped and renewed once per launch; another token's rejection drops nothing")
    func rejectedOncePerLaunch() async {
        let (store, transport, storage) = Self.store(.valid(AttestWire.stored(1800)), replies: Self.ok)
        #expect(await store.sessionToken() == AttestWire.oldToken)
        await store.sessionRejected("some.other.token")
        #expect(await store.sessionToken() == AttestWire.oldToken)
        #expect(await transport.requests == [])
        await store.sessionRejected(AttestWire.oldToken)
        #expect(await store.sessionToken() == AttestWire.newToken)
        await store.sessionRejected(AttestWire.newToken)
        #expect(await store.sessionToken() == nil)
        #expect(await transport.requests == [AttestWire.challengeRequest(), AttestWire.renewRequest(AttestWire.oldKey)])
        #expect(storage.writes == [.init(record: Self.renewed, write: .update)])
    }
}

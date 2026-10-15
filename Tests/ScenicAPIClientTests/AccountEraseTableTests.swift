import Foundation
import ScenicAPIClient
import Testing

/// T-0356 A3 (R3, R5): the local erase as a table over every stored item - the cross product of every outcome the
/// transport can produce and every item, through the SHIPPED `AccountDeletion.run()`; the inventory is the measured
/// literal (the T-0356 Log), so a new stored item fails here by name until it is ruled. And the in-memory half:
/// `SessionStore.forgetSession()` removes the Keychain item and never hands the forgotten token back.
@Suite("AccountEraseTableTests") struct AccountEraseTableTests {
    /// The thirteen items the T-0356 MEASURE found, in its order.
    static let inventory: [LocalAccountItem] = [
        .installIDDefaults, .installIDKeychain, .session, .appAttestKey, .purchaseToken, .userStore,
        .disclaimerAcknowledged, .vehicle, .corpusWifiOnly, .corpusFiles, .basemapTiles, .workerBaseURL,
        .corpusManifestURL,
    ]

    /// R3: what names the account, in the order it is erased - written here, never read from the table.
    static let identity: [LocalAccountItem] = [.installIDDefaults, .installIDKeychain, .session]

    struct Row: Sendable, CustomTestStringConvertible {
        let label: String
        let replies: [PlanHTTPReply]
        let tokens: [String?]
        let outcome: AccountOutcome
        var testDescription: String { label }
    }

    static let token = AccountClientTests.first
    static func reply(_ status: Int, _ body: String) -> PlanHTTPReply { AccountClientTests.reply(status, body) }

    static let rows: [Row] = [
        Row(label: "deleted", replies: [reply(200, #"{"deleted":true,"revoke_pending":false,"plans_pending":false}"#)],
            tokens: [token], outcome: .deleted(revokePending: false, plansPending: false)),
        Row(label: "deleted, both pending",
            replies: [reply(200, #"{"deleted":true,"revoke_pending":true,"plans_pending":true}"#)],
            tokens: [token], outcome: .deleted(revokePending: true, plansPending: true)),
        Row(label: "unreadable 200", replies: [reply(200, #"{"deleted":false,"revoke_pending":false,"plans_pending":false}"#)],
            tokens: [token], outcome: .unreadable),
        Row(label: "401 twice", replies: [reply(401, #"{"error":"unauthorized"}"#)],
            tokens: [token, AccountClientTests.second], outcome: .unauthorized),
        Row(label: "405", replies: [reply(405, #"{"error":"DELETE only"}"#)], tokens: [token], outcome: .methodRefused),
        Row(label: "503 auth", replies: [reply(503, #"{"error":"auth_unavailable"}"#)], tokens: [token],
            outcome: .authUnavailable),
        Row(label: "503 store", replies: [reply(503, #"{"error":"account_unavailable"}"#)], tokens: [token],
            outcome: .accountUnavailable),
        Row(label: "500", replies: [reply(500, "")], tokens: [token], outcome: .unexpected(500)),
        Row(label: "offline", replies: [], tokens: [token], outcome: .offline),
        Row(label: "no session", replies: [], tokens: [], outcome: .noSession),
    ]

    /// The row's expected erase list: a function of its outcome alone.
    static func expected(_ outcome: AccountOutcome) -> [LocalAccountItem] {
        if case .deleted = outcome { return identity }
        return []
    }

    @Test("The inventory is every stored item the MEASURE found, and nothing else")
    func inventoryIsMeasured() {
        #expect(LocalAccountItem.allCases == Self.inventory)
    }

    @Test("Every outcome x every item: erased exactly on deleted, and only the identity", arguments: rows)
    func eraseTable(_ row: Row) async {
        let transport = ScriptedTransport(row.replies.isEmpty ? [:] : ["DELETE /account": row.replies])
        let eraser = RecordingEraser()
        let deletion = AccountDeletion(client: AccountClient(base: AccountClientTests.base, transport: transport,
                                                             session: ScriptedAccountSession(row.tokens)),
                                       eraser: eraser)
        let outcome = await deletion.run()
        #expect(outcome == row.outcome)
        let erased = await eraser.erased
        #expect(erased == Self.expected(row.outcome))
        for item in LocalAccountItem.allCases {
            #expect(erased.contains(item) == (Self.expected(row.outcome).contains(item)), "\(item)")
        }
    }

    @Test("No row's expected erase list ignores its outcome")
    func noRowIgnoresItsOutcome() {
        let deleted = Self.rows.filter { if case .deleted = $0.outcome { return true } else { return false } }
        let others = Self.rows.filter { if case .deleted = $0.outcome { return false } else { return true } }
        #expect(!deleted.isEmpty && !others.isEmpty)
        #expect(deleted.allSatisfy { Self.expected($0.outcome) == Self.identity })
        #expect(others.allSatisfy { Self.expected($0.outcome).isEmpty })
        #expect(Set(Self.identity).isSubset(of: Set(Self.inventory)) && Self.identity.count < Self.inventory.count)
    }

    @Test("forgetSession removes the Keychain item and the forgotten token is never handed back")
    func forgetSession() async {
        let transport = ScriptedTransport(["POST /attest/challenge": [AttestWire.challengeReply],
                                           "POST /attest": [AttestWire.sessionReply]])
        let storage = MemorySessionStorage(.valid(AttestWire.stored(3600)))
        let store = SessionStore(client: AttestWire.client(transport), attester: FakeAttester(isSupported: true),
                                 storage: storage, account: nil, now: { AttestWire.now })
        #expect(await store.accountSession() == AttestWire.oldToken)
        await store.forgetSession()
        #expect(storage.removes == 1)
        let next = await store.accountSession()
        #expect(next != AttestWire.oldToken)
        #expect(next == AttestWire.newToken)
    }

    @Test("accountSessionRejected drops the token and grants one re-acquisition")
    func rejectedRenews() async {
        let transport = ScriptedTransport(["POST /attest/challenge": [AttestWire.challengeReply],
                                           "POST /attest/assert": [AttestWire.sessionReply]])
        let storage = MemorySessionStorage(.valid(AttestWire.stored(3600)))
        let store = SessionStore(client: AttestWire.client(transport), attester: FakeAttester(isSupported: true),
                                 storage: storage, account: nil, now: { AttestWire.now })
        #expect(await store.accountSession() == AttestWire.oldToken)
        await store.accountSessionRejected(AttestWire.oldToken)
        #expect(await store.accountSession() == AttestWire.newToken)
    }
}

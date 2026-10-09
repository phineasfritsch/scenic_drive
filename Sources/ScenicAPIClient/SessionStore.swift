import Foundation

/// Production's `LedgerSessionProvider` and `PlanSessionProvider` (T-0310 R3, R4; T-0322 R1-R3): the Worker session,
/// read from the Keychain once and, when it is missing, spent, or issued for another purchase, obtained by App Attest
/// carrying the device's purchase as `appAccountToken` - AT MOST ONE acquisition (a challenge, then an attest or an
/// assert) per launch for each purchase token value, spent before its first request, so no answer and no 401 can make
/// a launch ask twice for the same purchase. A purchase made mid-launch is a new value and gets its own one try.
///
/// A session is handed out only while its act is the purchase asked about (nil for none): the Worker reads a verified
/// Bearer's act and ignores the header beside it, so a session issued before a purchase is never sent for it.
/// A 401 hands the token back (`sessionRejected`): it is dropped for this launch and the next call renews if the
/// acquisition is unspent. T-0333 R4: a plan-family 401 (`planSessionRejected`) drops it the same way and, the FIRST
/// time in a launch for that purchase value, returns the value's acquisition - at most two per value per launch. An assertion the Worker rejects forgets the key, so the next launch attests a new one. No
/// session, for any reason, is nil: the ledger is not called, and a plan-family request carries no Bearer.
public actor SessionStore: LedgerSessionProvider, PlanSessionProvider {
    let client: AttestClient
    let attester: any AppAttesting
    let storage: any SessionStorage
    /// The launch's purchase, read by the ledger's `sessionToken()`; the plan family names its own per request.
    let account: (any AccountTokenProvider)?
    let now: @Sendable () -> Date

    /// What the Keychain holds, as last read or written: it decides between add and update. nil until first read.
    private var keychain: KeychainRead<SessionRecord>?
    /// The session this launch works with: the Keychain's, a new one, or a dropped one.
    private var current: KeychainRead<SessionRecord> = .absent
    /// The purchase token values ("" for none) whose one acquisition this launch has spent.
    private var spent: Set<String> = []
    /// The purchase token values whose one re-acquisition after a plan-family 401 this launch has granted (T-0333 R4).
    private var regranted: Set<String> = []

    public init(client: AttestClient, attester: any AppAttesting, storage: any SessionStorage,
                account: (any AccountTokenProvider)?, now: @escaping @Sendable () -> Date) {
        self.client = client
        self.attester = attester
        self.storage = storage
        self.account = account
        self.now = now
    }

    public func sessionToken() async -> String? {
        await session(for: await account?.accountToken())
    }

    public func planSession(account: UUID?) async -> String? {
        await session(for: account)
    }

    public func sessionRejected(_ token: String) async {
        guard case .valid(let record) = current, record.token == token else { return }
        current = .valid(SessionRecord(keyId: record.keyId, token: record.token, expiresAt: .distantPast,
                                       act: record.act))
    }

    public func planSessionRejected(_ token: String) async {
        guard case .valid(let record) = current, record.token == token else { return }
        await sessionRejected(token)
        let act = record.act ?? ""
        if regranted.insert(act).inserted { spent.remove(act) }
    }

    private func session(for account: UUID?) async -> String? {
        if keychain == nil {
            let read = storage.read()
            keychain = read
            current = read
        }
        let act = account?.uuidString.lowercased()
        let step = SessionStep.next(stored: current, now: now(), spent: spent.contains(act ?? ""), act: act)
        switch step {
        case .use(let token): return token
        case .none: return nil
        case .renew, .attest:
            spent.insert(act ?? "")
            guard attester.isSupported, case .challenge(let challenge) = await client.challenge() else { return nil }
            if case .renew(let keyId) = step { return await renew(keyId: keyId, challenge: challenge, account: account) }
            return await attest(challenge: challenge, account: account)
        }
    }

    private func attest(challenge: String, account: UUID?) async -> String? {
        guard let key = await attester.attestNewKey(challenge: challenge) else { return nil }
        let outcome = await client.attest(keyId: key.keyId, attestation: key.attestation, challenge: challenge,
                                          account: account)
        return keep(outcome, keyId: key.keyId, account: account)
    }

    private func renew(keyId: String, challenge: String, account: UUID?) async -> String? {
        guard let assertion = await attester.assertion(keyId: keyId, challenge: challenge) else { return nil }
        let outcome = await client.renew(keyId: keyId, assertion: assertion, challenge: challenge, account: account)
        if outcome == .rejected {
            storage.remove()
            keychain = .absent
            current = .absent
            return nil
        }
        return keep(outcome, keyId: keyId, account: account)
    }

    private func keep(_ outcome: AttestOutcome, keyId: String, account: UUID?) -> String? {
        guard case .session(let token, let expiresAt) = outcome else { return nil }
        // The expiry on THIS device's clock - receipt plus the token's own lifetime - so a slow or fast clock never
        // rides a session past the Worker's exp (T-0322 B1); the reply's instant only when the token carries none.
        let expiry = SessionRecord.lifetime(of: token).map { now().addingTimeInterval($0) } ?? expiresAt
        let record = SessionRecord(keyId: keyId, token: token, expiresAt: expiry,
                                   act: account?.uuidString.lowercased())
        if storage.write(record, as: KeychainWrite.replacing(over: keychain ?? .absent)) { keychain = .valid(record) }
        current = .valid(record)
        return token
    }
}

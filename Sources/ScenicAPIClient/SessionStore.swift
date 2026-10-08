import Foundation

/// Production's `LedgerSessionProvider` (T-0310 R3, R4): the Worker session, read from the Keychain once and, when
/// it is missing or spent, obtained by App Attest - AT MOST ONE acquisition (a challenge, then an attest or an
/// assert) per launch, spent before its first request, so no answer and no 401 can make a launch ask twice.
///
/// A 401 hands the token back (`sessionRejected`): it is dropped for this launch and the next call renews if the
/// acquisition is unspent. An assertion the Worker rejects forgets the key, so the next launch attests a new one. No
/// session, for any reason, is nil: the ledger is not called and the Surprise history stays on the device.
public actor SessionStore: LedgerSessionProvider {
    let client: AttestClient
    let attester: any AppAttesting
    let storage: any SessionStorage
    let now: @Sendable () -> Date

    /// What the Keychain holds, as last read or written: it decides between add and update. nil until first read.
    private var keychain: KeychainRead<SessionRecord>?
    /// The session this launch works with: the Keychain's, a new one, or a dropped one.
    private var current: KeychainRead<SessionRecord> = .absent
    private var spent = false

    public init(client: AttestClient, attester: any AppAttesting, storage: any SessionStorage,
                now: @escaping @Sendable () -> Date) {
        self.client = client
        self.attester = attester
        self.storage = storage
        self.now = now
    }

    public func sessionToken() async -> String? {
        if keychain == nil {
            let read = storage.read()
            keychain = read
            current = read
        }
        let step = SessionStep.next(stored: current, now: now(), spent: spent)
        switch step {
        case .use(let token): return token
        case .none: return nil
        case .renew, .attest:
            spent = true
            guard attester.isSupported, case .challenge(let challenge) = await client.challenge() else { return nil }
            if case .renew(let keyId) = step { return await renew(keyId: keyId, challenge: challenge) }
            return await attest(challenge: challenge)
        }
    }

    public func sessionRejected(_ token: String) async {
        guard case .valid(let record) = current, record.token == token else { return }
        current = .valid(SessionRecord(keyId: record.keyId, token: record.token, expiresAt: .distantPast))
    }

    private func attest(challenge: String) async -> String? {
        guard let key = await attester.attestNewKey(challenge: challenge) else { return nil }
        let outcome = await client.attest(keyId: key.keyId, attestation: key.attestation, challenge: challenge)
        return keep(outcome, keyId: key.keyId)
    }

    private func renew(keyId: String, challenge: String) async -> String? {
        guard let assertion = await attester.assertion(keyId: keyId, challenge: challenge) else { return nil }
        let outcome = await client.renew(keyId: keyId, assertion: assertion, challenge: challenge)
        if outcome == .rejected {
            storage.remove()
            keychain = .absent
            current = .absent
            return nil
        }
        return keep(outcome, keyId: keyId)
    }

    private func keep(_ outcome: AttestOutcome, keyId: String) -> String? {
        guard case .session(let token, let expiresAt) = outcome else { return nil }
        let record = SessionRecord(keyId: keyId, token: token, expiresAt: expiresAt)
        if storage.write(record, as: KeychainWrite.replacing(over: keychain ?? .absent)) { keychain = .valid(record) }
        current = .valid(record)
        return token
    }
}

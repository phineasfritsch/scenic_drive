import Foundation

/// Production's `LedgerSessionProvider` (T-0310 R3, R4). STUB (RED).
public actor SessionStore: LedgerSessionProvider {
    let client: AttestClient
    let attester: any AppAttesting
    let storage: any SessionStorage
    let now: @Sendable () -> Date

    public init(client: AttestClient, attester: any AppAttesting, storage: any SessionStorage,
                now: @escaping @Sendable () -> Date) {
        self.client = client
        self.attester = attester
        self.storage = storage
        self.now = now
    }

    public func sessionToken() async -> String? { nil }

    public func sessionRejected(_ token: String) async {}
}

import Foundation

/// Where the session lives (T-0310 R5): production's is PlanAdapter `KeychainSessionStorage` (one generic-password
/// item, this device only, never synchronized). The store decides HOW to write (`KeychainWrite.replacing`); the
/// storage only performs it.
public protocol SessionStorage: Sendable {
    func read() -> KeychainRead<SessionRecord>
    /// true when the Keychain took the write.
    func write(_ record: SessionRecord, as write: KeychainWrite) -> Bool
    func remove()
}

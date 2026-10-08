import Foundation

/// The install id's Keychain decision (T-0307 R1, T-0310 R6). STUB (RED).
public struct InstallIDDecision: Equatable, Sendable {
    public let id: UUID
    public let write: KeychainWrite

    public init(id: UUID, write: KeychainWrite) {
        self.id = id
        self.write = write
    }

    public static func decide(keychain: KeychainRead<UUID>, defaults: UUID?, fresh: UUID) -> InstallIDDecision {
        InstallIDDecision(id: fresh, write: .skip)
    }
}

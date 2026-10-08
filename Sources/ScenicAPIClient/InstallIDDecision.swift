import Foundation

/// The install id's Keychain decision (T-0307 R1, T-0310 R6), pure: which id this launch uses and how it is written.
/// A valid Keychain id is used and nothing is written. Otherwise the id is the UserDefaults copy (T-0294 R7's
/// `plan.install.id`) or a fresh one, written the way `KeychainWrite.replacing` decides - a malformed item is
/// updated, never left in place; after a failed read nothing is written. PlanAdapter `StoredInstallID` performs the
/// write and keeps the UserDefaults copy when the Keychain refuses it.
public struct InstallIDDecision: Equatable, Sendable {
    public let id: UUID
    public let write: KeychainWrite

    public init(id: UUID, write: KeychainWrite) {
        self.id = id
        self.write = write
    }

    public static func decide(keychain: KeychainRead<UUID>, defaults: UUID?, fresh: UUID) -> InstallIDDecision {
        if case .valid(let id) = keychain { return InstallIDDecision(id: id, write: .skip) }
        return InstallIDDecision(id: defaults ?? fresh, write: KeychainWrite.replacing(over: keychain))
    }
}

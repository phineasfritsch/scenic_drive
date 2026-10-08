import Foundation
import ScenicAPIClient

/// This install's id (T-0260), kept in the Keychain since T-0307 R1: a generic-password item readable after the
/// first unlock, on THIS device only and never synchronized - iOS keeps it across a reinstall, so the ledger's
/// session sub (the install UUID) and its 90 days of Surprise history survive one. A random UUID: nothing about
/// the user or a place goes into it.
///
/// The decision is ScenicAPIClient `InstallIDDecision` (T-0310 R6), Linux-tested: a valid Keychain id is used; an
/// absent item is added and a malformed one UPDATED with T-0294 R7's UserDefaults `plan.install.id` (moved once,
/// then removed) or a fresh id; after a failed read (before the first unlock) the UserDefaults copy, or a fresh id
/// stored nowhere, is used and nothing is written. If the Keychain refuses the write the id is kept in UserDefaults,
/// so it stays the same id on every launch - never a fresh one.
struct StoredInstallID: InstallIDProvider {
    static let key = "plan.install.id"
    static let item = KeychainItem(service: "scenic.install", account: "install-id")

    func installID() -> UUID {
        let defaults = UserDefaults.standard
        let kept = defaults.string(forKey: Self.key).flatMap(UUID.init(uuidString:))
        let stored = Self.item.read { String(data: $0, encoding: .utf8).flatMap(UUID.init(uuidString:)) }
        let decision = InstallIDDecision.decide(keychain: stored, defaults: kept, fresh: UUID())
        guard decision.write != .skip else { return decision.id }
        if Self.item.write(Data(decision.id.uuidString.utf8), as: decision.write) {
            defaults.removeObject(forKey: Self.key)
        } else {
            defaults.set(decision.id.uuidString, forKey: Self.key)
        }
        return decision.id
    }
}

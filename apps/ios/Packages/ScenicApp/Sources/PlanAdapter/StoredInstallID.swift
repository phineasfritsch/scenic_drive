import Foundation
import ScenicAPIClient
import Security

/// This install's id (T-0260), kept in the Keychain since T-0307 R1: a generic-password item readable after the
/// first unlock, on THIS device only and never synchronized - iOS keeps it across a reinstall, so the ledger's
/// session sub (the install UUID) and its 90 days of Surprise history survive one. A random UUID: nothing about
/// the user or a place goes into it.
///
/// T-0294 R7 kept it in UserDefaults `plan.install.id`; a valid value there is moved into the Keychain once and the
/// defaults key removed. If the Keychain refuses the write, the id is kept in UserDefaults instead, so it stays the
/// same id on every launch - never a fresh one. A fresh id is minted and stored only when the Keychain answers that
/// no item exists (`errSecItemNotFound`) or holds one that is not a UUID; any other read failure (for example
/// `errSecInteractionNotAllowed` before the first unlock) reuses the UserDefaults copy, or, with none, answers a
/// fresh id for this call that is stored nowhere, so the Keychain's id is read again on the next call.
struct StoredInstallID: InstallIDProvider {
    static let key = "plan.install.id"
    static let service = "scenic.install"
    static let account = "install-id"

    func installID() -> UUID {
        let (status, stored) = Self.keychainID()
        if let stored { return stored }
        let defaults = UserDefaults.standard
        let kept = defaults.string(forKey: Self.key).flatMap(UUID.init(uuidString:))
        guard status == errSecItemNotFound || status == errSecSuccess else { return kept ?? UUID() }
        let id = kept ?? UUID()
        if Self.storeInKeychain(id) {
            defaults.removeObject(forKey: Self.key)
        } else {
            defaults.set(id.uuidString, forKey: Self.key)
        }
        return id
    }

    /// The item's identity: service, account, generic password, not synchronizable.
    static func itemQuery() -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: service,
         kSecAttrAccount as String: account,
         kSecAttrSynchronizable as String: false]
    }

    /// The read's status and the stored id - nil unless the status is `errSecSuccess` and the item holds a UUID.
    static func keychainID() -> (status: OSStatus, id: UUID?) {
        var query = itemQuery()
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        var found: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &found)
        guard status == errSecSuccess, let data = found as? Data,
              let text = String(data: data, encoding: .utf8) else { return (status, nil) }
        return (status, UUID(uuidString: text))
    }

    static func storeInKeychain(_ id: UUID) -> Bool {
        var item = itemQuery()
        item[kSecValueData as String] = Data(id.uuidString.utf8)
        item[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        return SecItemAdd(item as CFDictionary, nil) == errSecSuccess
    }
}

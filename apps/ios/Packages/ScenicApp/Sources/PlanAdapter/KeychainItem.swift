import Foundation
import ScenicAPIClient
import Security

/// One generic-password Keychain item (T-0307 R1, T-0310 R5, R6): readable after the first unlock, on THIS device
/// only, never synchronized. It reads into a `KeychainRead` and performs the write `KeychainWrite.replacing` decided:
/// an existing item, valid or not, is UPDATED in place (SecItemUpdate) - never left while the value moves elsewhere.
struct KeychainItem: Sendable {
    let service: String
    let account: String

    /// The item's identity: service, account, generic password, not synchronizable.
    func query() -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: service,
         kSecAttrAccount as String: account,
         kSecAttrSynchronizable as String: false]
    }

    /// absent on errSecItemNotFound; the parsed value, or malformed, on errSecSuccess; any other status a failure.
    func read<Value: Equatable & Sendable>(_ parse: (Data) -> Value?) -> KeychainRead<Value> {
        var request = query()
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        var found: CFTypeRef?
        let status = SecItemCopyMatching(request as CFDictionary, &found)
        switch status {
        case errSecItemNotFound:
            return .absent
        case errSecSuccess:
            guard let data = found as? Data, let value = parse(data) else { return .malformed }
            return .valid(value)
        default:
            return .failed(status)
        }
    }

    /// true when the Keychain took the write.
    func write(_ data: Data, as write: KeychainWrite) -> Bool {
        switch write {
        case .add:
            var item = query()
            item[kSecValueData as String] = data
            item[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
            return SecItemAdd(item as CFDictionary, nil) == errSecSuccess
        case .update:
            let change: [String: Any] = [kSecValueData as String: data,
                                         kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly]
            return SecItemUpdate(query() as CFDictionary, change as CFDictionary) == errSecSuccess
        case .skip:
            return false
        }
    }

    func remove() {
        _ = SecItemDelete(query() as CFDictionary)
    }
}

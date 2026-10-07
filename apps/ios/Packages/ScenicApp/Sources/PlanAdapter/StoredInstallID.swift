import Foundation
import ScenicAPIClient

/// This install's id for the Worker's per-device quota (T-0260): generated once, kept in UserDefaults until plan M6
/// moves it to the keychain (T-0294 R7). A random UUID - nothing about the user or a place goes into it.
struct StoredInstallID: InstallIDProvider {
    static let key = "plan.install.id"

    func installID() -> UUID {
        let defaults = UserDefaults.standard
        if let text = defaults.string(forKey: Self.key), let id = UUID(uuidString: text) {
            return id
        }
        let id = UUID()
        defaults.set(id.uuidString, forKey: Self.key)
        return id
    }
}

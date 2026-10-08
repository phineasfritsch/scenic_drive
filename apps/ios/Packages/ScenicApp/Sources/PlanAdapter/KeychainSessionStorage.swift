import Foundation
import ScenicAPIClient

/// The Worker session's Keychain item (T-0310 R5): service `scenic.session`, account `session`, this device only,
/// never synchronized; the value is `SessionRecord.data`. `SessionStore` decides add or update; this performs it.
struct KeychainSessionStorage: SessionStorage {
    static let item = KeychainItem(service: "scenic.session", account: "session")

    func read() -> KeychainRead<SessionRecord> {
        Self.item.read { SessionRecord(data: $0) }
    }

    func write(_ record: SessionRecord, as write: KeychainWrite) -> Bool {
        Self.item.write(record.data, as: write)
    }

    func remove() {
        Self.item.remove()
    }
}

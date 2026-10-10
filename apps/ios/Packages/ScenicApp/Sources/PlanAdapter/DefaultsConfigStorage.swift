import Foundation
import ScenicAPIClient

/// Where the app keeps its last good /config answer (T-0357 R4): UserDefaults, under one key. Only ConfigCache reads
/// or writes it, and it reads the bytes back through ConfigReader - bytes that do not read are as if absent.
struct DefaultsConfigStorage: ConfigStorage {
    static let key = "config.lastGood.v1"

    func load() -> Data? {
        UserDefaults.standard.data(forKey: Self.key)
    }

    func save(_ data: Data) {
        UserDefaults.standard.set(data, forKey: Self.key)
    }
}

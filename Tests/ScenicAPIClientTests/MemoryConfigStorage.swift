import Foundation
import ScenicAPIClient

/// A ConfigStorage in memory (T-0357): the bytes the cache last kept, and how many times it saved.
final class MemoryConfigStorage: ConfigStorage, @unchecked Sendable {
    private let lock = NSLock()
    private var bytes: Data?
    private var saveCount = 0

    init(_ bytes: Data? = nil) {
        self.bytes = bytes
    }

    var saves: Int {
        lock.lock()
        defer { lock.unlock() }
        return saveCount
    }

    func load() -> Data? {
        lock.lock()
        defer { lock.unlock() }
        return bytes
    }

    func save(_ data: Data) {
        lock.lock()
        defer { lock.unlock() }
        bytes = data
        saveCount += 1
    }
}

import Foundation
import ScenicAPIClient

/// A test's Keychain: answers one fixed read and records every write (with how it was asked to write) and remove.
final class MemorySessionStorage: SessionStorage, @unchecked Sendable {
    struct Write: Equatable {
        let record: SessionRecord
        let write: KeychainWrite
    }

    private let lock = NSLock()
    private let initial: KeychainRead<SessionRecord>
    private var recorded: [Write] = []
    private var removed = 0

    init(_ initial: KeychainRead<SessionRecord>) {
        self.initial = initial
    }

    var writes: [Write] {
        lock.lock()
        defer { lock.unlock() }
        return recorded
    }

    var removes: Int {
        lock.lock()
        defer { lock.unlock() }
        return removed
    }

    func read() -> KeychainRead<SessionRecord> { initial }

    func write(_ record: SessionRecord, as write: KeychainWrite) -> Bool {
        lock.lock()
        recorded.append(Write(record: record, write: write))
        lock.unlock()
        return true
    }

    func remove() {
        lock.lock()
        removed += 1
        lock.unlock()
    }
}

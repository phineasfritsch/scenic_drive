import Foundation
import ScenicAPIClient

/// T-0360: an in-memory WaitlistMemory - the cells this "install" has joined, in the order they were remembered.
final class MemoryWaitlist: WaitlistMemory, @unchecked Sendable {
    private let lock = NSLock()
    private var cells: [String]

    init(_ cells: [String] = []) {
        self.cells = cells
    }

    var remembered: [String] {
        lock.lock()
        defer { lock.unlock() }
        return cells
    }

    func hasJoined(_ cell: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }
        return cells.contains(cell)
    }

    func rememberJoined(_ cell: String) {
        lock.lock()
        cells.append(cell)
        lock.unlock()
    }
}

import Foundation

/// T-0360: the injected `cellOf` of a WaitlistClient under test - answers one fixed cell (or a per-point table) and
/// records every (latitude, longitude) it was asked for, so a test compares what reached it exactly.
final class RecordingCellOf: @unchecked Sendable {
    private let lock = NSLock()
    private var calls: [[Double]] = []
    private let answer: @Sendable (Double, Double) -> String?

    init(_ cell: String?) {
        answer = { _, _ in cell }
    }

    init(answer: @escaping @Sendable (Double, Double) -> String?) {
        self.answer = answer
    }

    var asked: [[Double]] {
        lock.lock()
        defer { lock.unlock() }
        return calls
    }

    func cell(_ latitude: Double, _ longitude: Double) -> String? {
        lock.lock()
        calls.append([latitude, longitude])
        lock.unlock()
        return answer(latitude, longitude)
    }
}

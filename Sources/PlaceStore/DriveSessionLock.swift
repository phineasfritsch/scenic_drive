import Foundation

/// Whether a drive holds the corpus store (T-0300 O7). A drive takes a `DriveSessionToken` for as long as it reads
/// the store; `CorpusUpdater.openForLaunch` never swaps a corpus while any token is alive (plan: "never while a
/// Drive holds a connection"). NSLock-guarded: Synchronization.Mutex needs macOS 15 and the package floor is 14.
public final class DriveSessionLock: @unchecked Sendable {
    private let lock = NSLock()
    private var held = 0

    public init() {}

    public func hold() -> DriveSessionToken {
        lock.lock()
        held += 1
        lock.unlock()
        return DriveSessionToken(owner: self)
    }

    public var isHeld: Bool {
        lock.lock()
        defer { lock.unlock() }
        return held > 0
    }

    func release() {
        lock.lock()
        held -= 1
        lock.unlock()
    }
}

import Foundation

/// One drive's hold on the corpus store (T-0300 O7), from `DriveSessionLock.hold()`. Released once: by `end()` or,
/// if the drive never calls it, when the token is deallocated. A second `end()` releases nothing.
public final class DriveSessionToken: @unchecked Sendable {
    private let owner: DriveSessionLock
    private let lock = NSLock()
    private var ended = false

    init(owner: DriveSessionLock) {
        self.owner = owner
    }

    public func end() {
        lock.lock()
        let first = !ended
        ended = true
        lock.unlock()
        if first {
            owner.release()
        }
    }

    deinit {
        end()
    }
}

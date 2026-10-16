import Foundation

/// The install-id provider TelemetryClientTests hands the client (T-0367): a test sets `id` between records, as a
/// confirmed account deletion replaces the stored install id, and `read` is the closure the client calls.
final class ScriptedInstallID: @unchecked Sendable {
    private let lock = NSLock()
    private var current: UUID

    init(_ id: UUID) {
        current = id
    }

    var id: UUID {
        get { lock.withLock { current } }
        set { lock.withLock { current = newValue } }
    }

    var read: @Sendable () -> UUID {
        { [self] in id }
    }
}

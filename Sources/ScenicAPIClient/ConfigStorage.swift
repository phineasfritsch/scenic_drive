import Foundation

/// Where ConfigCache keeps the last good /config answer (T-0357 R4): the app's is UserDefaults (PlanAdapter), the
/// tests' is memory. Bytes in, bytes out; ConfigReader is the only reader of them.
public protocol ConfigStorage: Sendable {
    func load() -> Data?
    func save(_ data: Data)
}

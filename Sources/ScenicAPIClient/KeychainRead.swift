import Foundation

/// What a Keychain read found (T-0310 R6): nothing, a value of the expected shape, an item that is not the
/// expected shape, or a read that failed with an OSStatus (for example before the first unlock).
public enum KeychainRead<Value: Equatable & Sendable>: Equatable, Sendable {
    case absent
    case valid(Value)
    case malformed
    case failed(Int32)
}

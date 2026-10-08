import Foundation

/// How a new value goes into a Keychain item (T-0310 R6). STUB (RED).
public enum KeychainWrite: Equatable, Sendable {
    case add
    case update
    case skip

    public static func replacing<Value>(over read: KeychainRead<Value>) -> KeychainWrite {
        .skip
    }
}

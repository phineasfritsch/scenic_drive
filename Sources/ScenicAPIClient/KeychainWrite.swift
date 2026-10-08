import Foundation

/// How a new value goes into a Keychain item (T-0310 R6) - replace semantics, decided from what the read found. An
/// item that exists is UPDATED in place whether or not it held the expected shape (rv2-t0307: an add over a
/// malformed item fails errSecDuplicateItem and the value silently lived elsewhere); an absent one is added; after a
/// failed read nothing is written, because nothing is known about the item.
public enum KeychainWrite: Equatable, Sendable {
    case add
    case update
    case skip

    public static func replacing<Value>(over read: KeychainRead<Value>) -> KeychainWrite {
        switch read {
        case .absent: return .add
        case .valid, .malformed: return .update
        case .failed: return .skip
        }
    }
}

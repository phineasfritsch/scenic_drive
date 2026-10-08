import Foundation

/// The session as the Keychain holds it (T-0310 R5). STUB (RED).
public struct SessionRecord: Equatable, Sendable {
    public let keyId: String
    public let token: String
    public let expiresAt: Date

    public init(keyId: String, token: String, expiresAt: Date) {
        self.keyId = keyId
        self.token = token
        self.expiresAt = expiresAt
    }

    public init?(data: Data) {
        return nil
    }

    public var data: Data { Data() }
}

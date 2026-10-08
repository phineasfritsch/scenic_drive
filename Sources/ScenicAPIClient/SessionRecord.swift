import Foundation

/// The session as the Keychain holds it (T-0310 R5): the attested key's id (for renewing), the session JWT and its
/// expiry in whole seconds. Stored as sorted-key JSON {expires_at, key_id, token}; `init?(data:)` admits exactly the
/// bytes `data` would write, so any other item - extra keys, another order, a fractional or string expiry, an empty
/// field - is malformed and is replaced, never trusted.
public struct SessionRecord: Equatable, Sendable {
    public let keyId: String
    public let token: String
    public let expiresAt: Date

    public init(keyId: String, token: String, expiresAt: Date) {
        self.keyId = keyId
        self.token = token
        self.expiresAt = expiresAt
    }

    private struct Wire: Codable {
        let expires_at: Int64
        let key_id: String
        let token: String
    }

    public init?(data: Data) {
        guard let wire = try? JSONDecoder().decode(Wire.self, from: data), !wire.key_id.isEmpty, !wire.token.isEmpty
        else { return nil }
        self.init(keyId: wire.key_id, token: wire.token,
                  expiresAt: Date(timeIntervalSince1970: TimeInterval(wire.expires_at)))
        guard self.data == data else { return nil }
    }

    public var data: Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        let wire = Wire(expires_at: Int64(expiresAt.timeIntervalSince1970.rounded(.down)), key_id: keyId, token: token)
        // Two strings and an integer: this encoder cannot throw on them.
        return (try? encoder.encode(wire)) ?? Data()
    }
}

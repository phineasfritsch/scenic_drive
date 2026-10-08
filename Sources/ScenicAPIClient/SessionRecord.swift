import Foundation

/// The session as the Keychain holds it (T-0310 R5): the attested key's id (for renewing), the session JWT and its
/// expiry in whole seconds. Stored as sorted-key JSON {expires_at, key_id, token}; `init?(data:)` admits exactly the
/// bytes `data` would write, so any other item - extra keys, another order, a fractional or string expiry, an empty
/// field - is malformed and is replaced, never trusted.
public struct SessionRecord: Equatable, Sendable {
    public let keyId: String
    public let token: String
    public let expiresAt: Date
    public let act: String?

    public init(keyId: String, token: String, expiresAt: Date, act: String? = nil) {
        self.keyId = keyId
        self.token = token
        self.expiresAt = expiresAt
        self.act = act
    }

    /// The token's own lifetime, `exp - iat` from its payload (T-0322 B1): the Worker's span, which no device clock
    /// skews. nil unless the payload is base64url JSON with integer iat and exp, exp after iat.
    public static func lifetime(of token: String) -> TimeInterval? {
        let parts = token.split(separator: ".", omittingEmptySubsequences: false)
        guard parts.count == 3 else { return nil }
        var payload = parts[1].replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")
        payload += String(repeating: "=", count: (4 - payload.count % 4) % 4)
        guard let data = Data(base64Encoded: payload), let claims = try? JSONDecoder().decode(Claims.self, from: data),
              claims.exp > claims.iat
        else { return nil }
        return TimeInterval(claims.exp - claims.iat)
    }

    private struct Claims: Decodable {
        let iat: Int64
        let exp: Int64
    }

    private struct Wire: Codable {
        let act: String?
        let expires_at: Int64
        let key_id: String
        let token: String
    }

    public init?(data: Data) {
        guard let wire = try? JSONDecoder().decode(Wire.self, from: data), !wire.key_id.isEmpty, !wire.token.isEmpty,
              wire.act?.isEmpty != true
        else { return nil }
        self.init(keyId: wire.key_id, token: wire.token,
                  expiresAt: Date(timeIntervalSince1970: TimeInterval(wire.expires_at)), act: wire.act)
        guard self.data == data else { return nil }
    }

    public var data: Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        let wire = Wire(act: act, expires_at: Int64(expiresAt.timeIntervalSince1970.rounded(.down)), key_id: keyId, token: token)
        // Two strings and an integer: this encoder cannot throw on them.
        return (try? encoder.encode(wire)) ?? Data()
    }
}

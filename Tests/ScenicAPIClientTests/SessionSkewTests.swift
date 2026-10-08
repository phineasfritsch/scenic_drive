import Foundation
import ScenicAPIClient
import Testing

/// T-0322 B1(b): a session's expiry is kept on the DEVICE's clock - receipt plus the token's own `exp - iat` - so a
/// device clock any amount slow never rides a session the Worker has expired (the Worker reads an unverifiable Bearer
/// as none), and a fast one never renews early. Every write and request is compared WHOLE; each row's expectation is
/// a function of its variant, computed here from the rule.
@Suite("SessionSkewTests")
struct SessionSkewTests {
    static let header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    /// The Worker's issue instant in whole seconds: AttestWire.now, 2026-10-08T02:00:00Z.
    static let issued = Int64(AttestWire.now.timeIntervalSince1970)

    static func base64url(_ text: String) -> String {
        Data(text.utf8).base64EncodedString().replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "=", with: "")
    }

    static func token(_ payload: String) -> String { "\(header).\(base64url(payload)).c2ln" }

    static let hour = token("{\"iss\":\"scenic-api\",\"sub\":\"\(AttestWire.deviceWire)\",\"iat\":\(issued),"
                            + "\"exp\":\(issued + 3600)}")

    /// (name, token, the lifetime the rule reads from it).
    static let lifetimes: [(String, String, TimeInterval?)] = [
        ("the Worker's hour", hour, 3600),
        ("exp one second after iat (bound)", token("{\"iat\":1000,\"exp\":1001}"), 1),
        ("exp equal to iat (bound)", token("{\"iat\":1000,\"exp\":1000}"), nil),
        ("exp one second before iat", token("{\"iat\":1000,\"exp\":999}"), nil),
        ("a fractional iat", token("{\"iat\":1000.5,\"exp\":1001}"), nil),
        ("iat as a string", token("{\"iat\":\"1000\",\"exp\":1001}"), nil),
        ("no exp", token("{\"iat\":1000}"), nil),
        ("a payload that is not JSON", AttestWire.newToken, nil),
        ("two parts", "\(header).\(base64url("{\"iat\":1000,\"exp\":1001}"))", nil),
        ("four parts", "\(token("{\"iat\":1000,\"exp\":1001}")).x", nil),
        ("unpadded, 1 byte over", token("{\"iat\":1000,\"exp\":1060,\"p\":\"\"}"), 60),
        ("unpadded, 2 bytes over", token("{\"iat\":1000,\"exp\":1060,\"p\":\"a\"}"), 60),
        ("unpadded, 0 bytes over", token("{\"iat\":1000,\"exp\":1060,\"p\":\"ab\"}"), 60),
        ("base64url '-'", token("{\"iat\":1000,\"exp\":1060,\"p\":\"~~~~\"}"), 60),
        ("base64url '_'", token("{\"iat\":1000,\"exp\":1060,\"p\":\"????\"}"), 60),
    ]

    @Test("the padding and alphabet rows exercise what they are named for")
    func rowsExerciseTheirShape() {
        let payloads = Dictionary(uniqueKeysWithValues: Self.lifetimes.map { ($0.0, $0.1.split(separator: ".")[1]) })
        #expect([1, 2, 3, 0].map { r in payloads.values.contains { $0.count % 4 == r } } == [false, true, true, true])
        #expect(payloads["base64url '-'"]!.contains("-") && payloads["base64url '_'"]!.contains("_"))
    }

    @Test("a token's lifetime is exactly exp - iat of its payload, at every bound", arguments: lifetimes)
    func lifetime(_ row: (String, String, TimeInterval?)) {
        #expect(SessionRecord.lifetime(of: row.1) == row.2)
    }

    /// Device clock offsets from the Worker's, in seconds: slow (negative) and fast, either side of the margin.
    static let offsets: [TimeInterval] = [-7200, -3600, -61, -60, 0, 60, 61, 3600]
    /// Seconds since receipt at the next launch: the last one used, the first one not.
    static let elapsed: [TimeInterval] = [3539, 3540, 3541]

    @Test("a session is kept on the device's clock and used for exactly lifetime - margin seconds after receipt",
          arguments: offsets, elapsed)
    func skew(_ offset: TimeInterval, _ after: TimeInterval) async {
        await check(token: Self.hour, offset: offset, after: after,
                    expiry: AttestWire.now.addingTimeInterval(offset + 3600), used: after < 3600 - 60)
    }

    @Test("a token with no readable lifetime keeps the reply's expires_at", arguments: [-61.0, 0], [3539.0, 3540])
    func fallback(_ offset: TimeInterval, _ after: TimeInterval) async {
        await check(token: AttestWire.newToken, offset: offset, after: after, expiry: AttestWire.expires,
                    used: 3600 - offset - after > 60)
    }

    /// Launch 1 at Worker time + `offset` attests and writes; launch 2, `after` seconds later on the same clock, uses
    /// the record with no request or renews it by its key.
    func check(token: String, offset: TimeInterval, after: TimeInterval, expiry: Date, used: Bool) async {
        let reply = AttestWire.reply(200, "{\"token\":\"\(token)\",\"expires_at\":\"2026-10-08T03:00:00.000Z\"}")
        let replies = ["POST /attest/challenge": [AttestWire.challengeReply], "POST /attest": [reply],
                       "POST /attest/assert": [AttestWire.sessionReply]]
        let first = ScriptedTransport(replies)
        let storage = MemorySessionStorage(.absent)
        let received = AttestWire.now.addingTimeInterval(offset)
        let launch1 = SessionStore(client: AttestWire.client(first), attester: FakeAttester(isSupported: true),
                                   storage: storage, account: nil, now: { received })
        #expect(await launch1.planSession(account: nil) == token)
        let kept = SessionRecord(keyId: AttestWire.newKey, token: token, expiresAt: expiry, act: nil)
        #expect(storage.writes == [.init(record: kept, write: .add)])
        #expect(await first.requests == [AttestWire.challengeRequest(),
                                         SessionAccountTests.attestRequest(AttestWire.newKey, act: nil)])

        let second = ScriptedTransport(replies)
        let later = received.addingTimeInterval(after)
        let launch2 = SessionStore(client: AttestWire.client(second), attester: FakeAttester(isSupported: true),
                                   storage: MemorySessionStorage(.valid(kept)), account: nil, now: { later })
        #expect(await launch2.planSession(account: nil) == (used ? token : AttestWire.newToken))
        #expect(await second.requests == (used ? [] : [AttestWire.challengeRequest(),
                                                        SessionAccountTests.renewRequest(AttestWire.newKey, act: nil)]))
    }
}

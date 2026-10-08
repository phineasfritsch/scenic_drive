import Foundation
import ScenicAPIClient
import Testing

/// T-0310 acceptance 2 (R1, R2): each App Attest request by full equality to its recomputation, and every Worker
/// answer one typed outcome after exactly one request. Every case drives `AttestClient`, the calls `SessionStore`
/// makes in production.
@Suite("AttestClientTests") struct AttestClientTests {
    enum Call: String, Sendable, CaseIterable {
        case challenge
        case attest
        case renew
    }

    static func call(_ call: Call, _ client: AttestClient) async -> AttestOutcome {
        switch call {
        case .challenge: return await client.challenge()
        case .attest: return await client.attest(keyId: AttestWire.newKey, attestation: AttestWire.attestation,
                                                 challenge: AttestWire.challenge)
        case .renew: return await client.renew(keyId: AttestWire.oldKey, assertion: AttestWire.assertion,
                                               challenge: AttestWire.challenge)
        }
    }

    @Test("Each App Attest request is exactly its URL, its one header and its sorted-key body")
    func requests() async {
        let fake = CountingPlanTransport(reply: AttestWire.reply(503, "{\"error\":\"attest_unavailable\"}"))
        let client = AttestWire.client(fake)
        for c in Call.allCases { _ = await Self.call(c, client) }
        #expect(await fake.requests == [AttestWire.challengeRequest(), AttestWire.attestRequest(),
                                        AttestWire.renewRequest(AttestWire.oldKey)])
    }

    struct Row: Sendable, CustomTestStringConvertible {
        let status: Int
        let body: String
        let challenge: AttestOutcome
        let session: AttestOutcome
        var testDescription: String { "\(status) \(body)" }
    }

    static let tooShort = String(AttestWire.challenge.dropLast())
    static let plusSign = "+" + AttestWire.challenge.dropFirst()

    static let rows: [Row] = [
        Row(status: 200, body: "{\"challenge\":\"\(AttestWire.challenge)\",\"expires_at\":\"2026-10-08T02:05:00.000Z\"}",
            challenge: .challenge(AttestWire.challenge), session: .unreadable),
        Row(status: 200, body: "{\"token\":\"\(AttestWire.newToken)\",\"expires_at\":\"2026-10-08T03:00:00.000Z\"}",
            challenge: .unreadable, session: .session(token: AttestWire.newToken, expiresAt: AttestWire.expires)),
        Row(status: 200, body: "{\"challenge\":\"\(tooShort)\",\"expires_at\":\"2026-10-08T02:05:00.000Z\"}",
            challenge: .unreadable, session: .unreadable),
        Row(status: 200, body: "{\"challenge\":\"\(AttestWire.challenge)a\",\"expires_at\":\"2026-10-08T02:05:00.000Z\"}",
            challenge: .unreadable, session: .unreadable),
        Row(status: 200, body: "{\"challenge\":\"\(plusSign)\",\"expires_at\":\"2026-10-08T02:05:00.000Z\"}",
            challenge: .unreadable, session: .unreadable),
        Row(status: 200, body: "{\"challenge\":\"\(AttestWire.challenge)\"}", challenge: .unreadable, session: .unreadable),
        Row(status: 200, body: "{\"challenge\":\"\(AttestWire.challenge)\",\"expires_at\":\"soon\"}",
            challenge: .unreadable, session: .unreadable),
        Row(status: 200, body: "{\"token\":\"\",\"expires_at\":\"2026-10-08T03:00:00.000Z\"}",
            challenge: .unreadable, session: .unreadable),
        Row(status: 200, body: "{\"token\":\"\(AttestWire.newToken)\",\"expires_at\":\"later\"}",
            challenge: .unreadable, session: .unreadable),
        Row(status: 200, body: "not json", challenge: .unreadable, session: .unreadable),
        Row(status: 400, body: "{\"error\":\"invalid_attestation\"}", challenge: .rejected, session: .rejected),
        Row(status: 400, body: "{\"error\":\"invalid_assertion\"}", challenge: .rejected, session: .rejected),
        Row(status: 401, body: "{\"error\":\"unauthorized\"}", challenge: .unexpected(401), session: .unexpected(401)),
        Row(status: 405, body: "{\"error\":\"POST only\"}", challenge: .methodRefused, session: .methodRefused),
        Row(status: 429, body: "{\"error\":\"challenge_rate_limited\"}", challenge: .rateLimited, session: .rateLimited),
        Row(status: 429, body: "{\"error\":\"rate_limited\"}", challenge: .unexpected(429), session: .unexpected(429)),
        Row(status: 429, body: "", challenge: .unexpected(429), session: .unexpected(429)),
        Row(status: 500, body: "", challenge: .unexpected(500), session: .unexpected(500)),
        Row(status: 503, body: "{\"error\":\"attest_unavailable\"}", challenge: .unavailable, session: .unavailable),
    ]

    @Test("Every Worker answer is one typed outcome after exactly one request - never a retry", arguments: rows)
    func answers(_ row: Row) async {
        for c in Call.allCases {
            let fake = CountingPlanTransport(reply: AttestWire.reply(row.status, row.body))
            let outcome = await Self.call(c, AttestWire.client(fake))
            #expect(outcome == (c == .challenge ? row.challenge : row.session), "\(c.rawValue)")
            #expect(await fake.count == 1, "\(c.rawValue)")
        }
    }

    /// attest.ts CHALLENGE at every bound of every class: 0 9 A Z a z - _ admitted; each neighbour just outside a
    /// class ('/' 47, ':' 58, '@' 64, '[' 91, '`' 96, '{' 123, ',' 44, '.' 46, '^' 94) and '+' refused - each put at
    /// every one of the 43 positions of a valid challenge, so whether it is read is a function of the character alone.
    static let challengeCharacters: [(Character, Bool)] = [
        ("0", true), ("9", true), ("A", true), ("Z", true), ("a", true), ("z", true), ("-", true), ("_", true),
        ("/", false), (":", false), ("@", false), ("[", false), ("`", false), ("{", false), (",", false),
        (".", false), ("^", false), ("+", false),
    ]

    static func challengeReply(_ challenge: String) -> PlanHTTPReply {
        AttestWire.reply(200, "{\"challenge\":\"\(challenge)\",\"expires_at\":\"2026-10-08T02:05:00.000Z\"}")
    }

    @Test("Every challenge position admits exactly 0-9, A-Z, a-z, '-' and '_', at both bounds of each class",
          arguments: challengeCharacters)
    func challengeClass(_ character: Character, _ admitted: Bool) async {
        for position in 0..<43 {
            var characters = Array(AttestWire.challenge)
            characters[position] = character
            let text = String(characters)
            let fake = CountingPlanTransport(reply: Self.challengeReply(text))
            #expect(await AttestWire.client(fake).challenge() == (admitted ? .challenge(text) : .unreadable), "\(text)")
            #expect(await fake.count == 1, "\(text)")
        }
    }

    @Test("A challenge is read at exactly 43 characters", arguments: [0, 1, 42, 43, 44, 86])
    func challengeLength(_ length: Int) async {
        let text = String(String(repeating: "az", count: 43).prefix(length))
        let fake = CountingPlanTransport(reply: Self.challengeReply(text))
        #expect(await AttestWire.client(fake).challenge() == (length == 43 ? .challenge(text) : .unreadable))
    }

    @Test("No reply at all is offline, after exactly one request")
    func offline() async {
        for c in Call.allCases {
            let fake = CountingPlanTransport.offline()
            #expect(await Self.call(c, AttestWire.client(fake)) == .offline)
            #expect(await fake.count == 1)
        }
    }
}

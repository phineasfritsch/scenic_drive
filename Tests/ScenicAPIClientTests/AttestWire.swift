import Foundation
import ScenicAPIClient

/// The App Attest wire the T-0310 tests share: fixed values, and every request built here by string interpolation -
/// the recomputation each test compares the client's whole request to (memory full-equality-oracle).
enum AttestWire {
    static let base = URL(string: "https://scenic-api.test")!
    static let device = "0F8B2C3D-4E5F-4A6B-8C7D-9E0F1A2B3C4D"
    static let deviceWire = "0f8b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
    static let challenge = "q1w2e3r4t5y6u7i8o9p0-_ASDFGHJKLZXCVBNMqwert"
    static let newKey = "AbC+/0123456789abcdefghijklmnopqrstuvwxyzAB="
    static let oldKey = "ZyX+/9876543210zyxwvutsrqponmlkjihgfedcbaZY="
    static let attestation = "o2NmbXQ+/w=="
    static let assertion = "omlzaWduYXR1cmU+/A=="
    static let newToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.bmV3.c2lnLW5ldw"
    static let oldToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.b2xk.c2lnLW9sZA"
    static let now = utc(2026, 10, 8, 2, 0, 0)
    static let expires = utc(2026, 10, 8, 3, 0, 0)

    static func utc(_ year: Int, _ month: Int, _ day: Int, _ hour: Int, _ minute: Int, _ second: Int) -> Date {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "UTC")!
        return calendar.date(from: DateComponents(year: year, month: month, day: day, hour: hour, minute: minute,
                                                  second: second))!
    }

    static func reply(_ status: Int, _ body: String) -> PlanHTTPReply {
        PlanHTTPReply(status: status, body: Data(body.utf8))
    }

    static let challengeReply = reply(200, "{\"challenge\":\"\(challenge)\",\"expires_at\":\"2026-10-08T02:05:00.000Z\"}")
    static let sessionReply = reply(200, "{\"token\":\"\(newToken)\",\"expires_at\":\"2026-10-08T03:00:00.000Z\"}")

    static func client(_ transport: any PlanTransport) -> AttestClient {
        AttestClient(base: base, transport: transport, device: FixedInstallID(device))
    }

    static func challengeRequest() -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/attest/challenge")!, method: "POST",
                        headers: ["x-scenic-device": deviceWire], body: Data())
    }

    static func attestRequest(_ keyId: String = newKey) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/attest")!, method: "POST",
                        headers: ["content-type": "application/json"],
                        body: Data(("{\"attestation\":\"\(attestation)\",\"challenge\":\"\(challenge)\",\"device\":\""
                                    + "\(deviceWire)\",\"keyId\":\"\(keyId)\"}").utf8))
    }

    static func renewRequest(_ keyId: String) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/attest/assert")!, method: "POST",
                        headers: ["content-type": "application/json"],
                        body: Data("{\"assertion\":\"\(assertion)\",\"challenge\":\"\(challenge)\",\"keyId\":\"\(keyId)\"}".utf8))
    }

    static func ledgerPost(_ token: String, _ placeId: String, _ cell: String) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/ledger")!, method: "POST",
                        headers: ["authorization": "Bearer \(token)", "content-type": "application/json"],
                        body: Data("{\"cell\":\"\(cell)\",\"place_id\":\"\(placeId)\"}".utf8))
    }

    /// A stored session for `oldKey`, expiring `seconds` after `now`.
    static func stored(_ seconds: TimeInterval) -> SessionRecord {
        SessionRecord(keyId: oldKey, token: oldToken, expiresAt: now.addingTimeInterval(seconds))
    }
}

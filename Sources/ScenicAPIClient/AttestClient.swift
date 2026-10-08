import Foundation

/// The app's client for the Worker's App Attest routes (T-0278, T-0280; T-0310 R1): POST /attest/challenge,
/// POST /attest (a new key's attestation) and POST /attest/assert (an attested key renewing its session).
///
/// One call, at most one request, one `AttestOutcome` - nothing is retried. The challenge carries
/// `x-scenic-device` (the install id, the Worker's per-device challenge limit) and no body; /attest carries the same
/// id as `device`; /attest/assert carries no device at all - the Worker reads it from the attested key.
public struct AttestClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let device: any InstallIDProvider

    public init(base: URL, transport: any PlanTransport, device: any InstallIDProvider) {
        self.base = base
        self.transport = transport
        self.device = device
    }

    /// POST /attest/challenge: a single-use challenge for one attestation or assertion.
    public func challenge() async -> AttestOutcome {
        await send(PlanHTTPRequest(url: base.appendingPathComponent("attest/challenge"), method: "POST",
                                   headers: ["x-scenic-device": deviceID], body: Data()), call: .challenge)
    }

    /// POST /attest {attestation, challenge, device, keyId}: a new key's attestation -> a session.
    public func attest(keyId: String, attestation: String, challenge: String) async -> AttestOutcome {
        let body = Self.body(["attestation": attestation, "challenge": challenge, "device": deviceID, "keyId": keyId])
        return await send(PlanHTTPRequest(url: base.appendingPathComponent("attest"), method: "POST",
                                          headers: ["content-type": "application/json"], body: body), call: .session)
    }

    /// POST /attest/assert {assertion, challenge, keyId}: an attested key's assertion -> a renewed session.
    public func renew(keyId: String, assertion: String, challenge: String) async -> AttestOutcome {
        let body = Self.body(["assertion": assertion, "challenge": challenge, "keyId": keyId])
        return await send(PlanHTTPRequest(url: base.appendingPathComponent("attest/assert"), method: "POST",
                                          headers: ["content-type": "application/json"], body: body), call: .session)
    }

    private var deviceID: String { device.installID().uuidString.lowercased() }

    /// Sorted keys, slashes as they are: every value is a base64 or base64url string, a UUID or a challenge.
    static func body(_ fields: [String: String]) -> Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        // A dictionary of strings: this encoder cannot throw on it.
        return (try? encoder.encode(fields)) ?? Data()
    }

    private func send(_ request: PlanHTTPRequest, call: AttestReplyReader.Call) async -> AttestOutcome {
        do {
            return AttestReplyReader.read(try await transport.send(request), call: call)
        } catch {
            return .offline
        }
    }
}

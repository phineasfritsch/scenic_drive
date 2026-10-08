import Foundation

/// The app's client for the Worker's App Attest routes (T-0278, T-0280; T-0310 R1). STUB (RED).
public struct AttestClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let device: any InstallIDProvider

    public init(base: URL, transport: any PlanTransport, device: any InstallIDProvider) {
        self.base = base
        self.transport = transport
        self.device = device
    }

    public func challenge() async -> AttestOutcome { .offline }

    public func attest(keyId: String, attestation: String, challenge: String) async -> AttestOutcome { .offline }

    public func renew(keyId: String, assertion: String, challenge: String) async -> AttestOutcome { .offline }
}

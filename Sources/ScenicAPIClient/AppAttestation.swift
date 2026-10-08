import Foundation

/// A new App Attest key and Apple's attestation of it, both base64 as DCAppAttestService hands them over and as
/// POST /attest takes them (T-0278 R2).
public struct AppAttestation: Equatable, Sendable {
    public let keyId: String
    public let attestation: String

    public init(keyId: String, attestation: String) {
        self.keyId = keyId
        self.attestation = attestation
    }
}

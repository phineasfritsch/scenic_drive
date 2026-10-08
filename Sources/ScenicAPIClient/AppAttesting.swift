import Foundation

/// The device's App Attest service (T-0310 R3). Production's conformer is PlanAdapter `DeviceAppAttester`
/// (DCAppAttestService, Apple-only); both of its hashes are SHA256 of the UTF-8 challenge as issued, the
/// clientDataHash appAttest.ts and appAssert.ts recompute. nil is "no attestation" - the session stays absent.
public protocol AppAttesting: Sendable {
    /// false on the simulator and on devices without the Secure Enclave: no request is made at all.
    var isSupported: Bool { get }
    /// A new key, attested over the challenge.
    func attestNewKey(challenge: String) async -> AppAttestation?
    /// An assertion by the attested key `keyId` over the challenge, base64.
    func assertion(keyId: String, challenge: String) async -> String?
}

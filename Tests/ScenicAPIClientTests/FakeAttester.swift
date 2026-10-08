import Foundation
import ScenicAPIClient

/// A test's App Attest service: supported or not, always the same new key and the same assertion (T-0310).
struct FakeAttester: AppAttesting {
    let isSupported: Bool

    func attestNewKey(challenge: String) async -> AppAttestation? {
        AppAttestation(keyId: AttestWire.newKey, attestation: AttestWire.attestation)
    }

    func assertion(keyId: String, challenge: String) async -> String? { AttestWire.assertion }
}

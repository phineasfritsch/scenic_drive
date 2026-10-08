import CryptoKit
import DeviceCheck
import Foundation
import ScenicAPIClient

/// The device's App Attest service (T-0310 R3): DCAppAttestService, whose clientDataHash is SHA256 of the UTF-8
/// challenge exactly as the Worker issued it - what appAttest.ts and appAssert.ts recompute. Unsupported (the
/// simulator) the session store sends nothing; any error is nil, and the session stays absent this launch.
struct DeviceAppAttester: AppAttesting {
    var isSupported: Bool { DCAppAttestService.shared.isSupported }

    func attestNewKey(challenge: String) async -> AppAttestation? {
        let service = DCAppAttestService.shared
        do {
            let keyId = try await service.generateKey()
            let attestation = try await service.attestKey(keyId, clientDataHash: Self.hash(challenge))
            return AppAttestation(keyId: keyId, attestation: attestation.base64EncodedString())
        } catch {
            return nil
        }
    }

    func assertion(keyId: String, challenge: String) async -> String? {
        do {
            let assertion = try await DCAppAttestService.shared.generateAssertion(keyId,
                                                                                  clientDataHash: Self.hash(challenge))
            return assertion.base64EncodedString()
        } catch {
            return nil
        }
    }

    static func hash(_ challenge: String) -> Data {
        Data(SHA256.hash(data: Data(challenge.utf8)))
    }
}

import Foundation
import ScenicAPIClient

/// The launch's ONE Worker session store (T-0322 R8): App Attest, the Keychain item and the StoreKit purchase, shared by
/// the Surprise ledger and the three plan-family planners, so the one acquisition per purchase value per launch
/// (SessionStore) is one store's and a session renewed for a purchase serves every caller. nil without an https base
/// URL (LivePlanner's `plan.base.url`): no session, nothing sent, and the planners carry no Bearer.
enum LiveSession {
    static let store: SessionStore? = build()

    static func build() -> SessionStore? {
        guard let text = UserDefaults.standard.string(forKey: LivePlanner.baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return nil }
        return SessionStore(client: AttestClient(base: base, transport: URLSessionPlanTransport(),
                                                 device: StoredInstallID()),
                            attester: DeviceAppAttester(), storage: KeychainSessionStorage(),
                            account: StoreKitAccountToken(), now: { Date() })
    }
}

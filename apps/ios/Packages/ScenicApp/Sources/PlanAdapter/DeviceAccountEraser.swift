import Foundation
import ScenicAPIClient

/// The device's side of a confirmed account deletion (T-0356 R3): what ScenicAPIClient `AccountDeletion` names is
/// erased here - the install id's UserDefaults copy, its Keychain item, then the session through the launch's ONE
/// store (Keychain and memory alike). Every other item names no account, and this switch does nothing for it.
struct DeviceAccountEraser: LocalAccountEraser {
    func erase(_ item: LocalAccountItem) async {
        switch item {
        case .installIDDefaults:
            UserDefaults.standard.removeObject(forKey: StoredInstallID.key)
        case .installIDKeychain:
            StoredInstallID.item.remove()
        case .session:
            if let store = LiveSession.store {
                await store.forgetSession()
            } else {
                KeychainSessionStorage().remove()
            }
        case .appAttestKey, .purchaseToken, .userStore, .disclaimerAcknowledged, .vehicle, .corpusWifiOnly,
             .corpusFiles, .basemapTiles, .workerBaseURL, .corpusManifestURL:
            break
        }
    }
}

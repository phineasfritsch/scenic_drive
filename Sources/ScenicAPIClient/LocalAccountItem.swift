import Foundation

/// Everything the app stores on the device (T-0356 MEASURE, the Log's thirteen items) and whether a confirmed
/// account deletion erases it (R3). Only what names the account is erased - the install id's fallback copy, the install id that
/// is the session's sub, and the session - in this order; the rest names no account and never left the phone
/// (saved drives, the Surprise history, preferences, downloads, configuration), or is not the app's to erase (the
/// App Attest key has no delete API; the StoreKit purchase id is the App Store's).
public enum LocalAccountItem: String, CaseIterable, Sendable {
    /// UserDefaults plan.install.id: the install id's fallback copy - erased FIRST, so a concurrent
    /// `StoredInstallID.installID()` cannot move the old id back into an emptied Keychain item.
    case installIDDefaults
    /// Keychain scenic.install/install-id: the install UUID, the session's sub - erased before the session, so a
    /// session acquired after the forget can never carry the old id.
    case installIDKeychain
    /// Keychain scenic.session/session: the session JWT, its key id and act.
    case session
    /// The App Attest key in the Secure Enclave.
    case appAttestKey
    /// StoreKit's appAccountToken on the App Store's transactions.
    case purchaseToken
    /// Application Support/user.sqlite: saved drives and the Surprise shown history.
    case userStore
    /// UserDefaults safety.disclaimer.acknowledged.v1.
    case disclaimerAcknowledged
    /// UserDefaults VehicleProfile.storageKey.
    case vehicle
    /// UserDefaults corpus.wifi.only.
    case corpusWifiOnly
    /// The downloaded places corpus.
    case corpusFiles
    /// Application Support/tiles/la.pmtiles.
    case basemapTiles
    /// UserDefaults plan.base.url.
    case workerBaseURL
    /// UserDefaults corpus.manifest.url.
    case corpusManifestURL

    /// True for what a confirmed deletion erases.
    public var erasedOnDeletion: Bool {
        switch self {
        case .installIDDefaults, .installIDKeychain, .session:
            return true
        case .appAttestKey, .purchaseToken, .userStore, .disclaimerAcknowledged, .vehicle, .corpusWifiOnly,
             .corpusFiles, .basemapTiles, .workerBaseURL, .corpusManifestURL:
            return false
        }
    }
}

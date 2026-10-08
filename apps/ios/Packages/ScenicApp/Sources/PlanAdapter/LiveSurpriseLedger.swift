import Foundation
import ScenicAPIClient
import ScenicKit
import Telemetry

/// The Surprise card's ledger as the app runs it (T-0307 R6, T-0310): ScenicAPIClient `LedgerSurpriseSource` over the
/// Worker session `SessionStore` (App Attest, the Keychain) and the H3 resolution-5 cell of each shown PLACE.
public enum LiveSurpriseLedger {
    /// Built once per launch: the session store's one acquisition per launch belongs to this one instance.
    private static let live: (any SurpriseLedgerSource)? = build()

    /// nil without an https base URL (LivePlanner's `plan.base.url`): no ledger, nothing sent.
    public static func make() -> (any SurpriseLedgerSource)? { live }

    static func build() -> (any SurpriseLedgerSource)? {
        guard let text = UserDefaults.standard.string(forKey: LivePlanner.baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return nil }
        guard let session = LiveSession.store else { return nil }
        return LedgerSurpriseSource(client: LedgerClient(base: base, transport: URLSessionPlanTransport(),
                                                         session: session),
                                    cellOf: { place in
                                        H3Cell.containing(latitudeDegrees: place.latitude,
                                                          longitudeDegrees: place.longitude)?.hexString
                                    })
    }
}

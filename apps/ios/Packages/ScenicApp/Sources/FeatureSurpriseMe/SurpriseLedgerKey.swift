import ScenicKit
import SwiftUI

/// The Surprise card's ledger source in the environment (T-0307 R6). The shell sets it from PlanAdapter, so this
/// feature never imports the API client; unset, the card's history is the device's own.
struct SurpriseLedgerKey: EnvironmentKey {
    static let defaultValue: (any SurpriseLedgerSource)? = nil
}

extension EnvironmentValues {
    public var surpriseLedger: (any SurpriseLedgerSource)? {
        get { self[SurpriseLedgerKey.self] }
        set { self[SurpriseLedgerKey.self] = newValue }
    }
}

import Foundation
import ScenicAPIClient
import ScenicKit

/// The Surprise card's ledger (T-0307 R6): GET /ledger through `LedgerClient`, its rows handed to the card as
/// `SurpriseLedgerPlace`s for `SurpriseHistoryMerge`. Any outcome but `.places` - no session, offline, a refusal -
/// is nil, and the card's history stays the device's own.
public struct LiveSurpriseLedger: SurpriseLedgerSource {
    let client: LedgerClient

    /// nil without an https base URL (LivePlanner's `plan.base.url`): no ledger, nothing sent.
    public static func make() -> (any SurpriseLedgerSource)? {
        guard let text = UserDefaults.standard.string(forKey: LivePlanner.baseURLKey), let base = URL(string: text),
              base.scheme == "https" else { return nil }
        return LiveSurpriseLedger(client: LedgerClient(base: base, transport: URLSessionPlanTransport(),
                                                       session: NoLedgerSession()))
    }

    public func ledgerPlaces() async -> [SurpriseLedgerPlace]? {
        guard case .places(let rows) = await client.read() else { return nil }
        return rows.map { SurpriseLedgerPlace(candidateId: $0.placeId, date: $0.day) }
    }
}

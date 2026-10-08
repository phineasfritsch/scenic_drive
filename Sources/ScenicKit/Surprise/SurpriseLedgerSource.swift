import Foundation

/// Where the Surprise card reads the server's 90 days from (T-0307 R6). A protocol in ScenicKit so the feature
/// target never imports the API client; the app's conformer lives in PlanAdapter.
public protocol SurpriseLedgerSource: Sendable {
    /// The ledger's places, or nil when there is no session or no usable answer - the history then stays the
    /// device's own (`SurpriseHistoryMerge.merged` with `ledger: nil`).
    func ledgerPlaces() async -> [SurpriseLedgerPlace]?
}

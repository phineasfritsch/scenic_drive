import Foundation

/// Where the Surprise card reads the server's 90 days from, and records each place it shows (T-0307 R6, T-0310 R7).
/// A protocol in ScenicKit so the feature target never imports the API client; the app's conformer is
/// ScenicAPIClient `LedgerSurpriseSource`, built by PlanAdapter.
public protocol SurpriseLedgerSource: Sendable {
    /// The ledger's places, or nil when there is no session or no usable answer - the history then stays the
    /// device's own (`SurpriseHistoryMerge.merged` with `ledger: nil`).
    func ledgerPlaces() async -> [SurpriseLedgerPlace]?
    /// `candidate` was shown: the ledger keeps its id and the H3-5 cell of ITS coordinate (P-PRIV-05). The argument
    /// is the place itself, so no device position can reach the ledger from here.
    func recordShown(_ candidate: SurpriseCandidate) async
}

import ScenicKit

/// The Surprise card's ledger with surprise_shown on each shown place (T-0355 R5). `inner` is the live ledger or nil
/// (no base URL, no session): nil answers exactly as an absent ledger does - no places, nothing recorded.
struct TelemetrySurpriseLedger: SurpriseLedgerSource {
    let inner: (any SurpriseLedgerSource)?

    func ledgerPlaces() async -> [SurpriseLedgerPlace]? {
        await inner?.ledgerPlaces()
    }

    func recordShown(_ candidate: SurpriseCandidate) async {
        LiveTelemetry.surpriseShown()
        await inner?.recordShown(candidate)
    }
}

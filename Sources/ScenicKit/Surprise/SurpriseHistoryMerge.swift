import Foundation

/// T-0307 R5: the Surprise no-repeat history the selector sees - the device's own history united with the server
/// ledger's 90 days. Pure and independent of the ledger's order, so the pick stays reproducible (P-PROD-02).
public enum SurpriseHistoryMerge {
    /// `ledger == nil` (no session, or no usable answer): `device`, untouched. Otherwise the device's shown places
    /// and every ledger place whose id is a candidate (category and corridor from that candidate; any other id can
    /// never be picked and is dropped), one entry per id - the LATEST day, the device's on a tie - ordered by day,
    /// then id. The feedback is the device's.
    public static func merged(device: SurpriseHistory, ledger: [SurpriseLedgerPlace]?,
                              candidates: [SurpriseCandidate]) -> SurpriseHistory {
        guard let ledger else { return device }
        let byID = Dictionary(candidates.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
        var latest: [String: SurpriseHistory.Shown] = [:]
        func keep(_ entry: SurpriseHistory.Shown) {
            if let held = latest[entry.candidateId], Surprise.days(entry.date, since: held.date) <= 0 { return }
            latest[entry.candidateId] = entry
        }
        device.shown.forEach(keep)
        for place in ledger {
            guard let c = byID[place.candidateId] else { continue }
            keep(SurpriseHistory.Shown(candidateId: c.id, category: c.category, corridor: c.corridor, date: place.date))
        }
        let shown = latest.values.sorted {
            let gap = Surprise.days($0.date, since: $1.date)
            return gap != 0 ? gap < 0 : $0.candidateId < $1.candidateId
        }
        return SurpriseHistory(shown: shown, feedback: device.feedback)
    }
}

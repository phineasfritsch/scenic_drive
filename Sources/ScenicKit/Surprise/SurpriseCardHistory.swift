import Foundation

/// The Surprise card's whole history state (T-0312 R5): `history` is what the device has shown and been told, and
/// `basis` is what the pick is made from. Recording a shown place moves only `history`, so the card never re-picks
/// from the history it records into; "not this" and "start over" move both; a restore from the user store adds the
/// stored entries to both and never the places recorded in memory.
public struct SurpriseCardHistory: Sendable, Equatable {
    public let history: SurpriseHistory
    public let basis: SurpriseHistory

    public init(history: SurpriseHistory = SurpriseHistory(), basis: SurpriseHistory = SurpriseHistory()) {
        self.history = history
        self.basis = basis
    }

    /// The place on the card recorded as shown on `date`; nil when it is already shown that day (T-0310 R7).
    public func showing(_ candidate: SurpriseCandidate, on date: CivilDate) -> SurpriseCardHistory? {
        guard let next = SurpriseShowing.recording(candidate, on: date, in: history) else { return nil }
        return SurpriseCardHistory(history: next, basis: basis)
    }

    /// A "not this" answer: the feedback is appended and the pick moves to the new history.
    public func declining(_ feedback: SurpriseFeedback) -> SurpriseCardHistory {
        let next = SurpriseHistory(shown: history.shown, feedback: history.feedback + [feedback])
        return SurpriseCardHistory(history: next, basis: next)
    }

    /// "Start over": the feedback is cleared and the shown places stay (T-0310 R7, T-0312 R4).
    public func startingOver() -> SurpriseCardHistory {
        let next = SurpriseHistory(shown: history.shown)
        return SurpriseCardHistory(history: next, basis: next)
    }

    /// The user store's entries united into both halves, de-duplicated by (place, day), stored entries first.
    public func restoring(_ stored: [SurpriseHistory.Shown]) -> SurpriseCardHistory {
        SurpriseCardHistory(history: SurpriseHistory(shown: Self.union(stored, history.shown), feedback: history.feedback),
                            basis: SurpriseHistory(shown: Self.union(stored, basis.shown), feedback: basis.feedback))
    }

    /// `first`'s entries, then `then`'s, each (place, day) once - the first occurrence kept.
    static func union(_ first: [SurpriseHistory.Shown], _ then: [SurpriseHistory.Shown]) -> [SurpriseHistory.Shown] {
        var out: [SurpriseHistory.Shown] = []
        for entry in first + then
        where !out.contains(where: { $0.candidateId == entry.candidateId && $0.date == entry.date }) {
            out.append(entry)
        }
        return out
    }
}

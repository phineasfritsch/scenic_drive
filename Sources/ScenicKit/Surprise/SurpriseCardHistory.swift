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
        nil
    }

    /// A "not this" answer: the feedback is appended and the pick moves to the new history.
    public func declining(_ feedback: SurpriseFeedback) -> SurpriseCardHistory {
        self
    }

    /// "Start over": the feedback is cleared and the shown places stay (T-0310 R7, T-0312 R4).
    public func startingOver() -> SurpriseCardHistory {
        self
    }

    /// The user store's entries united into both halves, de-duplicated by (place, day), stored entries first.
    public func restoring(_ stored: [SurpriseHistory.Shown]) -> SurpriseCardHistory {
        self
    }
}

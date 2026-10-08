import Foundation

/// Recording a shown Surprise place (T-0310 R7): the device history - the 90-day no-repeat's input - gains the place
/// with its own category and corridor on the day it was shown. nil when that place is already shown that day, so a
/// re-render records nothing and the card posts nothing.
public enum SurpriseShowing {
    public static func recording(_ candidate: SurpriseCandidate, on date: CivilDate,
                                 in history: SurpriseHistory) -> SurpriseHistory? {
        guard !history.shown.contains(where: { $0.candidateId == candidate.id && $0.date == date }) else { return nil }
        let entry = SurpriseHistory.Shown(candidateId: candidate.id, category: candidate.category,
                                          corridor: candidate.corridor, date: date)
        return SurpriseHistory(shown: history.shown + [entry], feedback: history.feedback)
    }
}

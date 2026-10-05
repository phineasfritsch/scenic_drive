import Foundation

/// What this driver has already been shown and told us (T-0253 R1): the shown places and the "not this" answers.
public struct SurpriseHistory: Sendable, Equatable {
    public struct Shown: Sendable, Equatable {
        public let candidateId: String
        public let category: SurpriseCategory
        public let corridor: String
        public let date: CivilDate

        public init(candidateId: String, category: SurpriseCategory, corridor: String, date: CivilDate) {
            self.candidateId = candidateId
            self.category = category
            self.corridor = corridor
            self.date = date
        }
    }

    public let shown: [Shown]
    public let feedback: [SurpriseFeedback]

    public init(shown: [Shown] = [], feedback: [SurpriseFeedback] = []) {
        self.shown = shown
        self.feedback = feedback
    }
}

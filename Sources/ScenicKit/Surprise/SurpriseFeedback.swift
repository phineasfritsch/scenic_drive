import Foundation

/// One "not this" answer (T-0253 R6): which pick it was, what it was, and why the driver turned it down.
public struct SurpriseFeedback: Sendable, Equatable {
    public enum Reason: String, Sendable, Equatable, CaseIterable {
        case tooFar
        case notMyThing
        case beenThere
        case wrongTime
    }

    public let candidateId: String
    public let category: SurpriseCategory
    public let roundTripMinutes: Int
    public let date: CivilDate
    public let reason: Reason

    public init(candidateId: String, category: SurpriseCategory, roundTripMinutes: Int, date: CivilDate,
                reason: Reason) {
        self.candidateId = candidateId
        self.category = category
        self.roundTripMinutes = roundTripMinutes
        self.date = date
        self.reason = reason
    }
}

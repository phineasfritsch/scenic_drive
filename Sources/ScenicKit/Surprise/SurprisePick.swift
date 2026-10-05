import Foundation

/// The one place Surprise offers, and why (T-0253 R1).
public struct SurprisePick: Sendable, Equatable {
    public let candidateId: String
    public let name: String
    public let reason: SurpriseReason

    public init(candidateId: String, name: String, reason: SurpriseReason) {
        self.candidateId = candidateId
        self.name = name
        self.reason = reason
    }
}

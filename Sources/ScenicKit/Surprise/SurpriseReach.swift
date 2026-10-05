import Foundation

/// The reachable area as the caller measured it (T-0253 R1): the dial's round-trip budget and, per candidate
/// id, the round-trip minutes. A candidate absent from the map lies outside the reach polygon.
public struct SurpriseReach: Sendable, Equatable {
    public let budgetMinutes: Int
    public let roundTripMinutes: [String: Int]

    public init(budgetMinutes: Int, roundTripMinutes: [String: Int]) {
        self.budgetMinutes = budgetMinutes
        self.roundTripMinutes = roundTripMinutes
    }
}

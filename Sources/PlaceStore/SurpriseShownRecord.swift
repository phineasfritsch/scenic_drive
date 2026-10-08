import Foundation

/// One row of the user store's surprise_shown table (T-0312 R1): a place, its category and corridor, and the day it
/// was shown (whole days since 1970-01-01 of the card's civil date). No coordinate, cell or time of day (P-PRIV-05).
public struct SurpriseShownRecord: Sendable, Equatable {
    public let placeID: String
    public let category: String
    public let corridor: String
    public let day: Int
    public let latitude: Double

    public init(placeID: String, category: String, corridor: String, day: Int) {
        self.placeID = placeID
        self.category = category
        self.corridor = corridor
        self.day = day
        self.latitude = 0
    }
}

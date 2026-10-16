import Foundation

/// The plan sheet's typed-address search (T-0362 R6, R9): one call is one submitted query, answered as places the sheet
/// can plan to or one line of copy. `near` is the bias - at most ONE coordinate, rounded to 2 dp before it leaves the
/// device (CLAUDE.md: never more than one coordinate per action, never more than 2 dp).
public protocol PlaceSearching: Sendable {
    func searchPlaces(_ query: String, near: Coordinate?) async -> PlaceSearchAnswer
}

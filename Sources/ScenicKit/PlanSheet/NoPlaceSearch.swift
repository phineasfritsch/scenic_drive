import Foundation

/// The search a build without an https base hands the sheet (T-0362 R9): it sends nothing and says so.
public struct NoPlaceSearch: PlaceSearching {
    public init() {}

    public func searchPlaces(_ query: String, near: Coordinate?) async -> PlaceSearchAnswer {
        .notice(PlaceSearchAnswer.unavailableNotice)
    }
}

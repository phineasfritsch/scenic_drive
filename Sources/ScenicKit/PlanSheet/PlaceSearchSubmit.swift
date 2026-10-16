import Foundation

/// The plan sheet's ONE path to the address search (T-0362 R6, R7): a submit asks the searcher exactly once; a blank
/// submit asks nothing. Typing never reaches this type - the sheet calls `submit` from its field's submit action only,
/// while the bundled corpus list (on the device, no request) still follows every keystroke.
public struct PlaceSearchSubmit: Sendable {
    let searcher: any PlaceSearching

    public init(searcher: any PlaceSearching) {
        self.searcher = searcher
    }

    /// The answer to `query`, biased by `bias(start:destination:)`, or nil (and no call) when the query is blank.
    public func submit(_ query: String, start: PlanPlace?, destination: PlanPlace?) async -> PlaceSearchAnswer? {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return nil }
        return await searcher.searchPlaces(query, near: Self.bias(start: start, destination: destination))
    }

    /// R7: the sheet cannot see the map, so the bias is the place the user already chose - the start, else the
    /// destination, else none. SearchRequestBody rounds it to 2 dp on the device.
    public static func bias(start: PlanPlace?, destination: PlanPlace?) -> Coordinate? {
        start?.coordinate ?? destination?.coordinate
    }
}

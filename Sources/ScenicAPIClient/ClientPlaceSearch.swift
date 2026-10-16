import Foundation
import ScenicKit

/// The live `PlaceSearching` (T-0362 R9): one `SearchClient.search` per submitted query, its outcome in the sheet's
/// words (PlaceSearchCopy).
public struct ClientPlaceSearch: PlaceSearching {
    let client: SearchClient

    public init(client: SearchClient) {
        self.client = client
    }

    public func searchPlaces(_ query: String, near: Coordinate?) async -> PlaceSearchAnswer {
        PlaceSearchCopy.answer(await client.search(query, near: near))
    }
}

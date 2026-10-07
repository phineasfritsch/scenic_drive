import Foundation
import PlaceStore
import ScenicKit

/// The plan sheet's search over the bundled corpus: PlaceStore's FTS5 (T-0254), named places only. Photon is not
/// deployed and typed street addresses are a later task (Brief).
enum PlanPlaceSearch {
    static let corpusName = "corpus-fallback"
    static let limit = 20

    /// Read on first use and kept, as the Surprise card's deck is.
    static let store: PlaceStore? = {
        let bundle = Bundle.main
        guard let url = LaunchCorpus.url(fallback: bundle.url(forResource: corpusName, withExtension: "sqlite")
                ?? bundle.url(forResource: corpusName, withExtension: "sqlite", subdirectory: "Corpus")) else { return nil }
        return try? PlaceStore(path: url.path)
    }()

    /// Places matching `query`, best first; nothing for an empty query or a corpus that would not load.
    static func find(_ query: String) -> [PlanPlace] {
        guard let store, let places = try? store.search(query: query, limit: limit) else { return [] }
        return places.compactMap { place in
            guard let name = place.name else { return nil }
            return PlanPlace(id: place.placeID, name: name,
                             coordinate: Coordinate(latitude: Double(place.latE7) / 10_000_000,
                                                    longitude: Double(place.lonE7) / 10_000_000))
        }
    }
}

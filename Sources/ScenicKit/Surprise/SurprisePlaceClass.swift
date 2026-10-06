import Foundation

/// The ten place classes the corpus carries (services/etl placeallow.CLASSES, measured on the committed fallback)
/// and what the Surprise card says about each (T-0273 R3). Places carry only a name and a class today, so the hook
/// line is the class's; curated prose replaces it when T-0183 lands.
public enum SurprisePlaceClass: String, Sendable, Equatable, CaseIterable {
    case viewpoint
    case peak
    case waterfall
    case beach
    case trailhead
    case museum
    case cafe
    case garden
    case park
    case town

    /// The selector's category: a peak is looked at from a viewpoint, a waterfall is reached from a trailhead.
    public var category: SurpriseCategory {
        switch self {
        case .viewpoint, .peak: return .viewpoint
        case .waterfall, .trailhead: return .trailhead
        case .beach: return .beach
        case .museum: return .museum
        case .cafe: return .cafe
        case .garden: return .garden
        case .park: return .park
        case .town: return .town
        }
    }

    /// The class as the card names it.
    public var label: String {
        switch self {
        case .viewpoint: return "Viewpoint"
        case .peak: return "Peak"
        case .waterfall: return "Waterfall"
        case .beach: return "Beach"
        case .trailhead: return "Trailhead"
        case .museum: return "Museum"
        case .cafe: return "Cafe"
        case .garden: return "Garden"
        case .park: return "Park"
        case .town: return "Town"
        }
    }

    /// One short, specific line: why go.
    public var hook: String {
        switch self {
        case .viewpoint: return "Pull over for a long view."
        case .peak: return "A high point with the basin below."
        case .waterfall: return "A waterfall, if the season's been wet."
        case .beach: return "Sand underfoot and a long horizon."
        case .trailhead: return "Park the car and walk a while."
        case .museum: return "Something to look at, out of the sun."
        case .cafe: return "A slow cup somewhere new."
        case .garden: return "Planted paths and some shade."
        case .park: return "Green space to stretch your legs."
        case .town: return "A small main street to wander."
        }
    }

    /// Minutes spent there, the window the opening-hours and golden-hour rules read.
    public var dwellMinutes: Int {
        switch self {
        case .viewpoint: return 20
        case .cafe: return 30
        case .peak, .park: return 45
        case .waterfall, .beach, .trailhead, .garden, .town: return 60
        case .museum: return 90
        }
    }

    /// Assumed opening window in minutes after local midnight, or nil for an open-air place (hours-exempt).
    /// Conservative until opening_hours reaches the corpus.
    public var assumedHours: (opens: Int, closes: Int)? {
        switch self {
        case .museum: return (600, 1020)
        case .cafe: return (420, 1080)
        case .garden: return (540, 1020)
        case .viewpoint, .peak, .waterfall, .beach, .trailhead, .park, .town: return nil
        }
    }
}

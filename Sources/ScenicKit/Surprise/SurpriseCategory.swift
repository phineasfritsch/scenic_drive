import Foundation

/// What kind of place a Surprise candidate is (T-0253 R1). The fire-weather and hours rules read it.
public enum SurpriseCategory: String, Sendable, Equatable, CaseIterable {
    case park
    case trailhead
    case viewpoint
    case beach
    case garden
    case cafe
    case museum
    case town

    /// R3 (7): a red-flag / fire-weather day closes these.
    public var closesOnRedFlag: Bool {
        switch self {
        case .park, .trailhead, .viewpoint: return true
        case .beach, .garden, .cafe, .museum, .town: return false
        }
    }
}

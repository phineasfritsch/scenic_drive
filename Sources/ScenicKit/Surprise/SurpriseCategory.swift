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
}

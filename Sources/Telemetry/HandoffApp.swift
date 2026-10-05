import Foundation

/// The navigation app a drive was handed to - the `app` of `handoff_tapped`. A closed list; the raw value is
/// the wire label.
public enum HandoffApp: String, CaseIterable, Sendable {
    case appleMaps = "apple_maps"
    case googleMaps = "google_maps"
    case waze
}

import Foundation

/// A WGS-84 position.
///
/// Foundation-only on purpose: ScenicKit must build and test on Linux, so this type exists
/// instead of `CLLocationCoordinate2D`. Bridge at the `MapAdapter` / `NavAdapter` boundary.
public struct Coordinate: Hashable, Sendable, Codable {
    public let latitude: Double
    public let longitude: Double

    public init(latitude: Double, longitude: Double) {
        self.latitude = latitude
        self.longitude = longitude
    }
}

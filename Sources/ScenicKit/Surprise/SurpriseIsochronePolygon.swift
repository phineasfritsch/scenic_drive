import Foundation

/// A reach bucket's GeoJSON Polygon as /isochrone sends it (T-0262 R7): rings of [lon, lat], the outer ring first,
/// then the holes. `SurpriseIsochrone.decode` refuses any other `type` and any position short of two numbers.
public struct SurpriseIsochronePolygon: Sendable, Equatable, Decodable {
    public let type: String
    public let coordinates: [[[Double]]]

    public init(type: String, coordinates: [[[Double]]]) {
        self.type = type
        self.coordinates = coordinates
    }
}

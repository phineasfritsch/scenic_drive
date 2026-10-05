import Foundation

/// One /isochrone bucket (T-0262 R7): everything within `minutes` one way, and the round trip the reach charges a
/// place inside it - the bucket's upper bound there and back, as the Worker sends it.
public struct SurpriseIsochroneBucket: Sendable, Equatable, Decodable {
    public let minutes: Int
    public let roundTripMinutes: Int
    public let polygon: SurpriseIsochronePolygon

    public init(minutes: Int, roundTripMinutes: Int, polygon: SurpriseIsochronePolygon) {
        self.minutes = minutes
        self.roundTripMinutes = roundTripMinutes
        self.polygon = polygon
    }
}

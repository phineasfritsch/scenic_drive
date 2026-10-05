import Foundation

/// A candidate along a road trip: a corridor stop (ranked by `score`) or a lodging (an overnight town).
public struct RoadTripPlace: Sendable, Equatable {
    public enum Kind: String, Sendable, Equatable {
        case stop
        case lodging
    }

    public let name: String
    public let kind: Kind
    public let score: Int
    public let coordinate: Coordinate

    public init(name: String, kind: Kind, score: Int, coordinate: Coordinate) {
        self.name = name
        self.kind = kind
        self.score = score
        self.coordinate = coordinate
    }
}

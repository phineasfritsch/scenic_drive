import Foundation

/// One edge of a recorded A -> B route, as the road-trip splitter reads it (T-0249 R1, R2). Edges are atomic:
/// a day boundary always falls on a vertex. Seconds and metres are whole numbers so a day plan is compared by
/// exact equality.
public struct RoadTripEdge: Sendable, Equatable {
    public let start: Coordinate
    public let end: Coordinate
    public let seconds: Int
    public let meters: Int

    public init(start: Coordinate, end: Coordinate, seconds: Int, meters: Int) {
        self.start = start
        self.end = end
        self.seconds = seconds
        self.meters = meters
    }
}

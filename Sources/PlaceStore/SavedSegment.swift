/// One segment of a saved drive: the corpus segment id it was planned over and where that segment's middle was.
/// The midpoint is the drive's record of where it went; re-resolving replaces the id, never the midpoint (T-0290 R5).
public struct SavedSegment: Equatable, Sendable {
    public let segmentID: Int64
    public let midpoint: SavedMidpoint

    public init(segmentID: Int64, midpoint: SavedMidpoint) {
        self.segmentID = segmentID
        self.midpoint = midpoint
    }
}

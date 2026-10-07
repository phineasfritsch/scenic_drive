/// One segment of a saved drive: the corpus segment id it was planned over and where that segment's middle was.
/// The midpoint is the drive's record of where it went; re-resolving replaces the id, never the midpoint (T-0290 R5).
public struct SavedSegment: Equatable, Sendable {
    /// The id a segment carries from a save until `SavedDriveResolver` places it (T-0306 R2). Corpus segment ids are
    /// SQLite INTEGER PRIMARY KEYs the ETL assigns from 1, so no corpus holds it and the resolver always looks.
    public static let unplaced: Int64 = -1

    public let segmentID: Int64
    public let midpoint: SavedMidpoint

    public init(segmentID: Int64, midpoint: SavedMidpoint) {
        self.segmentID = segmentID
        self.midpoint = midpoint
    }
}

import PlaceStore

/// An in-memory corpus for the re-resolve table: `segmentIDs(in:)` answers like PlaceStore's R*Tree query - every
/// segment whose e7 box INTERSECTS the degree box, ids ascending.
struct FakeSavedDriveCorpus: SavedDriveCorpus {
    let segments: [Segment]

    func segment(id: Int64) throws -> Segment? {
        segments.first { $0.segmentID == id }
    }

    func segmentIDs(in box: BoundingBox) throws -> [Int64] {
        segments.filter { segment in
            Double(segment.maxLonE7) / 1e7 >= box.minLon && Double(segment.minLonE7) / 1e7 <= box.maxLon
                && Double(segment.maxLatE7) / 1e7 >= box.minLat && Double(segment.minLatE7) / 1e7 <= box.maxLat
        }.map(\.segmentID).sorted()
    }

    /// A one-point segment whose box and midpoint are (`latE7`, `lonE7`).
    static func segment(_ id: Int64, latE7: Int, lonE7: Int) -> Segment {
        Segment(segmentID: id, wayID: id, bucket: 0, offsetMM: 0, lengthMM: 1_000, minLonE7: lonE7,
                minLatE7: latE7, maxLonE7: lonE7, maxLatE7: latE7, midLonE7: lonE7, midLatE7: latE7, geometry: [])
    }
}

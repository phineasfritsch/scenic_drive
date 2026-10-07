/// What re-resolving a saved drive reads from a corpus: one segment by id, and the ids whose box intersects a
/// query box (T-0290 R5). `PlaceStore` conforms with the methods it already has; tests pass an in-memory corpus.
public protocol SavedDriveCorpus {
    func segment(id: Int64) throws -> Segment?
    func segmentIDs(in box: BoundingBox) throws -> [Int64]
}

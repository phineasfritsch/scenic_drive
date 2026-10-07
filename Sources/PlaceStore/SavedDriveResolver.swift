import Foundation

/// The re-resolve rule a saved drive meets when a new corpus activates (plan, Saved drives; T-0290 R5).
///
/// A saved segment id the corpus still has is kept. An absent one is replaced by the nearest corpus segment whose
/// stored midpoint is within 25 m of the saved midpoint (haversine; ties to the lowest id). If any absent id has
/// no such segment the drive keeps ALL its old ids and is marked `needsReplan`; otherwise `needsReplan` is false.
/// Midpoints are never rewritten. `SavedDriveStore.reresolve(against:)` is the shipped entry point; this type
/// uses nothing from GRDB, so its table and mutation population run on every toolchain.
public enum SavedDriveResolver {
    /// The plan's "nearest within 25 m".
    public static let radiusMeters: Double = 25
    /// Mean Earth radius (IUGG), the one services/etl uses for metres.
    static let earthRadiusMeters: Double = 6_371_008.8
    /// Below this cos(latitude) the longitude window is the whole range rather than a near-infinite widening.
    static let minimumCosine: Double = 0.01
    /// The corpus stores midpoints in e7 degrees.
    static let corpusScale: Double = 10_000_000

    public static func resolve(_ drive: SavedDrive, against corpus: SavedDriveCorpus) throws -> SavedDrive {
        var ids: [Int64] = []
        ids.reserveCapacity(drive.segments.count)
        for saved in drive.segments {
            if try corpus.segment(id: saved.segmentID) != nil {
                ids.append(saved.segmentID)
                continue
            }
            guard let replacement = try nearest(to: saved.midpoint, in: corpus) else {
                var unresolved = drive
                unresolved.needsReplan = true
                return unresolved
            }
            ids.append(replacement)
        }
        var resolved = drive
        resolved.segments = zip(drive.segments, ids).map { saved, id in
            SavedSegment(segmentID: id, midpoint: saved.midpoint)
        }
        resolved.needsReplan = false
        return resolved
    }

    /// The id of the nearest corpus segment within `radiusMeters` of `midpoint`, lowest id on a tie, or nil.
    static func nearest(to midpoint: SavedMidpoint, in corpus: SavedDriveCorpus) throws -> Int64? {
        let lat = midpoint.latitude
        let lon = midpoint.longitude
        let halfLat = 2 * radiusMeters / earthRadiusMeters * 180 / Double.pi
        let cosine = cos(lat * Double.pi / 180)
        let halfLon = cosine < minimumCosine ? 360 : halfLat / cosine
        let box = BoundingBox(minLon: lon - halfLon, minLat: lat - halfLat, maxLon: lon + halfLon,
                              maxLat: lat + halfLat)
        var best: (id: Int64, meters: Double)?
        for id in try corpus.segmentIDs(in: box) {
            guard let segment = try corpus.segment(id: id) else { continue }
            let meters = distance(lat, lon, Double(segment.midLatE7) / corpusScale,
                                  Double(segment.midLonE7) / corpusScale)
            guard meters <= radiusMeters else { continue }
            if let current = best, meters > current.meters || (meters == current.meters && id > current.id) {
                continue
            }
            best = (id, meters)
        }
        return best?.id
    }

    /// Great-circle metres between two points in degrees (haversine).
    static func distance(_ lat1: Double, _ lon1: Double, _ lat2: Double, _ lon2: Double) -> Double {
        let radians = Double.pi / 180
        let dLat = (lat2 - lat1) * radians
        let dLon = (lon2 - lon1) * radians
        let a = sin(dLat / 2) * sin(dLat / 2)
            + cos(lat1 * radians) * cos(lat2 * radians) * sin(dLon / 2) * sin(dLon / 2)
        return 2 * earthRadiusMeters * asin(min(1, a.squareRoot()))
    }
}

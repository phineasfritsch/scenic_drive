import Foundation
import PlaceStore

/// The re-resolve table (T-0290 R5), shared by SavedDriveResolverTests (native, `SavedDriveResolver.resolve`) and
/// SavedDriveStoreTests (GRDB, the shipped `SavedDriveStore.reresolve(against:)`).
///
/// Moves are e7 latitude steps of 1e-7 degree = 0.0111195 m on the meridian (R = 6371008.8 m): 2239 is 24.897 m,
/// 2248 is 24.997 m, 2249 is 25.008 m, 2257 is 25.097 m, 9000 is 100.08 m. Eastward moves are 24 m converted at the
/// drive's own latitude, so drive B (64 N) sits outside a box that forgot to widen longitude by 1/cos(lat).
enum SavedDriveResolveTable {
    static func midpoint(_ lat: Double, _ lon: Double) throws -> SavedMidpoint {
        try SavedMidpoint(latitude: lat, longitude: lon)
    }

    /// Two variants that differ in every field, so a row whose expected value ignores the input is caught.
    static func drives() throws -> [SavedDrive] {
        [try SavedDrive(name: "Saddle Peak", segments: [
            SavedSegment(segmentID: 101, midpoint: try midpoint(34.09012, -118.65432)),
            SavedSegment(segmentID: 102, midpoint: try midpoint(34.09234, -118.65001)),
        ], lambda: 2.5, budgetMinutes: 40, createdAt: 1_790_000_000, needsReplan: false),
         try SavedDrive(name: "Hringvegur", segments: [
            SavedSegment(segmentID: 201, midpoint: try midpoint(64.12345, -21.54321)),
            SavedSegment(segmentID: 202, midpoint: try midpoint(64.12456, -21.54001)),
            SavedSegment(segmentID: 203, midpoint: try midpoint(64.12567, -21.53789)),
         ], lambda: 0.75, budgetMinutes: 90, createdAt: 1_790_000_500, needsReplan: true)]
    }

    /// The saved segment at `index` as a corpus segment, moved by e7 steps.
    static func at(_ saved: SavedSegment, id: Int64, north: Int = 0, east: Int = 0) -> Segment {
        FakeSavedDriveCorpus.segment(id, latE7: saved.midpoint.latE5 * 100 + north,
                                     lonE7: saved.midpoint.lonE5 * 100 + east)
    }

    /// e7 longitude steps that are `meters` east at the segment's latitude.
    static func eastSteps(_ meters: Double, _ saved: SavedSegment) -> Int {
        let metersPerStep = 6_371_008.8 * Double.pi / 180 / 1e7 * cos(saved.midpoint.latitude * Double.pi / 180)
        return Int((meters / metersPerStep).rounded())
    }

    /// Every saved segment where it was, except those at `skipping`.
    static func present(_ drive: SavedDrive, skipping: Set<Int> = []) -> [Segment] {
        drive.segments.enumerated().filter { !skipping.contains($0.offset) }.map { at($0.element, id: $0.element.segmentID) }
    }

    /// `drive` rebuilt through the public initialiser with `ids` (nil keeps them) and `needsReplan`.
    static func with(_ drive: SavedDrive, ids: [Int64]? = nil, needsReplan: Bool) throws -> SavedDrive {
        let segments = zip(drive.segments, ids ?? drive.segments.map(\.segmentID)).map {
            SavedSegment(segmentID: $1, midpoint: $0.midpoint)
        }
        return try SavedDrive(id: drive.id, name: drive.name, segments: segments, lambda: drive.lambda,
                              budgetMinutes: drive.budgetMinutes, createdAt: drive.createdAt, needsReplan: needsReplan)
    }

    static func replacing(_ drive: SavedDrive, _ index: Int, by id: Int64) throws -> SavedDrive {
        var ids = drive.segments.map(\.segmentID)
        ids[index] = id
        return try with(drive, ids: ids, needsReplan: false)
    }

    static func same(_ drive: SavedDrive) -> SavedDrive { drive }

    static var rows: [SavedDriveResolveRow] { [
        SavedDriveResolveRow(name: "all present: ids kept, needsReplan cleared", input: same,
            corpus: { present($0) }, expected: { try with($0, needsReplan: false) }),
        SavedDriveResolveRow(name: "first moved 24.9 m north: replaced; a 24.997 m decoy loses", input: same,
            corpus: { present($0, skipping: [0]) + [at($0.segments[0], id: 950, north: 2248),
                                                     at($0.segments[0], id: 900, north: 2239)] },
            expected: { try replacing($0, 0, by: 900) }),
        SavedDriveResolveRow(name: "first moved 25.1 m north: needsReplan, old ids kept", input: same,
            corpus: { present($0, skipping: [0]) + [at($0.segments[0], id: 900, north: 2257)] },
            expected: { try with($0, needsReplan: true) }),
        SavedDriveResolveRow(name: "first gone: needsReplan, old ids kept", input: same,
            corpus: { present($0, skipping: [0]) }, expected: { try with($0, needsReplan: true) }),
        SavedDriveResolveRow(name: "empty drive: unchanged, needsReplan false",
            input: { try with($0, ids: [], needsReplan: $0.needsReplan) }, corpus: { _ in [] },
            expected: { try with($0, ids: [], needsReplan: false) }),
        SavedDriveResolveRow(name: "last moved 24.997 m south: replaced", input: same,
            corpus: { d in present(d, skipping: [d.segments.count - 1]) + [at(d.segments.last!, id: 900, north: -2248)] },
            expected: { d in try replacing(d, d.segments.count - 1, by: 900) }),
        SavedDriveResolveRow(name: "last moved 25.008 m south: needsReplan", input: same,
            corpus: { d in present(d, skipping: [d.segments.count - 1]) + [at(d.segments.last!, id: 900, north: -2249)] },
            expected: { try with($0, needsReplan: true) }),
        SavedDriveResolveRow(name: "second moved 24 m east at its own latitude: replaced", input: same,
            corpus: { d in present(d, skipping: [1]) + [at(d.segments[1], id: 900, east: eastSteps(24, d.segments[1]))] },
            expected: { try replacing($0, 1, by: 900) }),
        SavedDriveResolveRow(name: "second moved 24 m west: replaced", input: same,
            corpus: { d in present(d, skipping: [1]) + [at(d.segments[1], id: 900, east: -eastSteps(24, d.segments[1]))] },
            expected: { try replacing($0, 1, by: 900) }),
        SavedDriveResolveRow(name: "tie at one point: the lowest id wins", input: same,
            corpus: { present($0, skipping: [0]) + [at($0.segments[0], id: 905, north: 1000),
                                                     at($0.segments[0], id: 903, north: 1000)] },
            expected: { try replacing($0, 0, by: 903) }),
        SavedDriveResolveRow(name: "first resolves, second gone: needsReplan, ALL old ids kept", input: same,
            corpus: { present($0, skipping: [0, 1]) + [at($0.segments[0], id: 900, north: 2239)] },
            expected: { try with($0, needsReplan: true) }),
        SavedDriveResolveRow(name: "present id whose midpoint moved 100 m: kept, never searched", input: same,
            corpus: { present($0, skipping: [0]) + [at($0.segments[0], id: $0.segments[0].segmentID, north: 9000),
                                                     at($0.segments[0], id: 900, north: 0)] },
            expected: { try with($0, needsReplan: false) }),
    ] }
}

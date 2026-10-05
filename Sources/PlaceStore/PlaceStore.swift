#if canImport(GRDB)
import Foundation
import GRDB

/// RED-FIRST STUB (T-0175): opens the file and reads nothing. Replaced by the reader in the next commit.
public final class PlaceStore: Sendable {
    public static let schemaVersion: Int = 2

    private let queue: DatabaseQueue

    public init(path: String) throws {
        var configuration = Configuration()
        configuration.readonly = true
        queue = try DatabaseQueue(path: path, configuration: configuration)
    }

    public func meta() throws -> CorpusMeta {
        CorpusMeta(schemaVersion: 0, minAppBuild: 0, region: "", corpusVersion: "", builtAt: "", attribution: "")
    }

    public func segment(id: Int64) throws -> Segment? {
        nil
    }

    public func segmentIDs(in box: BoundingBox) throws -> [Int64] {
        []
    }
}
#endif

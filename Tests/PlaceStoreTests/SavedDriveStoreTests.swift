#if canImport(GRDB)
import Foundation
import GRDB
import PlaceStore
import Testing

/// `SavedDriveStore`, the shipped user store (T-0290 R1, R6): every write checked by FULL equality of the whole
/// `[SavedDrive]` that `list()` returns, and the re-resolve table through the shipped `reresolve(against:)`.
@Suite("SavedDriveStore")
struct SavedDriveStoreTests {
    static func freshPath() throws -> String {
        try CorpusFixture.scratch().appendingPathComponent("user.sqlite").path
    }

    static func drive(_ name: String, createdAt: Int64, lambda: Double = 1.5, id: Int64? = nil,
                      needsReplan: Bool = false) throws -> SavedDrive {
        try SavedDrive(id: id, name: name, segments: [
            SavedSegment(segmentID: 11, midpoint: try SavedMidpoint(latitude: 34.1, longitude: -118.7)),
            SavedSegment(segmentID: 12, midpoint: try SavedMidpoint(latitude: -34.00001, longitude: 179.99999)),
            SavedSegment(segmentID: 11, midpoint: try SavedMidpoint(latitude: 90, longitude: -180)),
        ], lambda: lambda, budgetMinutes: 45, createdAt: createdAt, needsReplan: needsReplan)
    }

    @Test("save returns the drive with its id; list is newest first; rename and delete change exactly one drive")
    func saveListRenameDelete() throws {
        let path = try Self.freshPath()
        let store = try SavedDriveStore(path: path)
        #expect(try store.list() == [])
        let older = try Self.drive("Mulholland", createdAt: 1_790_000_000, lambda: 1000, needsReplan: true)
        let newer = try SavedDrive(name: "Empty", segments: [], lambda: 0, budgetMinutes: 0, createdAt: 1_790_000_100)
        let savedOlder = try store.save(older)
        let savedNewer = try store.save(newer)
        #expect(savedOlder == (try Self.drive("Mulholland", createdAt: 1_790_000_000, lambda: 1000, id: 1,
                                              needsReplan: true)))
        #expect(savedNewer == (try SavedDrive(id: 2, name: "Empty", segments: [], lambda: 0, budgetMinutes: 0,
                                              createdAt: 1_790_000_100)))
        #expect(try store.list() == [savedNewer, savedOlder])
        #expect(try SavedDriveStore(path: path).list() == [savedNewer, savedOlder])

        try store.rename(id: 1, to: "Saddle Peak")
        let renamed = try Self.drive("Saddle Peak", createdAt: 1_790_000_000, lambda: 1000, id: 1, needsReplan: true)
        #expect(try store.list() == [savedNewer, renamed])

        try store.delete(id: 2)
        #expect(try store.list() == [renamed])
        try store.delete(id: 1)
        #expect(try store.list() == [])
        let orphans = try DatabaseQueue(path: path).read { db in
            try Int.fetchOne(db, sql: "SELECT count(*) FROM saved_drive_segment")
        }
        #expect(orphans == 0)
    }

    @Test("same created_at lists the higher id first")
    func tiesListByIDDescending() throws {
        let store = try SavedDriveStore(path: try Self.freshPath())
        let first = try store.save(try Self.drive("a", createdAt: 5))
        let second = try store.save(try Self.drive("b", createdAt: 5))
        let earlier = try store.save(try Self.drive("c", createdAt: 4))
        #expect(try store.list() == [second, first, earlier])
    }

    @Test("rename and delete of an unknown id are driveNotFound and change nothing")
    func unknownID() throws {
        let store = try SavedDriveStore(path: try Self.freshPath())
        let saved = try store.save(try Self.drive("a", createdAt: 5))
        #expect(throws: UserStoreError.driveNotFound(id: 99)) { try store.rename(id: 99, to: "x") }
        #expect(throws: UserStoreError.driveNotFound(id: 99)) { try store.delete(id: 99) }
        #expect(try store.list() == [saved])
    }

    @Test("a corpus.sqlite (application_id SCNC) is refused before any write, byte for byte untouched")
    func refusesACorpus() throws {
        let path = try Self.freshPath()
        try DatabaseQueue(path: path).write { db in
            try db.execute(sql: "CREATE TABLE segments (segment_id INTEGER); PRAGMA application_id = 1396919491")
        }
        let before = try Data(contentsOf: URL(fileURLWithPath: path))
        #expect(throws: UserStoreError.notAUserStore(applicationID: 0x5343_4E43)) { try SavedDriveStore(path: path) }
        #expect(try Data(contentsOf: URL(fileURLWithPath: path)) == before)
    }

    @Test("every re-resolve row over both drives through reresolve(against:): returned and stored drives equal")
    func reresolveTable() throws {
        for row in SavedDriveResolveTable.rows {
            for drive in try SavedDriveResolveTable.drives() {
                let store = try SavedDriveStore(path: try Self.freshPath())
                let saved = try store.save(try row.input(drive))
                let corpus = FakeSavedDriveCorpus(segments: try row.corpus(saved))
                let expected = try row.expected(saved)
                #expect(try store.reresolve(against: corpus) == [expected], "\(row.name) / \(drive.name)")
                #expect(try store.list() == [expected], "\(row.name) / \(drive.name) as stored")
            }
        }
    }
}
#endif

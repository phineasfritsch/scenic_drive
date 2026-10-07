#if canImport(GRDB)
import Foundation
import GRDB
@testable import PlaceStore
import Testing

/// The user store's migrations (T-0290 R2): a file written by the earlier migration set upgrades in place with
/// every row preserved by full equality; a file recording a migration this build does not know is refused and
/// left byte for byte as it was (byte equality implies sha256 before == after).
@Suite("UserStore migrations")
struct UserStoreMigrationTests {
    @Test("a v1-only store upgrades in place: every row preserved by full equality, needsReplan false")
    func upgradesV1InPlace() throws {
        let path = try CorpusFixture.scratch().appendingPathComponent("user.sqlite").path
        let v1 = try DatabaseQueue(path: path)
        try UserStoreMigrations.migrator().migrate(v1, upTo: UserStoreMigrations.savedDrives)
        try v1.write { db in
            try db.execute(sql: """
                INSERT INTO saved_drive (id, name, lambda_e5, budget_minutes, created_at)
                VALUES (3, 'Angeles Crest', 250000, 60, 1790000000), (8, 'Empty', 0, 0, 1790000900);
                INSERT INTO saved_drive_segment (drive_id, position, segment_id, mid_lat_e5, mid_lon_e5)
                VALUES (3, 1, 77, 3425001, -11800002), (3, 0, 76, 3425000, -11800000);
                """)
        }
        try v1.close()

        let store = try SavedDriveStore(path: path)
        #expect(try store.list() == [
            try SavedDrive(id: 8, name: "Empty", segments: [], lambda: 0, budgetMinutes: 0, createdAt: 1_790_000_900),
            try SavedDrive(id: 3, name: "Angeles Crest", segments: [
                SavedSegment(segmentID: 76, midpoint: try SavedMidpoint(latitude: 34.25, longitude: -118)),
                SavedSegment(segmentID: 77, midpoint: try SavedMidpoint(latitude: 34.25001, longitude: -118.00002)),
            ], lambda: 2.5, budgetMinutes: 60, createdAt: 1_790_000_000, needsReplan: false),
        ])
        let applied = try DatabaseQueue(path: path).read { db in
            try String.fetchAll(db, sql: "SELECT identifier FROM grdb_migrations ORDER BY identifier")
        }
        #expect(applied == ["v1-saved-drives", "v2-needs-replan"])
    }

    @Test("a store recording an unknown migration is refused with its sorted identifiers and not modified")
    func refusesUnknownMigrations() throws {
        let path = try CorpusFixture.scratch().appendingPathComponent("user.sqlite").path
        let saved = try SavedDriveStore(path: path).save(try SavedDrive(name: "a", segments: [], lambda: 1,
                                                                         budgetMinutes: 5, createdAt: 9))
        #expect(saved.id == 1)
        let queue = try DatabaseQueue(path: path)
        try queue.write { db in
            try db.execute(sql: """
                INSERT INTO grdb_migrations (identifier) VALUES ('v4-later'), ('v3-from-the-future')
                """)
        }
        try queue.close()
        let before = try Data(contentsOf: URL(fileURLWithPath: path))
        #expect(throws: UserStoreError.unknownMigrations(["v3-from-the-future", "v4-later"])) {
            try SavedDriveStore(path: path)
        }
        #expect(try Data(contentsOf: URL(fileURLWithPath: path)) == before)
        let sidecars = try FileManager.default.contentsOfDirectory(atPath: (path as NSString).deletingLastPathComponent)
        #expect(sidecars == ["user.sqlite"])
    }
}
#endif

#if canImport(GRDB)
import Foundation
import GRDB
@testable import PlaceStore
import Testing

/// T-0312 R1, R3, R6, R8: the Surprise history in the user store. Every write is checked by FULL equality of the
/// whole table `list()` answers; the first launch upgrades a v1+v2 store in place with every saved drive kept.
@Suite("SurpriseShownStore")
struct SurpriseShownStoreTests {
    static func record(_ id: String, _ day: Int, category: String = "viewpoint") -> SurpriseShownRecord {
        SurpriseShownRecord(placeID: id, category: category, corridor: "pch", day: day)
    }

    static func path() throws -> String {
        try CorpusFixture.scratch().appendingPathComponent("user.sqlite").path
    }

    @Test("records round-trip whole, one row per place per day, sorted by day then place; a reopen reads the same")
    func roundTrip() throws {
        let path = try Self.path()
        let store = try SurpriseShownStore(path: path)
        #expect(try store.list() == [])
        let first = [Self.record("b", 20_733), Self.record("a", 20_733, category: "park"), Self.record("c", 20_700)]
        let expected = [Self.record("c", 20_700), Self.record("a", 20_733, category: "park"), Self.record("b", 20_733)]
        #expect(try store.record(first, keepingFrom: 20_644) == expected)
        #expect(try store.record([Self.record("a", 20_733), Self.record("a", 20_734)], keepingFrom: 20_644)
                == expected + [Self.record("a", 20_734)], "the same place the same day is not a second row")
        #expect(try SurpriseShownStore(path: path).list() == expected + [Self.record("a", 20_734)])
    }

    @Test("a write prunes every day before keepingFrom and keeps keepingFrom itself; a read prunes nothing")
    func prunesOnWrite() throws {
        let store = try SurpriseShownStore(path: try Self.path())
        let rows = [Self.record("old", 20_642), Self.record("edge", 20_643), Self.record("kept", 20_644),
                    Self.record("today", 20_733)]
        #expect(try store.record(rows, keepingFrom: 20_600) == rows)
        #expect(try store.list() == rows)
        #expect(try store.record([], keepingFrom: 20_644) == [Self.record("kept", 20_644), Self.record("today", 20_733)])
        #expect(try store.record([Self.record("stale", 20_643)], keepingFrom: 20_644)
                == [Self.record("kept", 20_644), Self.record("today", 20_733)], "a stale record is not kept")
    }

    @Test("first launch: a v1+v2 store upgrades to v3 in place, saved drives kept whole, then records")
    func upgradesV2InPlace() throws {
        let path = try Self.path()
        let v2 = try DatabaseQueue(path: path)
        try UserStoreMigrations.migrator().migrate(v2, upTo: UserStoreMigrations.needsReplan)
        try v2.write { db in
            try db.execute(sql: """
                INSERT INTO saved_drive (id, name, lambda_e5, budget_minutes, created_at, needs_replan)
                VALUES (3, 'Angeles Crest', 250000, 60, 1790000000, 1);
                INSERT INTO saved_drive_segment (drive_id, position, segment_id, mid_lat_e5, mid_lon_e5)
                VALUES (3, 0, 76, 3425000, -11800000);
                """)
        }
        try v2.close()
        let store = try SurpriseShownStore(path: path)
        #expect(try store.record([Self.record("a", 20_733)], keepingFrom: 20_644) == [Self.record("a", 20_733)])
        #expect(try SavedDriveStore(path: path).list() == [
            try SavedDrive(id: 3, name: "Angeles Crest", segments: [
                SavedSegment(segmentID: 76, midpoint: try SavedMidpoint(latitude: 34.25, longitude: -118)),
            ], lambda: 2.5, budgetMinutes: 60, createdAt: 1_790_000_000, needsReplan: true),
        ])
        let applied = try DatabaseQueue(path: path).read { db in
            try String.fetchAll(db, sql: "SELECT identifier FROM grdb_migrations ORDER BY identifier")
        }
        #expect(applied == ["v1-saved-drives", "v2-needs-replan", "v3-surprise-shown"])
    }

    @Test("the shared gate: a corpus file is refused before anything is written")
    func refusesACorpus() throws {
        let path = try Self.path()
        let corpus = try DatabaseQueue(path: path)
        try corpus.write { db in try db.execute(sql: "PRAGMA application_id = 1396920899") }
        try corpus.close()
        let before = try Data(contentsOf: URL(fileURLWithPath: path))
        #expect(throws: UserStoreError.notAUserStore(applicationID: 1_396_920_899)) {
            try SurpriseShownStore(path: path)
        }
        #expect(try Data(contentsOf: URL(fileURLWithPath: path)) == before)
    }
}
#endif

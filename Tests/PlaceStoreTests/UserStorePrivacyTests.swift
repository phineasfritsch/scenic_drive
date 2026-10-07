#if canImport(GRDB)
import Foundation
import GRDB
import PlaceStore
import Testing

/// P-PRIV-05's user-store half (T-0290 R7): every column of every table of a store the shipped
/// `SavedDriveStore(path:)` migrated, read by `PRAGMA table_info` - none names a place or a trail, and the whole
/// {table: [columns]} map equals R3's list exactly, so a new column of any name is red until it is ruled.
@Suite("UserStore privacy")
struct UserStorePrivacyTests {
    @Test("no column of the migrated user store matches home|address|breadcrumb|trail|speed; the columns are R3's")
    func noColumnNamesAPlaceOrATrail() throws {
        let path = try CorpusFixture.scratch().appendingPathComponent("user.sqlite").path
        _ = try SavedDriveStore(path: path)
        let columns = try DatabaseQueue(path: path).read { db -> [String: [String]] in
            var map: [String: [String]] = [:]
            for table in try String.fetchAll(db, sql: "SELECT name FROM sqlite_master WHERE type = 'table'") {
                map[table] = try Row.fetchAll(db, sql: "SELECT name FROM pragma_table_info(?) ORDER BY cid",
                                              arguments: [table]).map { row -> String in row["name"] }
            }
            return map
        }
        let forbidden = try Regex("home|address|breadcrumb|trail|speed").ignoresCase()
        let offending = columns.flatMap { table, names in
            names.filter { $0.contains(forbidden) || table.contains(forbidden) }.map { "\(table).\($0)" }
        }
        #expect(offending == [])
        #expect(columns == [
            "grdb_migrations": ["identifier"],
            "saved_drive": ["id", "name", "lambda_e5", "budget_minutes", "created_at", "needs_replan"],
            "saved_drive_segment": ["drive_id", "position", "segment_id", "mid_lat_e5", "mid_lon_e5"],
        ])
    }
}
#endif

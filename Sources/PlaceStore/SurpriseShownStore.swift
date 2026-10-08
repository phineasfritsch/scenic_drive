#if canImport(GRDB)
import Foundation
import GRDB

/// The device's Surprise history, in the user store beside the saved drives (T-0312 R1, R3, R8): the 90-day
/// no-repeat's memory across launches when there is no ledger session.
///
/// `init(path:)` passes SavedDriveStore's read-only gate first (a corpus file or an unknown migration is refused
/// before anything is written) and then migrates in place. Its own connection waits up to five seconds for a lock,
/// because SavedDriveShelf holds a second connection to the same file.
public final class SurpriseShownStore: Sendable {
    private let queue: DatabaseQueue

    public init(path: String) throws {
        if FileManager.default.fileExists(atPath: path) {
            try SavedDriveStore.inspect(path: path)
        }
        var configuration = Configuration()
        configuration.busyMode = .timeout(5)
        let queue = try DatabaseQueue(path: path, configuration: configuration)
        try UserStoreMigrations.migrator().migrate(queue)
        self.queue = queue
    }

    /// Inserts each record not already stored (one row per place per day), then deletes every row older than
    /// `oldestDay`, in one transaction, and answers the whole table as `list()` would (R3: pruned on write).
    public func record(_ records: [SurpriseShownRecord], keepingFrom oldestDay: Int) throws -> [SurpriseShownRecord] {
        try queue.write { db in
            for record in records {
                try db.execute(sql: """
                    INSERT OR IGNORE INTO surprise_shown (place_id, category, corridor, day) VALUES (?, ?, ?, ?)
                    """, arguments: [record.placeID, record.category, record.corridor, record.day])
            }
            try db.execute(sql: "DELETE FROM surprise_shown WHERE day < ?", arguments: [oldestDay])
            return try Self.all(db)
        }
    }

    /// Every stored row, oldest day first, then by place id. Reads never write.
    public func list() throws -> [SurpriseShownRecord] {
        try queue.read { db in try Self.all(db) }
    }

    private static func all(_ db: Database) throws -> [SurpriseShownRecord] {
        try Row.fetchAll(db, sql: "SELECT place_id, category, corridor, day FROM surprise_shown ORDER BY day, place_id")
            .map { row in
                SurpriseShownRecord(placeID: row["place_id"], category: row["category"], corridor: row["corridor"],
                                    day: row["day"])
            }
    }
}
#endif

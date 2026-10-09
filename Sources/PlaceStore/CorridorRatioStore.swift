#if canImport(GRDB)
import Foundation
import GRDB

/// The device's learned corridor speeds, in the user store beside the saved drives (T-0343 R3): what the learner
/// knew when the last edge was taught, read back at the next launch. They never leave the device (P-PRIV-05).
///
/// `init(path:)` passes SavedDriveStore's read-only gate first (a corpus file or an unknown migration is refused
/// before anything is written) and then migrates in place. Its own connection waits up to five seconds for a lock,
/// because SavedDriveShelf and SurpriseShownStore hold connections to the same file. The table's CHECK constraints
/// hold every bound the learner restores by, so a bad row is refused at the write and the old table kept.
public final class CorridorRatioStore: Sendable {
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

    /// Replaces the whole table with `records` in one transaction - a refused record (a bound, a repeated slot)
    /// throws and leaves the table as it was - and answers it as `list()` would.
    public func replaceAll(with records: [CorridorRatioRecord]) throws -> [CorridorRatioRecord] {
        try queue.write { db in
            try db.execute(sql: "DELETE FROM corridor_ratio")
            for record in records {
                try db.execute(sql: "INSERT INTO corridor_ratio (cell, hour, ratio, samples) VALUES (?, ?, ?, ?)",
                               arguments: [Int64(bitPattern: record.cell), record.hour, record.ratio, record.samples])
            }
            return try Self.all(db)
        }
    }

    /// Every stored row, by cell (as stored) then hour. Reads never write.
    public func list() throws -> [CorridorRatioRecord] {
        try queue.read { db in try Self.all(db) }
    }

    private static func all(_ db: Database) throws -> [CorridorRatioRecord] {
        try Row.fetchAll(db, sql: "SELECT cell, hour, ratio, samples FROM corridor_ratio ORDER BY cell, hour")
            .map { row in
                CorridorRatioRecord(cell: UInt64(bitPattern: row["cell"] as Int64), hour: row["hour"],
                                    ratio: row["ratio"], samples: row["samples"])
            }
    }
}
#endif

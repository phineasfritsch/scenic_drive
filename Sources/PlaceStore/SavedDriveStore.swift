#if canImport(GRDB)
import Foundation
import GRDB

/// The device's saved drives, in their own SQLite file (the app passes Application Support/user.sqlite, never the
/// corpus path). T-0290 R1, R2, R6.
///
/// `init(path:)` is the gate. An existing file is first opened READ-ONLY and refused - before anything is written -
/// unless its application_id is 0 (fresh) or "SCNU" and every migration it records is one this build knows. Only
/// then is it opened writable and migrated in place by `UserStoreMigrations.migrator()`.
public final class SavedDriveStore: Sendable {
    private let queue: DatabaseQueue

    public init(path: String) throws {
        if FileManager.default.fileExists(atPath: path) {
            try Self.inspect(path: path)
        }
        let queue = try DatabaseQueue(path: path)
        try UserStoreMigrations.migrator().migrate(queue)
        self.queue = queue
    }

    /// Inserts `drive` and returns it with the id the store gave it.
    public func save(_ drive: SavedDrive) throws -> SavedDrive {
        try queue.write { db in
            try db.execute(sql: """
                INSERT INTO saved_drive (name, lambda_e5, budget_minutes, created_at, needs_replan)
                VALUES (?, ?, ?, ?, ?)
                """, arguments: [drive.name, drive.lambdaE5, drive.budgetMinutes, drive.createdAt, drive.needsReplan])
            let id = db.lastInsertedRowID
            try Self.insertSegments(db, driveID: id, drive.segments)
            var saved = drive
            saved.id = id
            return saved
        }
    }

    /// Every saved drive, newest first: created_at descending, then id descending.
    public func list() throws -> [SavedDrive] {
        try queue.read { db in
            let rows = try Row.fetchAll(db, sql: """
                SELECT id, name, lambda_e5, budget_minutes, created_at, needs_replan FROM saved_drive
                ORDER BY created_at DESC, id DESC
                """)
            return try rows.map { row in
                let id: Int64 = row["id"]
                let segments = try Row.fetchAll(db, sql: """
                    SELECT segment_id, mid_lat_e5, mid_lon_e5 FROM saved_drive_segment
                    WHERE drive_id = ? ORDER BY position
                    """, arguments: [id]).map { segment in
                    SavedSegment(segmentID: segment["segment_id"],
                                 midpoint: SavedMidpoint(latE5: segment["mid_lat_e5"], lonE5: segment["mid_lon_e5"]))
                }
                return SavedDrive(id: id, name: row["name"], segments: segments, lambdaE5: row["lambda_e5"],
                                  budgetMinutes: row["budget_minutes"], createdAt: row["created_at"],
                                  needsReplan: row["needs_replan"])
            }
        }
    }

    public func rename(id: Int64, to name: String) throws {
        try queue.write { db in
            try db.execute(sql: "UPDATE saved_drive SET name = ? WHERE id = ?", arguments: [name, id])
            guard db.changesCount == 1 else { throw UserStoreError.driveNotFound(id: id) }
        }
    }

    /// Deletes the drive and, by the foreign key's ON DELETE CASCADE, its segments.
    public func delete(id: Int64) throws {
        try queue.write { db in
            try db.execute(sql: "DELETE FROM saved_drive WHERE id = ?", arguments: [id])
            guard db.changesCount == 1 else { throw UserStoreError.driveNotFound(id: id) }
        }
    }

    /// The shipped entry point on corpus activation: `SavedDriveResolver.resolve` over every stored drive, each
    /// result written back in one transaction and returned newest first (R5).
    public func reresolve(against corpus: SavedDriveCorpus) throws -> [SavedDrive] {
        let resolved = try list().map { try SavedDriveResolver.resolve($0, against: corpus) }
        try queue.write { db in
            for drive in resolved {
                guard let id = drive.id else { continue }
                try db.execute(sql: "UPDATE saved_drive SET needs_replan = ? WHERE id = ?",
                               arguments: [drive.needsReplan, id])
                try db.execute(sql: "DELETE FROM saved_drive_segment WHERE drive_id = ?", arguments: [id])
                try Self.insertSegments(db, driveID: id, drive.segments)
            }
        }
        return resolved
    }

    private static func insertSegments(_ db: Database, driveID: Int64, _ segments: [SavedSegment]) throws {
        for (position, segment) in segments.enumerated() {
            try db.execute(sql: """
                INSERT INTO saved_drive_segment (drive_id, position, segment_id, mid_lat_e5, mid_lon_e5)
                VALUES (?, ?, ?, ?, ?)
                """, arguments: [driveID, position, segment.segmentID, segment.midpoint.latE5,
                                 segment.midpoint.lonE5])
        }
    }

    /// The read-only gate (R1, R2): nothing here can write, so a refused file is byte-for-byte untouched. Shared by
    /// SurpriseShownStore (T-0312 R8), which opens the same file.
    static func inspect(path: String) throws {
        var configuration = Configuration()
        configuration.readonly = true
        let queue = try DatabaseQueue(path: path, configuration: configuration)
        defer { try? queue.close() }
        try queue.read { db in
            let applicationID = try Int.fetchOne(db, sql: "PRAGMA application_id") ?? 0
            guard applicationID == 0 || applicationID == UserStoreMigrations.applicationID else {
                throw UserStoreError.notAUserStore(applicationID: applicationID)
            }
            guard try db.tableExists("grdb_migrations") else { return }
            let applied = try String.fetchAll(db, sql: "SELECT identifier FROM grdb_migrations")
            let unknown = Set(applied).subtracting(UserStoreMigrations.identifiers).sorted()
            guard unknown.isEmpty else { throw UserStoreError.unknownMigrations(unknown) }
        }
    }
}
#endif

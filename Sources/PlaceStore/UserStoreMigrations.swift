#if canImport(GRDB)
import GRDB

/// The user store's schema, owned by one GRDB `DatabaseMigrator` with named migrations (T-0290 R2, R3, R3a).
///
/// The user store is its own file, never corpus.sqlite: an OTA corpus replacement swaps the corpus and never
/// touches this one (R1). Its columns are exactly R3's - no origin, destination, address, breadcrumb or speed
/// (P-PRIV-05, UserStorePrivacyTests).
enum UserStoreMigrations {
    /// `PRAGMA application_id` of every user store: the ASCII bytes "SCNU" big-endian.
    static let applicationID: Int = 0x5343_4E55

    static let savedDrives = "v1-saved-drives"
    static let needsReplan = "v2-needs-replan"
    static let surpriseShown = "v3-surprise-shown"
    static let corridorRatio = "v4-corridor-ratio"
    /// Every migration this build knows, in order. A file recording any other identifier is refused (R2).
    static let identifiers = [savedDrives, needsReplan, surpriseShown, corridorRatio]

    static func migrator() -> DatabaseMigrator {
        var migrator = DatabaseMigrator()
        migrator.registerMigration(savedDrives) { db in
            try db.execute(sql: """
                CREATE TABLE saved_drive (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    lambda_e5 INTEGER NOT NULL CHECK (lambda_e5 BETWEEN 0 AND 100000000),
                    budget_minutes INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE saved_drive_segment (
                    drive_id INTEGER NOT NULL REFERENCES saved_drive(id) ON DELETE CASCADE,
                    position INTEGER NOT NULL CHECK (position >= 0),
                    segment_id INTEGER NOT NULL,
                    mid_lat_e5 INTEGER NOT NULL CHECK (mid_lat_e5 BETWEEN -9000000 AND 9000000),
                    mid_lon_e5 INTEGER NOT NULL CHECK (mid_lon_e5 BETWEEN -18000000 AND 18000000),
                    PRIMARY KEY (drive_id, position)
                ) WITHOUT ROWID;
                PRAGMA application_id = \(applicationID);
                """)
        }
        migrator.registerMigration(needsReplan) { db in
            try db.execute(sql: """
                ALTER TABLE saved_drive
                ADD COLUMN needs_replan INTEGER NOT NULL DEFAULT 0 CHECK (needs_replan IN (0, 1))
                """)
        }
        // T-0312 R1: the device's Surprise history - a place, its category and corridor, and the civil day it was
        // shown; one row per place per day. No coordinate, cell or time of day (P-PRIV-05).
        migrator.registerMigration(surpriseShown) { db in
            try db.execute(sql: """
                CREATE TABLE surprise_shown (
                    place_id TEXT NOT NULL CHECK (length(place_id) > 0),
                    category TEXT NOT NULL,
                    corridor TEXT NOT NULL,
                    day INTEGER NOT NULL,
                    PRIMARY KEY (place_id, day)
                ) WITHOUT ROWID
                """)
        }
        // T-0343 R3: the learned corridor slots - an H3-8 cell (the UInt64 index's bit pattern), the hour of the
        // week, the ratio and its samples, every bound the learner restores by held here too. No column names a
        // speed, a place or a trail (P-PRIV-05), and nothing here leaves the device.
        migrator.registerMigration(corridorRatio) { db in
            try db.execute(sql: """
                CREATE TABLE corridor_ratio (
                    cell INTEGER NOT NULL,
                    hour INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 167),
                    ratio REAL NOT NULL CHECK (ratio BETWEEN 0.3 AND 1.0),
                    samples INTEGER NOT NULL CHECK (samples >= 1),
                    PRIMARY KEY (cell, hour)
                ) WITHOUT ROWID
                """)
        }
        return migrator
    }
}
#endif

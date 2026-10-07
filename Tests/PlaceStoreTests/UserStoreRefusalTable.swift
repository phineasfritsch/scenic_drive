#if canImport(GRDB)
import Foundation
import GRDB
@testable import PlaceStore

/// The user store's refusal fixtures (T-0290 R1, R2): the cross product of every applied prefix of
/// `UserStoreMigrations.identifiers` - none, v1 only, v1 and v2, and any later prefix by itself - with every way a
/// file is refused. A prefix short of all of them leaves the migrator work to do, so a store that migrated before
/// refusing would write to it; the rows are generated from the shipped identifiers, so a new migration adds its
/// prefix rows with no edit here.
struct UserStoreRefusalTable {
    enum Refusal: CaseIterable {
        case oneUnknownMigration
        case twoUnknownMigrations
        case corpusApplicationID
    }

    /// The "SCNC" application_id corpus.sqlite carries.
    static let corpusApplicationID = 0x5343_4E43

    let applied: [String]
    let refusal: Refusal

    static var rows: [UserStoreRefusalTable] {
        (0...UserStoreMigrations.identifiers.count).flatMap { count in
            Refusal.allCases.map { refusal in
                UserStoreRefusalTable(applied: Array(UserStoreMigrations.identifiers.prefix(count)), refusal: refusal)
            }
        }
    }

    var name: String { "applied \(applied) + \(refusal)" }

    /// The identifiers this build does not know, in the order the fixture inserts them (deliberately unsorted).
    var unknown: [String] {
        switch refusal {
        case .oneUnknownMigration: ["v3-from-the-future"]
        case .twoUnknownMigrations: ["v4-later", "v3-from-the-future"]
        case .corpusApplicationID: []
        }
    }

    /// The error `SavedDriveStore(path:)` must throw: application_id is checked before the identifiers.
    var expected: UserStoreError {
        switch refusal {
        case .oneUnknownMigration, .twoUnknownMigrations: .unknownMigrations(unknown.sorted())
        case .corpusApplicationID: .notAUserStore(applicationID: Self.corpusApplicationID)
        }
    }

    /// Writes the fixture at `path` - the shipped migrator up to the prefix (with one saved drive once the table
    /// exists), or a bare grdb_migrations table for the empty prefix - and returns the identifiers it records.
    func build(at path: String) throws -> [String] {
        let queue = try DatabaseQueue(path: path)
        if let last = applied.last {
            try UserStoreMigrations.migrator().migrate(queue, upTo: last)
            try queue.write { db in
                try db.execute(sql: """
                    INSERT INTO saved_drive (name, lambda_e5, budget_minutes, created_at) VALUES ('a', 100000, 5, 9)
                    """)
            }
        } else {
            try queue.write { db in
                try db.execute(sql: "CREATE TABLE grdb_migrations (identifier TEXT NOT NULL PRIMARY KEY)")
            }
        }
        try queue.write { db in
            for identifier in unknown {
                try db.execute(sql: "INSERT INTO grdb_migrations (identifier) VALUES (?)", arguments: [identifier])
            }
            if refusal == .corpusApplicationID {
                try db.execute(sql: "PRAGMA application_id = \(Self.corpusApplicationID)")
            }
        }
        let recorded = try queue.read { db in
            try String.fetchAll(db, sql: "SELECT identifier FROM grdb_migrations ORDER BY identifier")
        }
        try queue.close()
        return recorded
    }
}
#endif

#if !canImport(GRDB)
import XCTest

/// The Windows dev toolchain ships no sqlite3.h / sqlite3.lib, so Package.swift conditions GRDB off there and
/// PlaceStore is empty (T-0175 ruling R2). This says so in the test output instead of running nothing silently.
final class PlaceStoreNoSQLiteTests: XCTestCase {
    func testPlaceStoreNeedsSystemSQLite() throws {
        throw XCTSkip("PlaceStore links the system SQLite through GRDB; this toolchain has none. "
                      + "Linux CI (linux-core, libsqlite3-dev) runs PlaceStoreTests.")
    }
}
#endif

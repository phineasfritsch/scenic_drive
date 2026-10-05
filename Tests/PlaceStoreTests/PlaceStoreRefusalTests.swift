#if canImport(GRDB)
import PlaceStore
import XCTest

/// `PlaceStore(path:)` - the entry point a device runs - refusing files it must not read. Each corpus is the
/// shipping build with ONE meta edit, so a refusal here is the check, not a malformed fixture.
final class PlaceStoreRefusalTests: XCTestCase {
    func testRefusesCorpusWithBumpedSchemaVersion() throws {
        let corpus = try CorpusFixture.build(rewriting: "UPDATE meta SET value = '4' WHERE key = 'schema_version'")
        XCTAssertThrowsError(try PlaceStore(path: corpus.path)) { error in
            XCTAssertEqual(error as? PlaceStoreError, .schemaVersionMismatch(found: "4", expected: 3))
        }
    }

    func testRefusesCorpusWithNoSchemaVersion() throws {
        let corpus = try CorpusFixture.build(rewriting: "DELETE FROM meta WHERE key = 'schema_version'")
        XCTAssertThrowsError(try PlaceStore(path: corpus.path)) { error in
            XCTAssertEqual(error as? PlaceStoreError, .missingMeta(key: "schema_version"))
        }
    }

    func testRefusesIncompleteBuild() throws {
        let corpus = try CorpusFixture.build(rewriting: "UPDATE meta SET value = '0' WHERE key = 'build_complete'")
        XCTAssertThrowsError(try PlaceStore(path: corpus.path)) { error in
            XCTAssertEqual(error as? PlaceStoreError, .incompleteBuild(buildComplete: "0"))
        }
    }

    func testRefusesSQLiteFileThatIsNotACorpus() throws {
        let other = try CorpusFixture.notACorpus()
        XCTAssertThrowsError(try PlaceStore(path: other.path)) { error in
            XCTAssertEqual(error as? PlaceStoreError, .notACorpus(applicationID: 0))
        }
    }

    func testRefusesMalformedMinAppBuild() throws {
        let corpus = try CorpusFixture.build(rewriting: "UPDATE meta SET value = 'one' WHERE key = 'min_app_build'")
        XCTAssertThrowsError(try PlaceStore(path: corpus.path).meta()) { error in
            XCTAssertEqual(error as? PlaceStoreError, .malformedMeta(key: "min_app_build", value: "one"))
        }
    }
}
#endif

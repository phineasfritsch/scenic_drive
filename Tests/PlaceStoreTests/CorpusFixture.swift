#if canImport(GRDB)
import Foundation
import GRDB
import XCTest

/// A corpus.sqlite built by the SHIPPING builder, `python -m etl.corpus`, from the committed
/// services/etl/tests/fixtures/corpus_extract.json - never a committed .sqlite (T-0175 ruling R6). A committed
/// file would keep its schema_version forever; a built one moves with services/etl/etl/schema.py, so a DDL
/// bump without a PlaceStore bump turns this suite red.
///
/// The measured population (T-0175 Log): 7 ways, 79 segments, region `fixture`, application_id "SCNC".
enum CorpusFixture {
    static let root = URL(fileURLWithPath: #filePath)   // Tests/PlaceStoreTests/<this file>
        .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    static let etl = root.appendingPathComponent("services/etl")
    static let extract = etl.appendingPathComponent("tests/fixtures/corpus_extract.json")
    /// One way and nine places (T-0254 ruling R7): the extract's optional `places` array, read by the shipping
    /// builder like the ways. The place rows are the literals PlaceStoreSearchTests types out.
    static let placesExtract = etl.appendingPathComponent("tests/fixtures/corpus_extract_places.json")
    /// One way and eight places, one per token category of T-0254 ruling R6 (PlaceStoreTokenClassTests).
    static let tokenClassesExtract = etl.appendingPathComponent("tests/fixtures/corpus_extract_token_classes.json")
    static let builtAt ="2026-09-18T00:00:00Z"

    /// A fresh directory per call, so no test reads a file another test rewrote.
    static func scratch() throws -> URL {
        let dir = FileManager.default.temporaryDirectory
            .appendingPathComponent("placestore-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    /// Runs the shipping builder. No interpreter, or a non-zero exit, is a test FAILURE - never a skip.
    static func build(extract: URL = CorpusFixture.extract) throws -> URL {
        let out = try scratch().appendingPathComponent("corpus.sqlite")
        let python = ProcessInfo.processInfo.environment["PYTHON"] ?? "python3"
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = [python, "-m", "etl.corpus", "--input", extract.path, "--out", out.path,
                             "--built-at", builtAt]
        process.currentDirectoryURL = etl
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        try process.run()
        let output = String(decoding: pipe.fileHandleForReading.readDataToEndOfFile(), as: UTF8.self)
        process.waitUntilExit()
        guard process.terminationStatus == 0 else {
            XCTFail("`\(python) -m etl.corpus` exited \(process.terminationStatus):\n\(output)")
            throw CocoaError(.fileWriteUnknown)
        }
        return out
    }

    /// The built corpus with ONE edit applied through a writable connection.
    static func build(rewriting sql: String) throws -> URL {
        let out = try build()
        let queue = try DatabaseQueue(path: out.path)
        try queue.write { db in try db.execute(sql: sql) }
        try queue.close()
        return out
    }

    /// A plain SQLite file that is not a corpus: application_id 0, no tables.
    static func notACorpus() throws -> URL {
        let out = try scratch().appendingPathComponent("other.sqlite")
        let queue = try DatabaseQueue(path: out.path)
        try queue.write { db in try db.execute(sql: "CREATE TABLE t (x INTEGER)") }
        try queue.close()
        return out
    }
}
#endif

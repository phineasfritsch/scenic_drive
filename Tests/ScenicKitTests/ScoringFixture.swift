import Foundation

/// `Tests/Fixtures/scoring/segment_terms.json` as decoded: the shared scorer contract.
///
/// The same bytes are read by `services/etl/tests/test_score_contract.py`. Neither side may edit the file to
/// make itself pass - it is regenerated only by `Tests/Fixtures/scoring/generate.py`, whose expectations come
/// from a hand transcription of the plan.
struct ScoringFixture: Decodable, Sendable {
    let generator: String
    let oracle: String
    let seed: Int
    let coveringRows: Int
    let rowCount: Int
    let rows: [ScoringFixtureRow]

    /// The fixture's path, derived from this file rather than from a working directory: `swift test` is run
    /// from the repo root, from worktrees and from mutation scratch paths in this repository, and the
    /// package declares no test resources (both `Package.swift` files are serial-only).
    static var fixtureURL: URL {
        URL(fileURLWithPath: #filePath)     // Tests/ScenicKitTests/ScoringFixture.swift
            .deletingLastPathComponent()    // Tests/ScenicKitTests
            .deletingLastPathComponent()    // Tests
            .appendingPathComponent("Fixtures/scoring/segment_terms.json")
    }

    /// Throws rather than returning an empty fixture: a contract that silently checked nothing would be
    /// green, and green is exactly what it must not be.
    static func load() throws -> ScoringFixture {
        let data = try Data(contentsOf: fixtureURL)
        return try JSONDecoder().decode(ScoringFixture.self, from: data)
    }
}

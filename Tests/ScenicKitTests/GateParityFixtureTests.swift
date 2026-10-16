import Foundation
import Testing
@testable import ScenicKit

/// P-PROD-01 (T-0012): ONE fixture of ways, three consumers, one expected verdict per row.
///
/// services/etl/tests/fixtures/gate_parity.json is read here through `Gates.decide` and `SegmentScore`, and by
/// services/etl/tests/test_gate_parity.py through the ETL's `assemble.scored_row` and `etl.profilegate` over the
/// shipped car_scenic_base.json. A row's `verdict` is the product's answer - ScenicKit's - and every failure
/// names ScenicKit and what the ETL and the profile are held to for that row.
@Suite("Gate parity fixture")
struct GateParityFixtureTests {

    static let fixture = URL(fileURLWithPath: #filePath)   // Tests/ScenicKitTests/<this file>
        .deletingLastPathComponent()                       // Tests/ScenicKitTests
        .deletingLastPathComponent()                       // Tests
        .deletingLastPathComponent()                       // repository root
        .appendingPathComponent("services/etl/tests/fixtures/gate_parity.json")

    struct Row {
        let name: String
        let wayID: Int?
        let tags: [String: String]
        let verdict: String
        let divergent: [String: String]?
    }

    static func rows() throws -> [Row] {
        let data = try Data(contentsOf: fixture)
        let root = try #require(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        let rows = try #require(root["rows"] as? [[String: Any]])
        return try rows.map { row in
            Row(name: try #require(row["class"] as? String),
                wayID: row["way_id"] as? Int,
                tags: try #require(row["tags"] as? [String: String]),
                verdict: try #require(row["verdict"] as? String),
                divergent: row["divergent"] as? [String: String])
        }
    }

    static let pavedSurface = "asphalt"
    static let neutral = 0.5

    static func terms(_ tags: [String: String], surface: String?) -> SegmentTerms {
        SegmentTerms(curvature: neutral, elevationGain: neutral, speedFit: neutral, sinuosity: neutral,
                     canopy: neutral, relief: neutral, impervious: neutral, pointsOfInterest: neutral,
                     water: neutral, furniture: neutral, highway: tags["highway"] ?? "", surface: surface)
    }

    /// ScenicKit's verdict for one row: the gate first, then the score against the same way on a paved surface.
    static func scenicKitVerdict(_ tags: [String: String]) -> String {
        if !Gates.decide(tags).isAllowed { return "GATED" }
        let asTagged = terms(tags, surface: tags["surface"])
        guard let score = SegmentScore.score(for: asTagged),
              let paved = SegmentScore.score(for: terms(tags, surface: pavedSurface)) else {
            return "INCONSISTENT(no score)"
        }
        let flagged = SegmentScore.raisesSurfaceUnknownFlag(asTagged)
        if !flagged && score == 0 && paved == 0 { return "ZERO_NOT_GATED" }
        if !flagged && score > 0 && score == paved { return "PAVED" }
        if flagged && score > 0 && abs(score - 0.8 * paved) <= 1e-12 * paved { return "UNKNOWN_X08" }
        return "INCONSISTENT(score=\(score) paved=\(paved) surface_unknown=\(flagged))"
    }

    @Test("every row of the parity fixture gets its verdict from Gates.decide and SegmentScore")
    func everyRowGetsTheFixtureVerdict() throws {
        let rows = try Self.rows()
        #expect(rows.count == 30)
        for row in rows {
            let got = Self.scenicKitVerdict(row.tags)
            let etl = row.divergent?["etl"] ?? row.verdict
            let profile = row.divergent?["profile"] ?? (row.verdict == "GATED" ? "GATED" : "NOT_GATED")
            #expect(got == row.verdict, """
                \(row.name) (way \(row.wayID.map(String.init) ?? "synthetic")): ScenicKit (Gates.decide + \
                SegmentScore) says \(got), expected \(row.verdict); the ETL is held to \(etl) and the profile \
                (car_scenic_base.json) to \(profile) for this row by test_gate_parity.py
                """)
        }
    }

    @Test("motorway and trunk rows score zero and are never gated by ScenicKit")
    func motorwayAndTrunkArePenalisedNotGated() throws {
        let rows = try Self.rows().filter { ["motorway", "motorway_link", "trunk", "trunk_link"].contains($0.name) }
        #expect(rows.count == 4)
        for row in rows {
            #expect(Gates.decide(row.tags).isAllowed, "ScenicKit gates \(row.name): penalised, never excluded")
            #expect(SegmentScore.score(for: Self.terms(row.tags, surface: row.tags["surface"])) == 0,
                    "ScenicKit scores \(row.name) above zero")
        }
    }
}

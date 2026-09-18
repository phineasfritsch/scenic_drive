import Foundation
import Testing
@testable import ScenicKit

/// The ScenicKit half of the scorer contract. `services/etl/tests/test_score_contract.py` is the other half
/// and reads the same bytes.
///
/// Tolerance is the plan's own number (plan:219, *"ScenicKit `SegmentScore` differential vs corpus on 1,000
/// sampled segments < 1e-6"*). The expectations are a hand transcription of the plan inside
/// `Tests/Fixtures/scoring/generate.py`, so this suite can contradict `SegmentScore` - which is the point,
/// and which it did: written against `isByway: Bool` it reported *"240 of 1000 rows disagree with the oracle
/// by >= 1e-06; worst delta 0.13076020187735218 at axis-scenery-zero-eligible"*, every one of them an
/// eligible-tier row, because ScenicKit paid one bonus of 0.15 where the ETL pays 0.06 for an *eligible*
/// byway (`byways.py:105`).
///
/// Failures are reported BY ROW ID. A count tells the next agent nothing; `cap-below-eligible` tells them
/// which property broke.
@Suite("SegmentScore contract (shared fixture)")
struct SegmentScoreContractTests {
    static let tolerance = 1e-6

    /// The one translation point: the fixture's neutral tier word becomes this package's type. The switch is
    /// over a String, so it needs a `default:` - and that arm records an Issue and throws, so a tier word the
    /// fixture gains is a loud test failure here rather than silently scored as a tier that already exists.
    static func tier(_ name: String) throws -> BywayTier {
        switch name {
        case "none": return .none
        case "eligible": return .eligible
        case "designated": return .designated
        default:
            Issue.record("unknown byway tier \(name) in the fixture")
            throw ContractFailure.unknownTier
        }
    }

    enum ContractFailure: Error { case unknownTier }

    static func terms(_ r: ScoringFixtureRow) throws -> SegmentTerms {
        SegmentTerms(curvature: r.curvature, elevationGain: r.elevationGain, speedFit: r.speedFit,
                     sinuosity: r.sinuosity, canopy: r.canopy, relief: r.relief, impervious: r.impervious,
                     pointsOfInterest: r.pointsOfInterest, water: r.water, furniture: r.furniture,
                     bywayTier: try tier(r.bywayTier), highway: r.highway, surface: r.surface,
                     tunnelMeters: r.tunnelMeters, metersToNearestMotorway: r.metersToNearestMotorway)
    }

    static func row(_ fixture: ScoringFixture, _ id: String) throws -> ScoringFixtureRow {
        try #require(fixture.rows.first { $0.id == id }, "the fixture has no row \(id)")
    }

    @Test("the fixture is the whole population it claims")
    func fixtureIsWhole() throws {
        let fixture = try ScoringFixture.load()
        #expect(fixture.rows.count == fixture.rowCount,
                "rowCount says \(fixture.rowCount), the file carries \(fixture.rows.count)")
        #expect(fixture.rows.count >= 1000, "the plan's differential is over 1,000 segments")
        #expect(Set(fixture.rows.map(\.id)).count == fixture.rows.count, "duplicate row ids")
    }

    @Test("the fixture covers the properties this contract exists for")
    func fixtureCovers() throws {
        let fixture = try ScoringFixture.load()
        #expect(Set(fixture.rows.map(\.bywayTier)) == ["none", "eligible", "designated"])
        let classes = Set(fixture.rows.map(\.highway))
        #expect(SegmentScore.dullClasses.isSubset(of: classes),
                "missing dull class(es): \(SegmentScore.dullClasses.subtracting(classes).sorted())")
        for tier in ["eligible", "designated"] {
            let scorable = fixture.rows.filter {
                $0.bywayTier == tier && !SegmentScore.dullClasses.contains($0.highway) && $0.expected > 0
            }
            #expect(scorable.count >= 50, "\(tier): only \(scorable.count) rows can show the bonus at all")
        }
        #expect(fixture.rows.contains { $0.tunnelMeters > SegmentScore.tunnelThresholdMeters })
        #expect(fixture.rows.contains { $0.tunnelMeters == SegmentScore.tunnelThresholdMeters })
        #expect(fixture.rows.contains { $0.metersToNearestMotorway < SegmentScore.motorwayProximityMeters })
        #expect(fixture.rows.contains { $0.metersToNearestMotorway == SegmentScore.motorwayProximityMeters })
        #expect(fixture.rows.contains { $0.surface == nil
            && SegmentScore.unsurveyedClasses.contains($0.highway) })
        for term in [\ScoringFixtureRow.curvature, \ScoringFixtureRow.canopy, \ScoringFixtureRow.furniture] {
            #expect(fixture.rows.contains { $0[keyPath: term] == 0 })
            #expect(fixture.rows.contains { $0[keyPath: term] == 1 })
        }
    }

    @Test("every fixture row scores within 1e-6 of the oracle")
    func everyRowMatchesTheOracle() throws {
        let fixture = try ScoringFixture.load()
        var failures: [String] = []
        var worst = 0.0
        var worstID = "none"
        for r in fixture.rows {
            guard let got = SegmentScore.score(for: try Self.terms(r)) else {
                failures.append("\(r.id): score returned nil on an in-range row")
                continue
            }
            let delta = abs(got - r.expected)
            if delta > worst { worst = delta; worstID = r.id }
            if !(delta < Self.tolerance) {
                failures.append("\(r.id): got \(got), oracle \(r.expected), delta \(delta) "
                                + "(tier=\(r.bywayTier) highway=\(r.highway))")
            }
        }
        for line in failures.prefix(20) { Issue.record("\(line)") }
        let summary = "\(failures.count) of \(fixture.rows.count) rows disagree with the oracle by >= "
            + "\(Self.tolerance); worst delta \(worst) at \(worstID)"
        #expect(failures.isEmpty, "\(summary)")
    }

    /// Guards the differential itself. If ScenicKit could not tell the two tiers apart, every eligible row
    /// would agree with a scorer that pays the designated bonus for both - which is the defect this contract
    /// was written to catch, and was ScenicKit's behaviour until T-0154.
    @Test("an eligible byway scores strictly below a designated one on the same road")
    func tiersAreNotTheSameNumber() throws {
        let fixture = try ScoringFixture.load()
        let plain = try SegmentScore.score(for: Self.terms(Self.row(fixture, "cap-below-none")))
        let eligible = try SegmentScore.score(for: Self.terms(Self.row(fixture, "cap-below-eligible")))
        let designated = try SegmentScore.score(for: Self.terms(Self.row(fixture, "cap-below-designated")))
        let p = try #require(plain), e = try #require(eligible), d = try #require(designated)
        #expect(p < e, "an eligible byway must beat no byway at all (\(p) vs \(e))")
        #expect(e < d, "an eligible byway must not be paid the designated bonus (\(e) vs \(d))")
    }

    /// plan:83, and CLAUDE.md's invariant. Zero on scenery, still routable: the two mechanisms are separate
    /// and the freeway-shoulders design needs both at once.
    @Test("a dull class scores zero in the fixture however pretty its terms are")
    func dullClassesScoreZero() throws {
        let fixture = try ScoringFixture.load()
        var checked = 0
        for r in fixture.rows where SegmentScore.dullClasses.contains(r.highway) {
            checked += 1
            #expect(r.expected == 0, "the oracle scored \(r.id) at \(r.expected)")
            let got = try #require(SegmentScore.score(for: Self.terms(r)), "\(r.id) scored nil")
            #expect(got == 0, "\(r.id) scored \(got)")
        }
        #expect(checked >= 40, "only \(checked) dull-class rows - the invariant is barely exercised")
    }
}

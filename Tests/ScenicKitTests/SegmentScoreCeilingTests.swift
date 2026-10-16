import Foundation
import Testing
@testable import ScenicKit

/// T-0218: a residential, living_street or service way never shows a higher number on the device than the
/// router uses. Every row goes through the SHIPPING entry `SegmentScoreCeiling.score(for:)` and is compared
/// EXACTLY with min(SegmentScore.score(for:), assemble.py's ceiling for the class) - the ETL table parsed by
/// identifier, not this package's copy.
///
/// The probes sit ON each nonzero ceiling: the identity terms (every positive term s, impervious and
/// furniture 1 - s) make M = E = s, so the score is s to rounding, and the test bisects s to the two adjacent
/// doubles whose scores straddle the ceiling. Rows are a cross product - class x probe x byway tier x surface
/// - because the ceiling must not be conditioned on any input the score reads (T-0207 R3's two survivors).
@Suite("SegmentScoreCeiling (T-0218)")
struct SegmentScoreCeilingTests {

    static let fixtureClasses = ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
                                 "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
                                 "residential", "living_street", "service"]
    /// Spellings Python's `dict.get` does not match, so the ETL ships them uncapped and so must the device.
    static let nearMisses = ["Residential", "residential ", " service", "living-street", "services", "SERVICE", ""]
    static let tiers: [BywayTier] = [.none, .eligible, .designated]
    static let surfaces: [String?] = ["asphalt", nil]

    static func identity(_ s: Double, highway: String, tier: BywayTier = .none,
                         surface: String? = "asphalt") -> SegmentTerms {
        SegmentTerms(curvature: s, elevationGain: s, speedFit: s, sinuosity: s, canopy: s, relief: s,
                     impervious: 1 - s, pointsOfInterest: s, water: s, furniture: 1 - s, bywayTier: tier,
                     highway: highway, surface: surface)
    }

    /// The two adjacent doubles lo < hi with formula(lo) <= c < formula(hi) on an uncapped paved class.
    static func straddle(_ c: Double) throws -> (lo: Double, hi: Double) {
        func f(_ s: Double) -> Double { SegmentScore.score(for: identity(s, highway: "tertiary")) ?? .nan }
        var lo = 0.0, hi = 1.0
        while lo.nextUp < hi {
            let mid = lo + (hi - lo) / 2
            if f(mid) <= c { lo = mid } else { hi = mid }
        }
        try #require(f(lo) <= c && f(hi) > c && lo.nextUp == hi, "no straddle of \(c): \(f(lo)) \(f(hi))")
        return (lo, hi)
    }

    @Test("the ceiling table is assemble.CLASS_SCORE_CEILING, parsed by identifier")
    func tableIsTheETLTable() throws {
        let etl = try ETLCeilingTable.load()
        #expect(!etl.isEmpty, "assemble.py's ceiling table parsed empty")
        #expect(SegmentScoreCeiling.byClass == etl,
                "ScenicKit \(SegmentScoreCeiling.byClass.sorted { $0.key < $1.key }) vs ETL \(etl.sorted { $0.key < $1.key })")
    }

    @Test("every class x bound x tier x surface is min(formula, the ETL ceiling), exactly")
    func everyClassAndBound() throws {
        let etl = try ETLCeilingTable.load()
        var probes: [Double] = [0, 1e-9, 1]
        for c in Set(etl.values) where c > 0 {
            let (lo, hi) = try Self.straddle(c)
            probes += [lo, hi]
        }
        var classes: [String] = []
        for h in Self.fixtureClasses + etl.keys.sorted() + Self.nearMisses where !classes.contains(h) {
            classes.append(h)
        }
        var failures: [String] = []
        var capped: Set<String> = [], uncappedPositive: Set<String> = []
        var rows = 0
        for h in classes {
            for s in probes {
                for tier in Self.tiers {
                    for surface in Self.surfaces {
                        let t = Self.identity(s, highway: h, tier: tier, surface: surface)
                        let formula = try #require(SegmentScore.score(for: t), "formula refused \(h) s=\(s)")
                        let expected = min(formula, etl[h] ?? .infinity)
                        let got = SegmentScoreCeiling.score(for: t)
                        rows += 1
                        if got != expected {
                            failures.append("\(h) s=\(s) tier=\(tier) surface=\(surface ?? "nil"): "
                                            + "got \(got.map { "\($0)" } ?? "nil"), expected \(expected)")
                        }
                        if let c = etl[h] {
                            if formula > c { capped.insert(h) } else if formula > 0 { uncappedPositive.insert(h) }
                        }
                    }
                }
            }
        }
        for line in failures.prefix(20) { Issue.record("\(line)") }
        #expect(failures.isEmpty, "\(failures.count) of \(rows) rows disagree")
        // Meta: the table really crosses every ceiling - a capped row on every class, an uncapped
        // positive row on every class whose ceiling is above zero.
        #expect(capped == Set(etl.keys), "classes never capped by a probe: \(Set(etl.keys).subtracting(capped))")
        let positive = Set(etl.filter { $0.value > 0 }.keys)
        #expect(uncappedPositive.isSuperset(of: positive), "no uncapped probe on \(positive.subtracting(uncappedPositive))")
    }

    @Test("refused terms stay refused on every ceiling class, never the ceiling")
    func refusalsStayRefused() throws {
        let etl = try ETLCeilingTable.load()
        for h in etl.keys.sorted() + ["tertiary"] {
            for bad in [-0.0001, 1.0001, Double.nan] {
                var t = Self.identity(0.5, highway: h)
                t.canopy = bad
                #expect(SegmentScoreCeiling.score(for: t) == nil, "\(h) canopy=\(bad) was not refused")
            }
            var tunnel = Self.identity(0.5, highway: h)
            tunnel.tunnelMeters = -1
            #expect(SegmentScoreCeiling.score(for: tunnel) == nil, "\(h) tunnel -1 was not refused")
        }
    }

    @Test("the ETL table reader refuses what it cannot read whole")
    func readerFailsClosed() {
        let good = "CLASS_SCORE_CEILING = {\"residential\": 0.6499}\n    ceiling = CLASS_SCORE_CEILING.get(record.highway)\n"
        #expect((try? ETLCeilingTable.parse(good)) == ["residential": 0.6499])
        let bad = [
            "x = 1\n",
            good + "CLASS_SCORE_CEILING = {\"service\": 0.0}\n",
            good + "CLASS_SCORE_CEILING[\"unclassified\"] = 0.6499\n",
            good + "CLASS_SCORE_CEILING.update(unclassified=0.6499)\n",
            "CLASS_SCORE_CEILING = {\"residential\": 0.6499,\n    \"service\": 0.0}\n",
            "CLASS_SCORE_CEILING = dict(residential=0.6499)\n",
            "CLASS_SCORE_CEILING = {\"residential\": \"high\"}\n",
        ]
        for text in bad {
            #expect((try? ETLCeilingTable.parse(text)) == nil, "read: \(text)")
        }
    }
}

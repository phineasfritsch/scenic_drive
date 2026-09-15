import Foundation
import Testing
@testable import ScenicKit

/// Validation is the half of `SegmentScore` that produces **nil**, and it was the half that was barely pinned.
///
/// `SegmentTerms.unitTerms` exists so that a term added later cannot quietly escape the `0...1` check, and the
/// suite next door probed four of the ten terms - so seven of them could be deleted from that list with
/// nothing objecting, and the one mutation written against the list removed `water`, one of the four that
/// happened to be probed. The same shape covered the two non-unit inputs: the whole
/// `metersToNearestMotorway` guard could be deleted, and `tunnelMeters.isFinite` dropped, in silence.
///
/// Two rules for everything here:
///
/// * the term list below is **transcribed by hand**, never derived from `SegmentTerms.unitTerms`. Reading the
///   list under test to decide what to test with makes the test agree with any list, an empty one included.
/// * the boundary probes are `1.0.nextUp` and `0.0.nextDown` - the nearest representable Doubles outside the
///   window, a fact about IEEE 754 and not about this code. A probe computed from the window it is testing
///   cancels against it and holds for every window.
@Suite("Segment score validation")
struct SegmentScoreValidationTests {

    /// Every `0...1` term, written out independently of `SegmentTerms.unitTerms`, which is the list on trial.
    ///
    /// Computed rather than stored because `WritableKeyPath` is not `Sendable`, and a stored static would be
    /// shared mutable state under Swift 6 concurrency checking.
    static var unitTermPaths: [(name: String, path: WritableKeyPath<SegmentTerms, Double>)] {
        [("curvature", \.curvature), ("elevationGain", \.elevationGain), ("speedFit", \.speedFit),
         ("sinuosity", \.sinuosity), ("canopy", \.canopy), ("relief", \.relief),
         ("impervious", \.impervious), ("pointsOfInterest", \.pointsOfInterest),
         ("water", \.water), ("furniture", \.furniture)]
    }

    /// Deliberately a local copy of the neighbouring suite's fixture builder rather than a call into it.
    /// `--prove-vacuity` empties every test file at once, so sharing would cost nothing there - but the way
    /// to check that this suite really is in the harness's TEST_FILES is to empty the OTHER file alone and
    /// watch this one go on catching mutations. A cross-file helper turns that measurement into a build
    /// error, which proves nothing about the vacuity arm.
    static func split(drive m: Double, scenery e: Double, highway: String = "tertiary") -> SegmentTerms {
        SegmentTerms(curvature: m, elevationGain: m, speedFit: m, sinuosity: m,
                     canopy: e, relief: e, impervious: 1 - e, pointsOfInterest: e, water: e,
                     furniture: 1 - e, highway: highway)
    }

    static func flat(_ v: Double) -> SegmentTerms { split(drive: v, scenery: v) }

    @Test("every one of the ten unit terms is refused out of range, not just the four with a fixture")
    func everyUnitTermIsValidated() {
        #expect(Self.unitTermPaths.count == 10,
                "a term added to SegmentTerms needs a line here as well as in unitTerms")

        // Each probe is chosen so the score would be a finite, plausible number if the term escaped
        // validation - the failure this file exists to make visible is a wrong answer, not a crash.
        for (name, path) in Self.unitTermPaths {
            for bad in [1.5, -0.1, Double.nan, .infinity, -.infinity] {
                var t = Self.flat(0.5)
                t[keyPath: path] = bad
                #expect(SegmentScore.score(for: t) == nil, "\(name) = \(bad) must be refused, not scored")
            }
        }
    }

    @Test("the 0...1 window is pinned on both edges, at the last representable step either side")
    func validationWindowIsExactlyZeroToOne() {
        // The suite next door probes 1.5 and -0.1, which are so far outside that the window could be widened
        // to 0...1.25 - accepting a curvature of 1.2 - with every test still green. These probes are one
        // Double away from the edge, so the window cannot move at all in either direction.
        for (name, path) in Self.unitTermPaths {
            var top = Self.flat(0.5)
            top[keyPath: path] = 1.0
            #expect(SegmentScore.score(for: top) != nil, "\(name) = 1.0 is inside the window")

            var overTop = Self.flat(0.5)
            overTop[keyPath: path] = (1.0).nextUp
            #expect(SegmentScore.score(for: overTop) == nil, "\(name) = \((1.0).nextUp) is outside it")

            var bottom = Self.flat(0.5)
            bottom[keyPath: path] = 0.0
            #expect(SegmentScore.score(for: bottom) != nil, "\(name) = 0.0 is inside the window")

            var underBottom = Self.flat(0.5)
            underBottom[keyPath: path] = (0.0).nextDown
            #expect(SegmentScore.score(for: underBottom) == nil, "\(name) = \((0.0).nextDown) is outside it")
        }
    }

    @Test("tunnel length is validated by its own rule: finite and not negative, with no upper bound")
    func tunnelLengthIsValidated() throws {
        for bad in [-1.0, Double.nan, .infinity, -.infinity] {
            var t = Self.flat(0.5)
            t.tunnelMeters = bad
            #expect(SegmentScore.score(for: t) == nil, "tunnelMeters = \(bad) must be refused")
        }

        // A very long tunnel is a real road and must be PENALISED rather than refused - otherwise the
        // isFinite guard could be "fixed" into an upper bound and lose every alpine route.
        var long = Self.flat(0.5)
        long.tunnelMeters = 10_000
        #expect(abs(try #require(SegmentScore.score(for: long)) - 0.5 * 0.15) < 1e-12)
    }

    @Test("motorway distance is validated by a different rule: infinity is legal and means no motorway near")
    func motorwayDistanceIsValidated() throws {
        for bad in [-1.0, -.infinity, Double.nan] {
            var t = Self.flat(0.5)
            t.metersToNearestMotorway = bad
            #expect(SegmentScore.score(for: t) == nil, "metersToNearestMotorway = \(bad) must be refused")
        }

        // The two guards differ on purpose and the difference is load-bearing: `.infinity` is this field's
        // DEFAULT and means "no motorway anywhere near", while an infinite tunnel is a broken measurement.
        // A negative distance would otherwise apply the x0.7 penalty and a NaN would silently skip it.
        var none = Self.flat(0.5)
        none.metersToNearestMotorway = .infinity
        #expect(abs(try #require(SegmentScore.score(for: none)) - 0.5) < 1e-12)

        var near = Self.flat(0.5)
        near.metersToNearestMotorway = 0
        #expect(abs(try #require(SegmentScore.score(for: near)) - 0.5 * 0.7) < 1e-12)
    }

    @Test("a score that is returned at all lands in 0...1, across every combination that can move it")
    func scoreAlwaysLandsInZeroToOne() throws {
        // The brief asks for "output always in 0...1" and nothing asserted it in general: the top was pinned
        // at a single point by the byway cap and the bottom at a single point by a zero axis, and a range
        // claim is about every point. The 0 and the 1 here are the invariant itself, written as literals -
        // not read back from anything the formula computes, which would hold for any range.
        let levels = [0.0, 0.001, 0.25, 0.5, 0.75, 0.999, 1.0]
        let tunnels = [0.0, 300.0, 301.0, 10_000.0]
        let distances = [0.0, 149.0, 150.0, Double.infinity]
        let classes = ["tertiary", "residential", "unclassified", "motorway", "trunk_link", "secondary"]
        var walked = 0
        for m in levels {
            for e in levels {
                for byway in [false, true] {
                    for tunnel in tunnels {
                        for distance in distances {
                            for highway in classes {
                                var t = Self.split(drive: m, scenery: e, highway: highway)
                                t.isByway = byway
                                t.tunnelMeters = tunnel
                                t.metersToNearestMotorway = distance
                                let at = "m=\(m) e=\(e) byway=\(byway) tunnel=\(tunnel)"
                                    + " motorway=\(distance) highway=\(highway)"
                                let score = try #require(SegmentScore.score(for: t),
                                                         "every input in this grid is legal: \(at)")
                                #expect(score >= 0 && score <= 1, "\(at) scored \(score)")
                                walked += 1
                            }
                        }
                    }
                }
            }
        }
        // Without this the loops could be emptied - by a fixture list going to [] - and the test would pass
        // having asserted nothing. The count is the product of the literal list lengths above.
        #expect(walked == 7 * 7 * 2 * 4 * 4 * 6, "the grid must actually have been walked; walked \(walked)")
    }
}

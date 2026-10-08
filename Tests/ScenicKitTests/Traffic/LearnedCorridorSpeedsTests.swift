import Foundation
import Testing
@testable import ScenicKit

/// T-0320: the on-device corridor learner through its two shipping calls, record and retime, each answer compared
/// WHOLE (the whole slot table, the whole RetimedRoute) to a value written out per row.
@Suite("learned corridor speeds (T-0320)") struct LearnedCorridorSpeedsTests {
    static let utc = TimeZone(secondsFromGMT: 0)!
    static let cellA = CorridorCell(index: 0x0882_8308_2bff_ffff)
    static let cellB = CorridorCell(index: 0x0882_8308_2dff_ffff)
    /// Monday 2026-10-05 08:00:00Z, hour of the week 8.
    static let monday8 = Date(timeIntervalSince1970: 1_791_187_200)
    static let hour8 = HourOfWeek(8)!

    static func taught(_ times: Int, _ cell: CorridorCell, _ hour: HourOfWeek, actual: Double, freeFlow: Double,
                       into speeds: inout LearnedCorridorSpeeds) {
        for _ in 0..<times {
            let accepted = speeds.record(cell: cell, hourOfWeek: hour, actualSeconds: actual, freeFlowSeconds: freeFlow)
            #expect(accepted)
        }
    }

    /// P-SAFE-07: the badge is on through 4 samples and off at 5 exactly, crossed with the route's other edge
    /// learned or not - the row's answer is a function of both.
    @Test("the estimate badge: on at 0 and 4 samples, off at 5 and 6, and on whenever another edge is unlearned")
    func badgeAtFiveSamples() {
        for otherLearned in [true, false] {
            for (n, edgeA, estimate) in [(0, 60.0, true), (4, 60.0, true), (5, 120.0, false), (6, 120.0, false)] {
                var speeds = LearnedCorridorSpeeds(timeZone: Self.utc)
                Self.taught(n, Self.cellA, Self.hour8, actual: 120, freeFlow: 60, into: &speeds)
                Self.taught(otherLearned ? 5 : 4, Self.cellB, Self.hour8, actual: 100, freeFlow: 75, into: &speeds)
                let edges = [CorridorEdge(cell: Self.cellA, freeFlowSeconds: 60),
                             CorridorEdge(cell: Self.cellB, freeFlowSeconds: 1)]
                // edge B: 1 s at ratio 0.75 is 4/3 s - entered within hour 8 either way.
                let edgeB = otherLearned ? 1.0 / 0.75 : 1.0
                let expected = RetimedRoute(edgeSeconds: [edgeA, edgeB], isEstimate: estimate || !otherLearned)
                #expect(speeds.retime(edges, departsAt: Self.monday8) == expected, "n=\(n) other=\(otherLearned)")
            }
        }
    }

    @Test("an empty route is an estimate with no edges")
    func emptyRouteIsAnEstimate() {
        var speeds = LearnedCorridorSpeeds(timeZone: Self.utc)
        Self.taught(5, Self.cellA, Self.hour8, actual: 120, freeFlow: 60, into: &speeds)
        #expect(speeds.retime([], departsAt: Self.monday8) == RetimedRoute(edgeSeconds: [], isEstimate: true))
    }

    /// R3: alpha 0.25; the first sample seeds the ratio, the second weighs 1/4.
    @Test("the EWMA: the first sample seeds the ratio, the second moves it by alpha 0.25")
    func ewmaFirstAndSecondUpdate() {
        var speeds = LearnedCorridorSpeeds(timeZone: Self.utc)
        let slot = CorridorSlot(cell: Self.cellA, hour: Self.hour8)
        let first = speeds.record(cell: Self.cellA, hourOfWeek: Self.hour8, actualSeconds: 120, freeFlowSeconds: 60)
        #expect(first)
        #expect(speeds.slots == [slot: CorridorRatio(ratio: 0.5, samples: 1)])
        let second = speeds.record(cell: Self.cellA, hourOfWeek: Self.hour8, actualSeconds: 60, freeFlowSeconds: 60)
        #expect(second)
        #expect(speeds.slots == [slot: CorridorRatio(ratio: 0.625, samples: 2)])
    }

    /// R2: each observation clamped to [0.3, 1.0], both bounds with their neighbours on either side.
    @Test("the ratio clamp at 0.3 and 1.0, one ulp either side of each bound")
    func ratioClampBounds() {
        let rows: [(observed: Double, kept: Double)] = [
            (0.3.nextDown, 0.3), (0.3, 0.3), (0.3.nextUp, 0.3.nextUp),
            (1.0.nextDown, 1.0.nextDown), (1.0, 1.0), (1.0.nextUp, 1.0),
            (Double.leastNonzeroMagnitude, 0.3), (Double.greatestFiniteMagnitude, 1.0)]
        for row in rows {
            var speeds = LearnedCorridorSpeeds(timeZone: Self.utc)
            let accepted = speeds.record(cell: Self.cellA, hourOfWeek: Self.hour8, actualSeconds: 1,
                                         freeFlowSeconds: row.observed)
            #expect(accepted, "observed \(row.observed)")
            #expect(speeds.slots == [CorridorSlot(cell: Self.cellA, hour: Self.hour8):
                                        CorridorRatio(ratio: row.kept, samples: 1)], "observed \(row.observed)")
        }
    }

    /// R4: every bad value in either position, over an empty and a holding store - refused, the store unchanged.
    @Test("NaN, infinite, zero and negative times are refused and change nothing")
    func badTimesRefused() {
        let bad: [Double] = [.nan, .infinity, -.infinity, 0, -0.0, -1, -Double.leastNonzeroMagnitude]
        var holding = LearnedCorridorSpeeds(timeZone: Self.utc)
        Self.taught(3, Self.cellA, Self.hour8, actual: 120, freeFlow: 60, into: &holding)
        for before in [LearnedCorridorSpeeds(timeZone: Self.utc), holding] {
            for value in bad {
                for (actual, freeFlow) in [(value, 60.0), (60.0, value), (value, value)] {
                    var speeds = before
                    let accepted = speeds.record(cell: Self.cellA, hourOfWeek: Self.hour8, actualSeconds: actual,
                                                 freeFlowSeconds: freeFlow)
                    #expect(!accepted, "actual \(actual) freeFlow \(freeFlow)")
                    #expect(speeds == before, "actual \(actual) freeFlow \(freeFlow)")
                }
            }
        }
    }

    /// R6: each edge reads the hour it is ENTERED, after the earlier edges' re-timed seconds; Sunday 23 wraps to
    /// Monday 0. Departing 23:58:30, free-flow would enter edge B at 23:59:30 (hour 167, decoy ratio 0.5) while
    /// the re-timed 120 s enter it at 00:00:30 Monday (hour 0, ratio 0.75).
    @Test("departsAt: an edge entered after Sunday 23:59 reads Monday 00:00's ratio, and the hour shifts the ratio")
    func hourBoundaryMidRoute() {
        var speeds = LearnedCorridorSpeeds(timeZone: Self.utc)
        let sunday23 = HourOfWeek(167)!, monday0 = HourOfWeek(0)!
        Self.taught(5, Self.cellA, sunday23, actual: 120, freeFlow: 60, into: &speeds)
        Self.taught(5, Self.cellB, sunday23, actual: 120, freeFlow: 60, into: &speeds)
        Self.taught(5, Self.cellB, monday0, actual: 100, freeFlow: 75, into: &speeds)
        let edges = [CorridorEdge(cell: Self.cellA, freeFlowSeconds: 60),
                     CorridorEdge(cell: Self.cellB, freeFlowSeconds: 60)]
        let departs = Date(timeIntervalSince1970: 1_791_763_110)
        #expect(speeds.retime(edges, departsAt: departs) == RetimedRoute(edgeSeconds: [120, 80], isEstimate: false))
        #expect(speeds.retime(edges, departsAt: departs).etaSeconds == 200)
        // The same edge A one week-hour earlier (Sunday 22:58:30) is unlearned: free-flow and the badge.
        #expect(speeds.retime(Array(edges.prefix(1)), departsAt: departs.addingTimeInterval(-3600))
                == RetimedRoute(edgeSeconds: [60], isEstimate: true))
    }
}

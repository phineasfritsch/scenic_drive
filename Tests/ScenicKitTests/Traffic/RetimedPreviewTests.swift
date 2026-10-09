import Foundation
import Testing
@testable import ScenicKit

/// T-0325 R4/R5: the preview's ETA and badge from retime, previews compared WHOLE to a value written out per row.
@Suite("the preview's ETA and badge come from retime (T-0325)") struct RetimedPreviewTests {
    static let utc = TimeZone(secondsFromGMT: 0)!
    static let v = CorridorRouteTests.v
    static let c = CorridorRouteTests.c
    static let runs = CorridorRouteTests.runs
    /// Edge 0 is entered in hour 8, the others in hour 9, whether retimed at free flow or at ratio 0.5.
    static let departs = CorridorClockTests.start
    static let hours = [8, 9, 9, 9]
    static let freeFlow = [80.0, 90, 40, 100]

    /// The server's preview: its ETA, the badge, and every other field set so a dropped one shows.
    static let server = PlanPreview(route: v, etaSeconds: 333, fastestEtaSeconds: 250, etaIsEstimate: true,
                                    hazards: [PlanHazardRun(kind: "surface", value: "gravel", fromIndex: 1, toIndex: 2)],
                                    waypoints: [v[2]], lambda: 1.5,
                                    continuation: PlanContinuation(token: "t0325", place: 42, budgetMinutes: 30))

    static func expected(eta: Double, estimate: Bool) -> PlanPreview {
        PlanPreview(route: server.route, etaSeconds: eta, fastestEtaSeconds: 250, etaIsEstimate: estimate,
                    hazards: server.hazards, waypoints: server.waypoints, lambda: 1.5, continuation: server.continuation)
    }

    /// Every edge taught `samples` times at ratio 0.5 (actual = 2 x free flow), edge 2 only 4 times when `oneShort`.
    static func learner(samples: Int, oneShort: Bool) -> LearnedCorridorSpeeds {
        var speeds = LearnedCorridorSpeeds(timeZone: utc)
        for edge in 0..<4 {
            let times = oneShort && edge == 2 ? min(samples, 4) : samples
            for _ in 0..<times {
                speeds.record(cell: c[edge], hourOfWeek: HourOfWeek(hours[edge])!,
                              actualSeconds: 2 * freeFlow[edge], freeFlowSeconds: freeFlow[edge])
            }
        }
        return speeds
    }

    /// P-SAFE-07: the badge goes only when every edge has 5 samples; no runs leaves the server's preview.
    @Test("the badge: on at 0 and 4 samples, off at 5 and 6, on with one edge unlearned, and kept without runs")
    func badgeTable() {
        let rows: [(Int, Bool, Bool, PlanPreview)] = [
            (0, false, true, Self.expected(eta: 310, estimate: true)),
            (4, false, true, Self.expected(eta: 310, estimate: true)),
            (5, false, true, Self.expected(eta: 620, estimate: false)),
            (6, false, true, Self.expected(eta: 620, estimate: false)),
            (0, true, true, Self.expected(eta: 310, estimate: true)),
            (4, true, true, Self.expected(eta: 310, estimate: true)),
            (5, true, true, Self.expected(eta: 580, estimate: true)),
            (6, true, true, Self.expected(eta: 580, estimate: true)),
            (0, false, false, Self.server), (6, false, false, Self.server), (6, true, false, Self.server),
        ]
        for (samples, oneShort, withRuns, preview) in rows {
            let answer = RetimedPreview.of(Self.server, timeRuns: withRuns ? Self.runs : [],
                                           by: Self.learner(samples: samples, oneShort: oneShort),
                                           departsAt: Self.departs)
            #expect(answer == preview, "\(samples) samples, oneShort \(oneShort), runs \(withRuns)")
        }
        // Runs that do not tile the drawn line are no runs.
        let bad = [CorridorTimeRun(from: 0, to: 3, milliseconds: 1000)]
        #expect(RetimedPreview.of(Self.server, timeRuns: bad, by: Self.learner(samples: 6, oneShort: false),
                                  departsAt: Self.departs) == Self.server)
    }

    /// The M7 exit on the Linux path: drives through DriveSession and CorridorClock clear the badge at the fifth.
    @Test("five completed drives clear the badge and four do not")
    func fiveDrivesClearTheBadge() {
        var speeds = LearnedCorridorSpeeds(timeZone: Self.utc)
        var oracle = LearnedCorridorSpeeds(timeZone: Self.utc)
        let clean = [CorridorClockTests.f0, CorridorClockTests.f1, CorridorClockTests.f2, CorridorClockTests.f3,
                     CorridorClockTests.arrive]
        let actual = [100.0, 150, 50, 100]
        for drive in 1...5 {
            speeds = CorridorClockTests.drive(clean, into: speeds)
            for edge in 0..<4 {
                oracle.record(cell: Self.c[edge], hourOfWeek: HourOfWeek(Self.hours[edge])!,
                              actualSeconds: actual[edge], freeFlowSeconds: Self.freeFlow[edge])
            }
            #expect(speeds == oracle, "drive \(drive)")
            let answer = RetimedPreview.of(Self.server, timeRuns: Self.runs, by: speeds, departsAt: Self.departs)
            let learnedEta = (0..<4).map { Self.freeFlow[$0] / oracle.slots[CorridorSlot(
                cell: Self.c[$0], hour: HourOfWeek(Self.hours[$0])!)]!.ratio }.reduce(0, +)
            #expect(answer == Self.expected(eta: drive < 5 ? 310 : learnedEta, estimate: drive < 5),
                    "drive \(drive)")
        }
    }
}

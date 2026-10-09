import Foundation
import Testing
@testable import ScenicKit

/// T-0343 R1/R5: the drive's feed through the shipped CorridorLearner.observe - the controller first, the clock on
/// its session at the fix's date, a save of the whole table exactly when an edge was taught - and the M7 exit with a
/// relaunch between drives: the next launch restores the last saved rows and the planner's preview reads them.
@Suite("the drive teaches the device's learner and the next launch keeps it (T-0343)") struct CorridorLearnerTests {
    static let utc = TimeZone(secondsFromGMT: 0)!
    static let runs = CorridorRouteTests.runs
    /// The server's preview of the clock tests' route, with its time runs; every other field set so a dropped one shows.
    static let server = PlanPreview(route: CorridorRouteTests.v, etaSeconds: 333, fastestEtaSeconds: 250,
                                    etaIsEstimate: true, hazards: RetimedPreviewTests.server.hazards, lambda: 1.5,
                                    continuation: RetimedPreviewTests.server.continuation, timeRuns: runs)
    static let clean = [CorridorClockTests.f0, CorridorClockTests.f1, CorridorClockTests.f2, CorridorClockTests.f3,
                        CorridorClockTests.arrive]

    @MainActor final class Saves {
        var rows: [[CorridorSlotRow]] = []
    }

    /// Drives `steps` (fixes only) on `preview` through a learner over `speeds`; per fix, the commands must equal a
    /// bare controller's fed the same DriveFix, and the controllers must stay equal. Answers every save.
    @MainActor
    static func drive(_ steps: [CorridorClockTests.Step], on preview: PlanPreview,
                      from speeds: LearnedCorridorSpeeds) -> (saves: [[CorridorSlotRow]], learner: CorridorLearner) {
        let saves = Saves()
        let learner = CorridorLearner(speeds: speeds, save: { saves.rows.append($0) })
        guard let session = DriveSession(preview: preview, online: false) else {
            Issue.record("the preview is not drivable")
            return ([], learner)
        }
        var controller = DriveController(session: session)
        var bare = DriveController(session: session)
        var clock = learner.clock(for: preview)
        for step in steps {
            guard case let .fix(at, t) = step else { continue }
            let date = CorridorClockTests.start.addingTimeInterval(t)
            let commands = learner.observe(coordinate: at, speedMetersPerSecond: 20, at: date, on: &controller,
                                           clock: &clock)
            let expected = bare.observe(DriveFix(coordinate: at, speedMetersPerSecond: 20,
                                                 timestamp: date.timeIntervalSinceReferenceDate))
            #expect(commands == expected && controller == bare, "fix at \(t)")
        }
        return (saves.rows, learner)
    }

    @Test("each fix teaches through the shipped entry: a save of the whole table exactly when an edge completes")
    @MainActor
    func feedTable() {
        let noRuns = PlanPreview(route: Self.server.route, etaSeconds: 333, fastestEtaSeconds: 250, etaIsEstimate: true,
                                 hazards: [])
        let untiled = PlanPreview(route: Self.server.route, etaSeconds: 333, fastestEtaSeconds: 250,
                                  etaIsEstimate: true, hazards: [],
                                  timeRuns: [CorridorTimeRun(from: 0, to: 3, milliseconds: 1000)])
        let skip = [CorridorClockTests.f0, CorridorClockTests.f1, CorridorClockTests.f3, CorridorClockTests.arrive]
        // (name, preview, steps, the edges each save holds, in order)
        let rows: [(String, PlanPreview, [CorridorClockTests.Step], [[Int]])] = [
            ("clean", Self.server, Self.clean, [[0], [0, 1], [0, 1, 2], [0, 1, 2, 3]]),
            ("edge 2 skipped", Self.server, skip, [[0]]),
            ("no runs", noRuns, Self.clean, []),
            ("runs that do not tile the line", untiled, Self.clean, []),
        ]
        for (name, preview, steps, edges) in rows {
            let (saves, learner) = Self.drive(steps, on: preview, from: LearnedCorridorSpeeds(timeZone: Self.utc))
            #expect(saves.map { LearnedCorridorSpeeds(timeZone: Self.utc, restoring: $0)?.slots }
                    == edges.map(CorridorClockTests.slots), "\(name)")
            #expect(saves.last ?? [] == learner.speeds.rows, "\(name): the last save is the learner's whole table")
            #expect(learner.speeds.slots == CorridorClockTests.slots(edges.last ?? []), "\(name)")
        }
        // Meta: the table has a row that saves and a row that never does.
        #expect(Set(rows.map { $0.3.isEmpty }) == [true, false])
    }

    struct Fixed: RoutePlanning {
        let outcome: PlanOutcome
        func plan(_ ticket: PlanTicket) async -> PlanOutcome { outcome }
    }

    static let ticket = PlanTicket(serial: 1, origin: Coordinate(latitude: 34.05, longitude: -118.25), place: 42,
                                   budgetMinutes: 30)

    static let la = TimeZone(identifier: "America/Los_Angeles")!
    /// (zone, the hour each edge is entered in at the drive's departure 2026-10-05T08:59Z): rows are f(zone) - in Los
    /// Angeles the same instant is 01:59 PDT, so the clock teaches and the planner reads hours 1 and 2 (rv1-t0343 B2).
    static let zoned: [(String, TimeZone, [Int])] = [("UTC", utc, RetimedPreviewTests.hours),
                                                      ("Los Angeles", la, [1, 2, 2, 2])]

    @Test("five drives, each followed by a relaunch, clear the planner's badge on the fifth and not before")
    @MainActor
    func fiveDrivesAcrossRelaunch() async {
        var last: [String: [CorridorSlotRow]] = [:]
        for (name, zone, hours) in Self.zoned {
            last[name] = await Self.fiveDrives(zone, hours: hours, name: name)
        }
        // Meta: the zone is read. Los Angeles's kept rows relaunched in UTC answer the badge at the same departure.
        let laRows = last["Los Angeles"] ?? []
        let misread = CorridorLearner(speeds: LearnedCorridorSpeeds(timeZone: Self.utc, restoring: laRows)
                                      ?? LearnedCorridorSpeeds(timeZone: Self.utc), save: { _ in })
        let planner = RetimingPlanner(inner: Fixed(outcome: .preview(Self.server)), learner: misread,
                                      now: { RetimedPreviewTests.departs })
        #expect(await planner.plan(Self.ticket) == .preview(Self.expected(eta: 310, estimate: true)))
        #expect(last["UTC"] != last["Los Angeles"] && last["UTC"]?.isEmpty == false)
    }

    static func expected(eta: Double, estimate: Bool) -> PlanPreview {
        PlanPreview(route: server.route, etaSeconds: eta, fastestEtaSeconds: 250, etaIsEstimate: estimate,
                    hazards: server.hazards, lambda: 1.5, continuation: server.continuation, timeRuns: runs)
    }

    /// Five drives in `zone`, a relaunch from the saved rows after each; answers the rows the fifth drive saved.
    @MainActor
    static func fiveDrives(_ zone: TimeZone, hours: [Int], name: String) async -> [CorridorSlotRow] {
        var kept: [CorridorSlotRow] = []
        var oracle = LearnedCorridorSpeeds(timeZone: zone)
        let actual = [100.0, 150, 50, 100]
        for drive in 1...5 {
            // A relaunch: the learner is rebuilt from what the last launch saved, and nothing else.
            guard let restored = LearnedCorridorSpeeds(timeZone: zone, restoring: kept) else {
                Issue.record("\(name) drive \(drive): the kept rows are refused")
                return []
            }
            kept = Self.drive(clean, on: server, from: restored).saves.last ?? []
            for edge in 0..<4 {
                oracle.record(cell: CorridorRouteTests.c[edge], hourOfWeek: HourOfWeek(hours[edge])!,
                              actualSeconds: actual[edge], freeFlowSeconds: RetimedPreviewTests.freeFlow[edge])
            }
            let relaunched = CorridorLearner(speeds: LearnedCorridorSpeeds(timeZone: zone, restoring: kept)
                                             ?? LearnedCorridorSpeeds(timeZone: zone), save: { _ in })
            #expect(relaunched.speeds == oracle, "\(name) drive \(drive)")
            let planner = RetimingPlanner(inner: Fixed(outcome: .preview(server)), learner: relaunched,
                                          now: { RetimedPreviewTests.departs })
            let learnedEta = (0..<4).map { RetimedPreviewTests.freeFlow[$0] / oracle.slots[CorridorSlot(
                cell: CorridorRouteTests.c[$0], hour: HourOfWeek(hours[$0])!)]!.ratio }.reduce(0, +)
            #expect(await planner.plan(ticket) == .preview(expected(eta: drive < 5 ? 310 : learnedEta,
                                                                    estimate: drive < 5)), "\(name) drive \(drive)")
        }
        return kept
    }
}

@testable import ScenicKit
import Testing

/// T-0324 R2 (P-SAFE-09): what the drive screen shows for every DriveSurface x DriveMode, compared WHOLE against a
/// literal table, and through the session the navigator publishes from.
@Suite("DriveDisplayTests")
struct DriveDisplayTests {
    typealias Row = (surface: DriveSurface, mode: DriveMode, display: DriveDisplay)

    static func shown(_ title: String, _ height: Double, _ status: String?, _ details: Bool) -> DriveDisplay {
        DriveDisplay(actionTitle: title, actionMinHeight: height, status: status, showsDetails: details)
    }

    /// Typed, never derived from the type under test: one row per pair, each a function of BOTH inputs.
    static let table: [Row] = [
        (.minimal, .guiding, shown("End", 60, nil, false)),
        (.minimal, .rerouting, shown("End", 60, "Finding a new way", false)),
        (.minimal, .rejoining, shown("End", 60, "Head back to your route", false)),
        (.full, .guiding, shown("End", 44, nil, true)),
        (.full, .rerouting, shown("End", 44, "You left the route. Finding a new way.", true)),
        (.full, .rejoining, shown("End", 44, "You left the route and are offline. Head back to it.", true)),
    ]

    static let line = [DriveFixtures.probeStart, DriveFixtures.probeEnd]
    static let onLine = Coordinate(latitude: 0, longitude: 0.005)
    static let away = Coordinate(latitude: 0.002, longitude: 0.005)

    static func expected(_ surface: DriveSurface, _ mode: DriveMode) -> DriveDisplay? {
        table.first { $0.surface == surface && $0.mode == mode }?.display
    }

    @Test("P-SAFE-09: the drive screen shows the typed display for every surface and mode, compared whole")
    func everySurfaceAndMode() {
        #expect(DriveSurface.allCases.count == 2 && DriveMode.allCases.count == 3)
        for surface in DriveSurface.allCases {
            for mode in DriveMode.allCases {
                #expect(DriveDisplay(surface: surface, mode: mode) == Self.expected(surface, mode),
                        "\(surface) \(mode)")
            }
        }
    }

    @Test("P-SAFE-09: the table covers each pair once and no row ignores either input")
    func tableIsTheCrossProduct() {
        let pairs = Self.table.map { "\($0.surface) \($0.mode)" }
        #expect(Set(pairs).count == 6 && pairs.count == 6)
        for row in Self.table {
            let other = row.surface == .full ? DriveSurface.minimal : .full
            #expect(Self.expected(other, row.mode) != row.display)
            for mode in DriveMode.allCases where mode != row.mode {
                #expect(Self.expected(row.surface, mode) != row.display)
            }
        }
    }

    @Test("P-SAFE-09: moving shows only the one large action - 60 pt, no details - in every mode")
    func minimalIsTheOneLargeAction() {
        for mode in DriveMode.allCases {
            let shown = DriveDisplay(surface: .minimal, mode: mode)
            #expect(shown.actionMinHeight >= 60 && !shown.showsDetails)
        }
    }

    @Test("P-SAFE-09: the session's display is the table's row for its own surface and mode, before and after fixes")
    func sessionDisplayFollowsTheSession() {
        var guiding = DriveSession(line: Self.line, waypoints: [], lambda: 0.5, online: true)!
        #expect(DriveDisplay(session: guiding) == Self.expected(.minimal, .guiding)?.drawing(Self.line))
        _ = guiding.observe(DriveFixtures.fix(Self.onLine, at: 0, speed: 2))
        #expect(DriveDisplay(session: guiding) == Self.expected(.full, .guiding)?.drawing(Self.line))

        var rejoining = DriveSession(line: Self.line, waypoints: [], lambda: 0.5, online: false)!
        for t in 0...5 { _ = rejoining.observe(DriveFixtures.fix(Self.away, at: Double(t))) }
        #expect(DriveDisplay(session: rejoining) == Self.expected(.minimal, .rejoining)?.drawing(Self.line))
        _ = rejoining.observe(DriveFixtures.fix(Self.away, at: 6, speed: 4.5))
        #expect(DriveDisplay(session: rejoining) == Self.expected(.full, .rejoining)?.drawing(Self.line))

        var rerouting = DriveSession(line: Self.line, waypoints: [], lambda: 0.5, online: true)!
        for t in 0...5 { _ = rerouting.observe(DriveFixtures.fix(Self.away, at: Double(t))) }
        #expect(DriveDisplay(session: rerouting) == Self.expected(.minimal, .rerouting)?.drawing(Self.line))
        _ = rerouting.observe(DriveFixtures.fix(Self.away, at: 6, speed: 0))
        #expect(DriveDisplay(session: rerouting) == Self.expected(.full, .rerouting)?.drawing(Self.line))
    }

    /// T-0397 R2: typed rows - each bound of the minute rounding and of the tenths/whole-miles switch.
    static let glanceRows: [(seconds: Double, meters: Double, line: String)] = [
        (0, 0, "0 min · 0.0 mi"),
        (89, 1_609.344, "1 min · 1.0 mi"),
        (90, 1_609.344, "2 min · 1.0 mi"),
        (1_500, 160.9344 * 99.4, "25 min · 9.9 mi"),
        (1_500, 160.9344 * 99.5, "25 min · 10 mi"),
        (1_500, 16_093.44, "25 min · 10 mi"),
        (1_500, 160.9344 * 104.9, "25 min · 10 mi"),
        (1_500, 160.9344 * 105, "25 min · 11 mi"),
    ]

    @Test("T-0397 R2: the glance line is whole minutes and tenths of a mile under 10 mi, whole miles from 10")
    func glanceLineBounds() {
        for row in Self.glanceRows {
            #expect(DriveDisplay(surface: .minimal, mode: .guiding, remainingSeconds: row.seconds,
                                 remainingMeters: row.meters).glanceLine == row.line, "\(row)")
        }
    }

    /// Two equal 0.01-degree segments on the equator: 2 x 1111.95 m = 1.38 mi; 1200 s for the whole line.
    static let twoSegments = [Coordinate(latitude: 0, longitude: 0), Coordinate(latitude: 0, longitude: 0.01),
                              Coordinate(latitude: 0, longitude: 0.02)]

    @Test("T-0397 R2: the session's glance is its line's ETA and metres left past the progress vertex, pro rata")
    func sessionGlanceIsWhatIsLeft() {
        var session = DriveSession(line: Self.twoSegments, waypoints: [], lambda: 0.5, online: true,
                                   etaSeconds: 1_200, fastestEtaSeconds: 1_000)!
        let start = DriveDisplay(session: session)
        #expect(start.glanceLine == "20 min · 1.4 mi" && start.remainingSeconds == 1_200)
        _ = session.observe(DriveFixtures.fix(Coordinate(latitude: 0, longitude: 0.005), at: 0))
        #expect(DriveDisplay(session: session).glanceLine == "20 min · 1.4 mi")
        _ = session.observe(DriveFixtures.fix(Coordinate(latitude: 0, longitude: 0.015), at: 1))
        let half = DriveDisplay(session: session)
        #expect(half.glanceLine == "10 min · 0.7 mi" && abs(half.remainingSeconds - 600) < 1e-6)
        #expect(half == DriveDisplay(actionTitle: "End", actionMinHeight: 60, status: nil, showsDetails: false,
                                     line: Self.twoSegments, etaLine: "20 min · 3 min longer than the fastest way",
                                     remainingSeconds: half.remainingSeconds, glanceLine: "10 min · 0.7 mi"))
    }
}

extension DriveDisplay {
    /// The same row drawing `line` (T-0328 R4): the session's display carries the session's current line.
    func drawing(_ line: [Coordinate]) -> DriveDisplay {
        DriveDisplay(actionTitle: actionTitle, actionMinHeight: actionMinHeight, status: status,
                     showsDetails: showsDetails, line: line, etaLine: "0 min · about as quick as the fastest way",
                     glanceLine: "0 min · 0.7 mi")
    }
}

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
        (.minimal, .guiding, shown("End drive", 60, nil, false)),
        (.minimal, .rerouting, shown("End drive", 60, "Finding a new way", false)),
        (.minimal, .rejoining, shown("End drive", 60, "Head back to your route", false)),
        (.full, .guiding, shown("End drive", 44, nil, true)),
        (.full, .rerouting, shown("End drive", 44, "You left the route. Finding a new way.", true)),
        (.full, .rejoining, shown("End drive", 44, "You left the route and are offline. Head back to it.", true)),
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
}

extension DriveDisplay {
    /// The same row drawing `line` (T-0328 R4): the session's display carries the session's current line.
    func drawing(_ line: [Coordinate]) -> DriveDisplay {
        DriveDisplay(actionTitle: actionTitle, actionMinHeight: actionMinHeight, status: status,
                     showsDetails: showsDetails, line: line)
    }
}

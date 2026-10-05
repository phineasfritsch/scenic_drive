import Foundation
import Testing
@testable import Telemetry

/// The Workers Analytics Engine encoding of every one of the fourteen events, by EXACT equality of the whole
/// data point (T-0265 R2). The table must cover every TelemetryEventKind, and `kindBySwitch` switches over
/// TelemetryEvent with no `default`, so a fifteenth case does not compile here until it has a row.
@Suite("TelemetryEvent encoding") struct TelemetryEventEncodingTests {
    /// Two published cells (rand05centers.txt rows 1 and 2) made from their INDEX, so this table measures
    /// the encoder alone: the H3 port is H3ReferenceCellTests' subject, and a broken port must not crash or
    /// redden this suite's static rows.
    static let origin = H3Cell(index: 0x0850_DAB6_3FFF_FFFF)
    static let otherOrigin = H3Cell(index: 0x0850_336B_7FFF_FFFF)

    static func point(_ name: String, _ label: String = "", _ cell: String = "", _ value1: Double = 0,
                      _ value2: Double = 0) -> TelemetryDataPoint {
        TelemetryDataPoint(indexes: [name], blobs: [name, label, cell], doubles: [value1, value2])
    }

    static let rows: [(event: TelemetryEvent, expected: TelemetryDataPoint)] = [
        (.planRequested(feature: .scenic, budgetMinutes: 25, origin: origin),
         point("plan_requested", "scenic", "850dab63fffffff", 25)),
        (.planRequested(feature: .roadTrip, budgetMinutes: 120, origin: otherOrigin),
         point("plan_requested", "road_trip", "850336b7fffffff", 120)),
        (.planResult(.noAlternative), point("plan_result", "no_alternative")),
        (.previewShown, point("preview_shown")),
        (.handoffTapped(.appleMaps), point("handoff_tapped", "apple_maps")),
        (.driveStarted, point("drive_started")),
        (.driveCompleted(CompletionPercent(fraction: 0.987), deviations: 2), point("drive_completed", "", "", 98, 2)),
        (.driveAbandoned(CompletionPercent(fraction: 0.375)), point("drive_abandoned", "", "", 37)),
        (.postDriveAnswer(prettier: true), point("post_drive_answer", "prettier")),
        (.postDriveAnswer(prettier: false), point("post_drive_answer", "not_prettier")),
        (.surpriseShown, point("surprise_shown")),
        (.surpriseNotThis(.beenThere), point("surprise_not_this", "been_there")),
        (.surpriseTakeMeThere, point("surprise_take_me_there")),
        (.surpriseArrived, point("surprise_arrived")),
        (.corpusActivated(version: 7), point("corpus_activated", "", "", 7)),
        (.paywall(.shown), point("paywall_shown")),
        (.paywall(.converted), point("paywall_converted")),
    ]

    /// An independent event -> kind map. No `default`: a new TelemetryEvent case is a compile failure here.
    static func kindBySwitch(_ event: TelemetryEvent) -> TelemetryEventKind {
        switch event {
        case .planRequested: return .planRequested
        case .planResult: return .planResult
        case .previewShown: return .previewShown
        case .handoffTapped: return .handoffTapped
        case .driveStarted: return .driveStarted
        case .driveCompleted: return .driveCompleted
        case .driveAbandoned: return .driveAbandoned
        case .postDriveAnswer: return .postDriveAnswer
        case .surpriseShown: return .surpriseShown
        case .surpriseNotThis: return .surpriseNotThis
        case .surpriseTakeMeThere: return .surpriseTakeMeThere
        case .surpriseArrived: return .surpriseArrived
        case .corpusActivated: return .corpusActivated
        case .paywall: return .paywall
        }
    }

    @Test("the plan's fourteen events, no more and no fewer, each with a row")
    func fourteenEventsEachWithARow() {
        #expect(TelemetryEventKind.allCases.count == 14)
        #expect(Set(Self.rows.map { $0.event.kind }) == Set(TelemetryEventKind.allCases))
        #expect(Self.rows.map { $0.event.kind } == Self.rows.map { Self.kindBySwitch($0.event) })
    }

    @Test("every event encodes to its whole Analytics Engine data point by exact equality")
    func everyEventEncodesExactly() {
        for row in Self.rows {
            #expect(row.event.dataPoint == row.expected, "\(row.event)")
        }
    }

    @Test("the data point serializes to exactly writeDataPoint's three keys")
    func dataPointJSON() throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let json = try encoder.encode(Self.rows[0].event.dataPoint)
        #expect(String(decoding: json, as: UTF8.self)
            == #"{"blobs":["plan_requested","scenic","850dab63fffffff"],"doubles":[25,0],"indexes":["plan_requested"]}"#)
    }

    /// writeDataPoint's JSON rebuilt by hand from the EXPECTED point: every blob quoted in its slot (an empty
    /// label or cell is still a "" slot - R2's fixed width) and every double written as its whole number.
    static func json(_ point: TelemetryDataPoint) -> String {
        let quoted: ([String]) -> String = { items in items.map { "\"" + $0 + "\"" }.joined(separator: ",") }
        let numbers = point.doubles.map { String(Int($0)) }.joined(separator: ",")
        return #"{"blobs":["# + quoted(point.blobs) + #"],"doubles":["# + numbers + #"],"indexes":["#
            + quoted(point.indexes) + "]}"
    }

    @Test("every event serializes byte-for-byte with its empty blobs and zero doubles kept in place")
    func everyDataPointJSON() throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let got = try Self.rows.map { String(decoding: try encoder.encode($0.event.dataPoint), as: UTF8.self) }
        #expect(got == Self.rows.map { Self.json($0.expected) })
        #expect(got[3] == #"{"blobs":["preview_shown","",""],"doubles":[0,0],"indexes":["preview_shown"]}"#)
    }
}

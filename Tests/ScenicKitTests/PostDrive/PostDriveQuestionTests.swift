@testable import ScenicKit
import Foundation
import Testing

/// T-0358: when the app asks "Prettier than your usual way?" (R1-R5), decided on Linux. Every table is the whole cross
/// product of its inputs through the shipping entry points, compared as one value; the expected answers are typed
/// here, never derived from the type under test.
@Suite("PostDriveQuestionTests")
struct PostDriveQuestionTests {
    struct Row: Hashable, CustomStringConvertible {
        let outcome: PostDriveOutcome
        let moment: PostDriveMoment
        let surface: DriveSurface
        let asked: Bool
        var description: String { "\(outcome) \(moment) \(surface) asked=\(asked)" }
    }

    static let outcomes: [PostDriveOutcome] = [.arrived, .endedEarly, .handedOff]
    static let moments: [PostDriveMoment] = [.driveEnded, .appOpened]
    static let surfaces: [DriveSurface] = [.full, .minimal]
    static let askedValues = [false, true]

    /// R2/R3/R4: the only two rows that ask. Everything else in the cross product is false.
    static let asking: Set<Row> = [
        Row(outcome: .arrived, moment: .driveEnded, surface: .full, asked: false),
        Row(outcome: .handedOff, moment: .appOpened, surface: .full, asked: false),
    ]

    static var rows: [Row] {
        outcomes.flatMap { outcome in
            moments.flatMap { moment in
                surfaces.flatMap { surface in askedValues.map { Row(outcome: outcome, moment: moment, surface: surface, asked: $0) } }
            }
        }
    }

    static func answer(_ row: Row) -> Bool {
        PostDriveQuestion.asks(outcome: row.outcome, moment: row.moment, surface: row.surface, alreadyAsked: row.asked)
    }

    @Test("T-0358 R2-R4: the whole outcome x moment x surface x already-asked table asks exactly the two typed rows")
    func everyRow() {
        let rows = Self.rows
        #expect(rows.count == 24 && Set(rows).count == 24)
        #expect(Self.outcomes.count == PostDriveOutcome.allCases.count && Self.moments.count == PostDriveMoment.allCases.count
                && Self.surfaces.count == DriveSurface.allCases.count)
        let got = Dictionary(uniqueKeysWithValues: rows.map { ($0, Self.answer($0)) })
        let want = Dictionary(uniqueKeysWithValues: rows.map { ($0, Self.asking.contains($0)) })
        #expect(got == want)
    }

    @Test("T-0358: no input is ignored - for each of the four, some pair of rows differing only in it answers differently")
    func noInputIgnored() {
        let rows = Self.rows
        func flips(_ vary: (Row) -> [Row]) -> Bool {
            rows.contains { row in vary(row).contains { Self.answer($0) != Self.answer(row) } }
        }
        #expect(flips { r in Self.outcomes.map { Row(outcome: $0, moment: r.moment, surface: r.surface, asked: r.asked) } })
        #expect(flips { r in Self.moments.map { Row(outcome: r.outcome, moment: $0, surface: r.surface, asked: r.asked) } })
        #expect(flips { r in Self.surfaces.map { Row(outcome: r.outcome, moment: r.moment, surface: $0, asked: r.asked) } })
        #expect(flips { r in Self.askedValues.map { Row(outcome: r.outcome, moment: r.moment, surface: r.surface, asked: $0) } })
    }

    @Test("T-0358 R2/R8: after every drive display - every surface x mode x arrived x already-asked - asks only full, arrived, not asked")
    func afterEveryDisplay() {
        var got: [String: Bool] = [:]
        var want: [String: Bool] = [:]
        for surface in DriveSurface.allCases {
            for mode in DriveMode.allCases {
                for arrived in [false, true] {
                    for asked in Self.askedValues {
                        let key = "\(surface) \(mode) arrived=\(arrived) asked=\(asked)"
                        let display = DriveDisplay(surface: surface, mode: mode, arrived: arrived)
                        got[key] = PostDriveQuestion.asks(after: display, alreadyAsked: asked)
                        want[key] = surface == .full && arrived && !asked
                    }
                }
            }
        }
        #expect(got.count == 24 && got == want)
    }

    @Test("T-0358 R2: a display carries the arrival it was given, and a session's display has not arrived")
    func displayCarriesArrival() throws {
        #expect(DriveDisplay(surface: .full, mode: .guiding).arrived == false)
        #expect(DriveDisplay(surface: .full, mode: .guiding, arrived: true).arrived == true)
        let line = [Coordinate(latitude: 0, longitude: 0), Coordinate(latitude: 0, longitude: 0.01)]
        let session = try #require(DriveSession(line: line, waypoints: [], lambda: 0.5, online: true))
        #expect(DriveDisplay(session: session).arrived == false)
        #expect(DriveDisplay(session: session, arrived: true)
                == DriveDisplay(surface: session.surface, mode: session.mode, line: line,
                                etaLine: DriveDisplay(session: session).etaLine, arrived: true))
    }

    @Test("T-0358 R5/R9: the answer set, its titles, what each sends, and the prompt - each compared whole")
    func answerSet() {
        #expect(PostDriveAnswer.allCases == [.prettier, .notPrettier, .dismissed])
        #expect(PostDriveAnswer.allCases.map(\.title) == ["Prettier", "Not really", "Skip"])
        #expect(PostDriveAnswer.allCases.map(\.prettier) == [true, false, nil])
        #expect(PostDriveQuestion.prompt == "Prettier than your usual way?")
    }

    @Test("T-0358 R5/R6: a sink hears exactly the two answers that send, in order, and never a dismissal")
    func sendsOnlyAnswers() {
        let sink = RecordingAnswers()
        for answer in PostDriveAnswer.allCases { PostDriveQuestion.send(answer, to: sink) }
        PostDriveQuestion.send(.prettier, to: nil)
        #expect(sink.heard == [true, false])
    }
}

/// Records what PostDriveQuestion hands a sink.
final class RecordingAnswers: PostDriveAnswering, @unchecked Sendable {
    private(set) var heard: [Bool] = []
    func answered(prettier: Bool) { heard.append(prettier) }
}

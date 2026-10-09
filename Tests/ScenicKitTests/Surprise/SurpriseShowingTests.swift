import Foundation
import ScenicKit
import Testing

/// T-0310 acceptance 3 (R7): a shown place goes into the device history - the 90-day no-repeat's input - once a
/// day; the whole history by full equality, the feedback untouched.
@Suite("SurpriseShowingTests") struct SurpriseShowingTests {
    static let today = SurpriseShownFixture.today
    static let yesterday = SurpriseShownFixture.yesterday
    static let a = SurpriseShownFixture.a
    static let b = SurpriseShownFixture.b

    static func shown(_ p: SurpriseCandidate, _ date: CivilDate) -> SurpriseHistory.Shown {
        SurpriseShownFixture.shown(p, date)
    }

    static let feedback = SurpriseFeedback(candidateId: "7654321", category: .park, roundTripMinutes: 60,
                                           date: yesterday, reason: .wrongTime)

    struct Row: Sendable, CustomTestStringConvertible {
        let label: String
        let history: SurpriseHistory
        let expected: SurpriseHistory?
        var testDescription: String { label }
    }

    static let rows: [Row] = [
        Row(label: "an empty history", history: SurpriseHistory(),
            expected: SurpriseHistory(shown: [shown(a, today)])),
        Row(label: "shown yesterday", history: SurpriseHistory(shown: [shown(a, yesterday)]),
            expected: SurpriseHistory(shown: [shown(a, yesterday), shown(a, today)])),
        Row(label: "already shown today", history: SurpriseHistory(shown: [shown(b, today), shown(a, today)]),
            expected: nil),
        Row(label: "another place today, with feedback",
            history: SurpriseHistory(shown: [shown(b, today)], feedback: [feedback]),
            expected: SurpriseHistory(shown: [shown(b, today), shown(a, today)], feedback: [feedback])),
    ]

    @Test("A shown place is appended once a day, its category and corridor its own", arguments: rows)
    func recording(_ row: Row) {
        #expect(SurpriseShowing.recording(Self.a, on: Self.today, in: row.history) == row.expected)
    }
}

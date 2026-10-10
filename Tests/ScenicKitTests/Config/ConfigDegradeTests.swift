import Foundation
import ScenicKit
import Testing

/// T-0357 A6-A7: the degrade mapping as a literal table (R5), our build's reader, each degrade's notice (R6) and the
/// gate it closes.
@Suite("ConfigDegradeTests")
struct ConfigDegradeTests {
    static let max = 2_147_483_647
    /// The minimum builds the table's columns are, in order.
    static let mins = [1, 41, 42, 43, max]
    /// (paused, our build, one letter per `mins` column: c clear, p planningPaused, u updateRequired).
    static let table: [(Bool, Int?, String)] = [
        (false, nil, "ccccc"), (false, 1, "cuuuu"), (false, 42, "cccuu"), (false, max, "ccccc"),
        (true, nil, "ppppp"), (true, 1, "puuuu"), (true, 42, "pppuu"), (true, max, "ppppp"),
    ]
    static let letters: [Character: ConfigDegrade] = ["c": .clear, "p": .planningPaused, "u": .updateRequired]

    @Test("The degrade is exactly the table's row for every pause, minimum build and our build")
    func mapping() {
        var seen = 0
        for (paused, build, row) in Self.table {
            #expect(row.count == Self.mins.count)
            for (min, letter) in zip(Self.mins, row) {
                let degrade = ConfigDegrade.of(RemoteConfig(minAppBuild: min, planningPaused: paused), appBuild: build)
                #expect(degrade == Self.letters[letter], "paused \(paused) min \(min) build \(String(describing: build))")
                seen += 1
            }
        }
        #expect(seen == 40)
    }

    @Test("Our build reads only a positive decimal integer within 1...2147483647")
    func appBuild() {
        let rows: [(String?, Int?)] = [
            (nil, nil), ("", nil), ("0", nil), ("1", 1), ("2", 2), ("9", 9), ("42", 42), ("01", 1),
            ("2147483646", 2_147_483_646), ("2147483647", Self.max), ("2147483648", nil),
            ("99999999999999999999", nil), ("+1", nil), ("-1", nil), (" 1", nil), ("1 ", nil), ("1.0", nil),
            ("1a", nil), ("0x1", nil), ("\u{FF11}", nil), ("\u{0663}", nil),
        ]
        for (text, expected) in rows {
            #expect(AppBuild.parse(text) == expected, "\(String(describing: text))")
        }
        #expect(RemoteConfig.maxAppBuild == Self.max)
    }

    @Test("Each degrade's notice is its row: the typed planningPaused copy, the update line, none")
    func notices() {
        #expect(ConfigDegrade.allCases == [.clear, .planningPaused, .updateRequired])
        #expect(ConfigDegrade.clear.notice == nil)
        #expect(ConfigDegrade.planningPaused.notice == PlanFailureCopy.of(.planningPaused).line)
        #expect(ConfigDegrade.planningPaused.notice == "Planning is paused right now. Surprise Me still works.")
        #expect(ConfigDegrade.updateRequired.notice
                == "This version can't plan drives anymore. Update Scenic Drive from the App Store to keep planning.")
    }

    static let start = PlanPlace(id: 7, name: "Santa Monica Pier",
                                 coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let destination = PlanPlace(id: 42, name: "Topanga Lookout",
                                       coordinate: Coordinate(latitude: 34.09312, longitude: -118.60071))

    static func chosen(_ degrade: ConfigDegrade) -> PlanSheet {
        var sheet = PlanSheet(disclaimerAccepted: true)
        sheet.search("", for: .start)
        sheet.choose(start)
        sheet.search("", for: .destination)
        sheet.choose(destination)
        sheet.setDegrade(degrade)
        return sheet
    }

    @Test("Under a degrade the gate issues no ticket; clear, it issues one; clearing reopens it")
    func gate() {
        for degrade in ConfigDegrade.allCases {
            var sheet = Self.chosen(degrade)
            #expect(sheet.degrade == degrade)
            let ticket = sheet.startPlanning()
            if degrade == .clear {
                #expect(ticket?.origin == Coordinate(latitude: 34.01, longitude: -118.5))
                #expect(ticket?.place == 42)
                #expect(ticket?.budgetMinutes == 30)
            } else {
                #expect(ticket == nil, "\(degrade)")
                #expect(sheet.state == .chosen(Self.destination), "\(degrade)")
                sheet.setDegrade(.clear)
                #expect(sheet.startPlanning() != nil, "\(degrade) then clear")
            }
        }
    }

    struct Fixed: RoutePlanning {
        let answer: ConfigDegrade
        func plan(_ ticket: PlanTicket) async -> PlanOutcome { .failure(.routingOffline) }
        func degrade() async -> ConfigDegrade { answer }
    }

    @Test("The retiming planner's degrade is its inner planner's")
    @MainActor
    func retiming() async {
        for degrade in ConfigDegrade.allCases {
            let learner = CorridorLearner(speeds: LearnedCorridorSpeeds(timeZone: TimeZone(identifier: "UTC")!),
                                          save: { _ in })
            let planner = RetimingPlanner(inner: Fixed(answer: degrade), learner: learner, now: { Date() })
            #expect(await planner.degrade() == degrade)
        }
    }
}

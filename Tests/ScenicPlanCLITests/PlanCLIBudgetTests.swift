import Foundation
import Testing
import ScenicKit
@testable import ScenicPlanCLI

/// The CLI's own unit conversion, which until T-0182's pre-review pass was asserted by NOTHING.
///
/// `ops/plan <O> <D> 25` means 25 MINUTES, because that is the unit the product speaks in; every number
/// below `PlanArguments.budget` is seconds. Changing that one multiplication to `* 3600` left all 315
/// tests green and shipped a tool that printed `budget=25h00m00s` and enforced a 25-hour ceiling - a
/// silent breach of the invariant CLAUDE.md states without qualification: *the extra-time budget is a
/// ceiling: returned ETA <= fastest + budget. Always.*
///
/// Both halves are here, and the second is the one that matters: a test of `parse` alone would be a test
/// of a number nothing has to use. The second drives `PlanCommand.run`, the function `main.swift` calls -
/// the same call `ops/plan` makes, over the same recorded pair - and reads the ceiling off the line the
/// terminal prints. With `* 3600` the parse assertion and the printed ceiling both fail by name.
@Suite("ops/plan budget")
struct PlanCLIBudgetTests {

    /// The recorded canyon pair: Topanga village to PCH at Malibu Canyon, off T-0213's graph. The same
    /// fixture ScenicPlanGoldenTests plans over, reached through the CLI's `--recorded` flag here, so what
    /// is under test is the tool's own path to it.
    static let fixture = URL(fileURLWithPath: #filePath)   // Tests/ScenicPlanCLITests/<this file>
        .deletingLastPathComponent()                       // Tests/ScenicPlanCLITests
        .deletingLastPathComponent()                       // Tests
        .appendingPathComponent("Fixtures/t0182/plan-pair")

    /// Exactly what `ops/plan 34.0944,-118.6013 34.0365,-118.6870 25 --recorded <dir>` hands the CLI.
    static func arguments() throws -> PlanArguments {
        try PlanArguments.parse(["34.0944,-118.6013", "34.0365,-118.6870", "25",
                                 "--recorded", fixture.path])
    }

    @Test("25 extra minutes on the command line is 1500 seconds of budget")
    func theMinutesTypedBecomeSeconds() throws {
        let arguments = try Self.arguments()
        #expect(arguments.budgetMinutes == 25)
        #expect(arguments.budget == 1500)
    }

    @Test("the ceiling ops/plan prints is the fastest route plus the minutes asked for")
    func theCeilingIsTheFastestRoutePlusTheBudget() throws {
        let lines = try PlanCommand.run(Self.arguments())

        // 17m56s fastest + 25m00s asked for = 42m56s, and the returned route is inside it.
        let eta = try #require(lines.first { $0.hasPrefix("ETA ") })
        #expect(eta == "ETA fastest=17m56s returned=37m33s ceiling=42m56s distance=33068.9m")

        // The budget the tool ECHOES is the one it was given, in the unit it was given in.
        let plan = try #require(lines.first { $0.hasPrefix("PLAN ") })
        #expect(plan.hasSuffix("budget=25m00s"))
    }
}

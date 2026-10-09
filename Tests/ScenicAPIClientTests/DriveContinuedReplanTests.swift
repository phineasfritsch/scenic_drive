import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0330: the Worker's `continued` through the shipping chain NavAdapter runs - DriveSession(preview:online:), fixes
/// into DriveController, the `.send` through PlanRerouter over a recording transport, the answer back under its ticket
/// - over continued {true, false, absent, not a boolean}. Each row's session and full-surface display are compared
/// WHOLE against literals; PlanRerouter.reply(of:) is compared whole to the RerouteReply it must build.
@Suite struct DriveContinuedReplanTests {
    typealias R = DriveReplanTests
    static let freshNote = "A new route from here - not the rest of your plan."

    /// The Worker's 200 from DriveReplanTests.reply() with `field` spliced in before its closing brace (nil: absent).
    static func reply(continued field: String?) -> PlanHTTPReply {
        let base = String(decoding: R.reply().body, as: UTF8.self)
        guard let field else { return R.reply() }
        return PlanHTTPReply(status: 200, body: Data((String(base.dropLast()) + ",\"continued\":\(field)}").utf8))
    }

    struct Variant { let label: String; let field: String?; let taken: Bool; let continued: Bool }
    static let variants = [Variant(label: "true", field: "true", taken: true, continued: true),
                           Variant(label: "false", field: "false", taken: true, continued: false),
                           Variant(label: "absent", field: nil, taken: true, continued: false),
                           Variant(label: "a string", field: "\"yes\"", taken: false, continued: true)]

    struct Seen: Equatable {
        let mode: DriveMode
        let continued: Bool
        let display: DriveDisplay
    }

    /// The whole outcome the row must produce, as literals: taken (the answer's line, its ETA line, the note when
    /// fresh) or refused (rejoining on the preview's line with the preview's ETA line, no note).
    static func expected(_ v: Variant) -> Seen {
        guard v.taken else {
            return Seen(mode: .rejoining, continued: true, display: DriveDisplay(
                surface: .full, mode: .rejoining, line: R.line, etaLine: "25 min · 5 min longer than the fastest way"))
        }
        return Seen(mode: .guiding, continued: v.continued, display: DriveDisplay(
            surface: .full, mode: .guiding, line: R.answerLine, etaLine: "15 min · 2 min longer than the fastest way",
            continued: v.continued))
    }

    static func run(_ v: Variant) async -> Seen {
        let preview = PlanPreview(route: R.line, etaSeconds: 1_500, fastestEtaSeconds: 1_200, etaIsEstimate: true,
                                  hazards: [], waypoints: R.pins, lambda: 7.75,
                                  continuation: PlanContinuation(token: R.planToken, place: 42, budgetMinutes: 25))
        var controller = DriveController(session: DriveSession(preview: preview, online: true)!)
        var commands = controller.observe(R.fix(R.midpoint(0), 0))
        for t in 1...6 { commands += controller.observe(R.fix(R.away(0), Double(t))) }
        await R.carryOut(commands, &controller, R.rerouter(CountingPlanTransport(reply: reply(continued: v.field))))
        let at = v.taken ? R.answerLine[0] : R.away(0)
        _ = controller.observe(DriveFix(coordinate: at, speedMetersPerSecond: 0, timestamp: 7))
        return Seen(mode: controller.session.mode, continued: controller.session.continued,
                    display: DriveDisplay(session: controller.session))
    }

    @Test("T-0330 R3: continued true / false / absent / not a boolean - taken with its ETA and note, or refused whole")
    func continuedThroughTheRerouter() async {
        for v in Self.variants {
            #expect(await Self.run(v) == Self.expected(v), "continued \(v.label)")
        }
    }

    @Test("T-0330: no row ignores its variant, and the expected displays are the literals the screen shows")
    func noRowIgnoresItsVariant() {
        let all = Self.variants.map(Self.expected)
        #expect(all[0] != all[1] && all[0] != all[3] && all[1] != all[3])
        #expect(all[1] == all[2])
        #expect(all.map(\.display.note) == [nil, Self.freshNote, Self.freshNote, nil])
    }

    @Test("T-0330 R4: PlanRerouter.reply(of:) carries the answer's line, pins, token, ETA, fastest ETA and marker, whole")
    func replyCarriesTheMarkerAndEta() async throws {
        for (field, continued) in [("true", true), ("false", false)] {
            let response = try await PlanWire.plan(answering: Self.reply(continued: field)).outcome.get()
            #expect(response.continued == continued)
            #expect(PlanRerouter.reply(of: response)
                == RerouteReply(line: R.answerLine, waypoints: R.answerPins, planToken: R.answerToken, etaSeconds: 900,
                                fastestEtaSeconds: 800, continued: continued))
        }
        let absent = try await PlanWire.plan(answering: Self.reply(continued: nil)).outcome.get()
        #expect(absent.continued == false)
    }
}

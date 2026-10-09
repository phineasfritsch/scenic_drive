@testable import ScenicKit
import Foundation
import Testing

/// T-0330 R3/R4: a fresh answer mid-drive is TAKEN with a note on the full surface, and the drive screen's ETA line is
/// the line being driven - the preview's, then each taken answer's. Every row runs the shipping entry points:
/// DriveSession(preview:online:) as NavAdapter seeds it, DriveController under its ticket, DriveDisplay(session:) as
/// the navigator publishes it - and compares the whole display or session against literals.
@Suite struct DriveContinuedTests {
    static let planToken = "0f1e2d3c-4b5a-4968-8776-655443322110"
    static let answerToken = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
    static let line = DriveFixtures.line(latitude: 34.05, firstLongitude: -118.70, count: 6)
    static let pins = [line[1], line[2], line[3]]
    static let answerLine = DriveFixtures.line(latitude: 34.03, firstLongitude: -118.70, count: 5)
    static let answerPins = [answerLine[2], answerLine[3]]
    static let continuation = PlanContinuation(token: planToken, place: 42, budgetMinutes: 25)
    static let freshNote = "A new route from here - not the rest of your plan."

    static func preview(eta: Double = 1_500, fastest: Double = 1_200,
                        continuation: PlanContinuation? = continuation) -> PlanPreview {
        PlanPreview(route: line, etaSeconds: eta, fastestEtaSeconds: fastest, etaIsEstimate: true, hazards: [],
                    waypoints: pins, lambda: 7.75, continuation: continuation)
    }

    static func fix(_ latitude: Double, _ longitude: Double, _ t: Double, speed: Double = 12) -> DriveFix {
        DriveFix(coordinate: Coordinate(latitude: latitude, longitude: longitude), speedMetersPerSecond: speed,
                 timestamp: t)
    }

    /// The preview's drive, off its line for the 5 s dwell: the one reroute is out under ticket 1.
    static func rerouting() -> DriveController {
        var controller = DriveController(session: DriveSession(preview: preview(), online: true)!)
        _ = controller.observe(fix(34.05, -118.695, 0))
        for t in 1...6 { _ = controller.observe(fix(34.052, -118.694, Double(t))) }
        return controller
    }

    /// The answer the Worker sent, as PlanRerouter hands it over.
    static func reply(continued: Bool, eta: Double = 900, fastest: Double = 800,
                      line: [Coordinate] = answerLine) -> RerouteReply {
        RerouteReply(line: line, waypoints: answerPins, planToken: answerToken, etaSeconds: eta,
                     fastestEtaSeconds: fastest, continued: continued)
    }

    static let surfaces: [(label: String, speed: Double)] = [("full", 0), ("minimal", 12)]
    static let continuedVariants = [true, false]

    /// What the screen must show after the answer is taken and the driver is seen on it at `speed`: literals.
    static func expected(continued: Bool, speed: Double) -> DriveDisplay {
        let eta = "15 min · 2 min longer than the fastest way"
        return speed == 0
            ? DriveDisplay(actionTitle: "End drive", actionMinHeight: 44, status: nil, showsDetails: true,
                           line: answerLine, etaLine: eta, note: continued ? nil : freshNote)
            : DriveDisplay(actionTitle: "End drive", actionMinHeight: 60, status: nil, showsDetails: false,
                           line: answerLine, etaLine: eta, note: nil)
    }

    @Test("T-0330 R3/R4: continued x surface - the taken answer's ETA line, and the fresh note on the full surface only")
    func continuedBySurface() {
        for continued in Self.continuedVariants {
            for surface in Self.surfaces {
                var controller = Self.rerouting()
                let took = controller.rerouteArrived(ticket: 1, reply: Self.reply(continued: continued))
                #expect(took)
                _ = controller.observe(Self.fix(34.03, -118.695, 7, speed: surface.speed))
                #expect(DriveDisplay(session: controller.session)
                    == Self.expected(continued: continued, speed: surface.speed),
                        "continued \(continued), \(surface.label)")
                #expect(controller.session.continued == continued)
            }
        }
    }

    @Test("T-0330: no row ignores its variant - on the full surface the two answers differ only by the note")
    func noRowIgnoresItsVariant() {
        let full = Self.continuedVariants.map { Self.expected(continued: $0, speed: 0) }
        #expect(full[0] != full[1])
        #expect(full[0].note == nil && full[1].note == Self.freshNote)
        let minimal = Self.continuedVariants.map { Self.expected(continued: $0, speed: 12) }
        #expect(minimal[0] == minimal[1] && minimal[0].note == nil)
        #expect(Self.expected(continued: true, speed: 0) != Self.expected(continued: true, speed: 12))
    }

    @Test("T-0330 R4: the preview seeds the drive - line, pins, lambda, token and ETA - and its ETA line until a reroute")
    func previewSeedsTheDrive() {
        let session = DriveSession(preview: Self.preview(), online: true)
        #expect(session == DriveSession(line: Self.line, waypoints: Self.pins, lambda: 7.75, online: true,
                                        planToken: Self.planToken, etaSeconds: 1_500, fastestEtaSeconds: 1_200))
        #expect(session?.etaSeconds == 1_500 && session?.fastestEtaSeconds == 1_200 && session?.continued == true)
        let tokenless = DriveSession(preview: Self.preview(continuation: nil), online: false)
        #expect(tokenless == DriveSession(line: Self.line, waypoints: Self.pins, lambda: 7.75, online: false,
                                          etaSeconds: 1_500, fastestEtaSeconds: 1_200))
        var stopped = session!
        _ = stopped.observe(Self.fix(34.05, -118.695, 0, speed: 0))
        #expect(DriveDisplay(session: stopped)
            == DriveDisplay(actionTitle: "End drive", actionMinHeight: 44, status: nil, showsDetails: true,
                            line: Self.line, etaLine: "25 min · 5 min longer than the fastest way", note: nil))
    }

    /// Every bound of an ETA: just below 0, 0, exactly a day, just above it, and NaN and both infinities.
    static let bounds: [(label: String, value: Double, accepted: Bool)] = [
        ("just below 0", -Double.leastNonzeroMagnitude, false), ("0", 0, true), ("86400", 86_400, true),
        ("just above 86400", Double(86_400).nextUp, false), ("NaN", .nan, false), ("+inf", .infinity, false),
        ("-inf", -.infinity, false),
    ]

    struct Taken: Equatable {
        let line: [Coordinate]
        let token: String?
        let eta: Double
        let fastest: Double
        let continued: Bool
        let mode: DriveMode
    }

    static func taken(_ session: DriveSession) -> Taken {
        Taken(line: session.line.coordinates, token: session.planToken, eta: session.etaSeconds,
              fastest: session.fastestEtaSeconds, continued: session.continued, mode: session.mode)
    }

    static let kept = Taken(line: line, token: planToken, eta: 1_500, fastest: 1_200, continued: true, mode: .rejoining)

    @Test("T-0330 R5: every ETA bound x field x entry - an answer or a preview outside 0...86400 s is refused whole")
    func etaBounds() {
        for bound in Self.bounds {
            for field in ["eta", "fastest"] {
                let eta = field == "eta" ? bound.value : 900
                let fastest = field == "fastest" ? bound.value : 800
                var controller = Self.rerouting()
                let took = controller.rerouteArrived(ticket: 1,
                                                     reply: Self.reply(continued: false, eta: eta, fastest: fastest))
                let want = bound.accepted
                    ? Taken(line: Self.answerLine, token: Self.answerToken, eta: eta, fastest: fastest, continued: false,
                            mode: .guiding)
                    : Self.kept
                #expect(took == bound.accepted && Self.taken(controller.session) == want, "\(field) \(bound.label)")
                let seeded = DriveSession(preview: Self.preview(eta: field == "eta" ? bound.value : 1_500,
                                                                fastest: field == "fastest" ? bound.value : 1_200),
                                          online: true)
                #expect((seeded != nil) == bound.accepted, "preview \(field) \(bound.label)")
            }
        }
    }

    @Test("T-0330 R5: an answer refused for its line takes neither its ETA nor its marker")
    func refusedAnswerTakesNothing() {
        var controller = Self.rerouting()
        let refused = controller.rerouteArrived(ticket: 1, reply: Self.reply(continued: false, line: [Self.answerLine[0]]))
        #expect(!refused)
        #expect(Self.taken(controller.session) == Self.kept)
        var late = Self.rerouting()
        let dropped = late.rerouteArrived(ticket: 2, reply: Self.reply(continued: false))
        #expect(!dropped)
        #expect(Self.taken(late.session)
            == Taken(line: Self.line, token: Self.planToken, eta: 1_500, fastest: 1_200, continued: true,
                     mode: .rerouting))
    }
}

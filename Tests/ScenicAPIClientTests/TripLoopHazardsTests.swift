import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0340 A3/A4: a /trip day's or the /loop's hazard runs, sent through the shipping clients and planners, reach the
/// card's lines WHOLE (R5, the copy written out here independently of HazardCopy), and a hazards field the client
/// cannot read refuses the whole answer (R3) - every malformed row is a function of its base.
@Suite("TripLoopHazardsTests")
struct TripLoopHazardsTests {
    static let gravel = "Gravel on part of this route - check it suits your car"
    static let restricted = "Restricted access on part of this route - check the signs before you drive it"
    static let generic = "Something on part of this route needs a closer look - check the road before you drive it"

    static let gravelRun = #"{"kind":"surface","value":"gravel","from_index":0,"to_index":1}"#
    static let oddAccessRun = #"{"kind":"road_access","value":"permit","from_index":1,"to_index":2}"#
    static let unknownRun = #"{"kind":"ford","value":"yes","from_index":0,"to_index":2}"#
    static let full = "[\(gravelRun),\(oddAccessRun),\(unknownRun)]"
    static let fullRuns = [PlanHazardRun(kind: "surface", value: "gravel", fromIndex: 0, toIndex: 1),
                           PlanHazardRun(kind: "road_access", value: "permit", fromIndex: 1, toIndex: 2),
                           PlanHazardRun(kind: "ford", value: "yes", fromIndex: 0, toIndex: 2)]
    static let field = #""hazards":[]"#

    enum Answer: CaseIterable { case tripPreview, tripFull, loop }

    /// The answer's body with its n-th hazards field replaced, in order (a trip preview has two days).
    static func body(_ answer: Answer, _ fields: [String]) -> String {
        var text: String
        switch answer {
        case .tripPreview: text = TripWire.previewBody
        case .tripFull: text = TripWire.fullBody
        case .loop: text = LoopWire.squareBody
        }
        for replacement in fields {
            guard let at = text.range(of: field) else { return "unreachable: no hazards field left" }
            text.replaceSubrange(at, with: replacement)
        }
        return text
    }

    /// What the card reads, through the shipping entry points; nil when the client did not answer a route.
    static func read(_ body: String, _ answer: Answer) async -> (lines: [String], runs: [[PlanHazardRun]])? {
        let reply = TripWire.reply(200, body)
        switch answer {
        case .tripPreview, .tripFull:
            guard case .success(let response) = await TripWire.trip(through: CountingPlanTransport(reply: reply))
            else { return nil }
            let itinerary = ClientTripPlanner.itinerary(of: response)
            return (HazardCopy.lines(for: itinerary), itinerary.days.map(\.hazards))
        case .loop:
            guard case .success(let response) = await LoopWire.loop(through: CountingPlanTransport(reply: reply)),
                  case .preview(let preview) = ClientLoopPlanner.outcome(of: response) else { return nil }
            return (HazardCopy.lines(for: preview), [preview.hazards])
        }
    }

    @Test("trip and loop answers read their hazard lines, whole")
    func readsWhole() async {
        let rows: [(Answer, [String], [String], [[PlanHazardRun]])] = [
            (.tripPreview, [Self.field, Self.field], [], [[], []]),
            (.tripPreview, [#""hazards":[\#(Self.gravelRun)]"#, #""hazards":[\#(Self.oddAccessRun),\#(Self.unknownRun)]"#],
             ["Day 1 · \(Self.gravel)", "Day 2 · \(Self.restricted)", "Day 2 · \(Self.generic)"],
             [[Self.fullRuns[0]], [Self.fullRuns[1], Self.fullRuns[2]]]),
            (.tripFull, [Self.field], [], [[]]),
            (.tripFull, ["\"hazards\":\(Self.full)"], ["Day 1 · \(Self.gravel)", "Day 1 · \(Self.restricted)", "Day 1 · \(Self.generic)"],
             [Self.fullRuns]),
            (.loop, [Self.field], [], [[]]),
            (.loop, ["\"hazards\":\(Self.full)"], [Self.gravel, Self.restricted, Self.generic], [Self.fullRuns]),
        ]
        for (answer, fields, lines, runs) in rows {
            let got = await Self.read(Self.body(answer, fields), answer)
            #expect(got?.lines == lines, "\(answer) \(fields)")
            #expect(got?.runs == runs, "\(answer) \(fields)")
        }
    }

    /// R3: every way the hazards field or one of its runs can be unreadable, over a base (empty or full).
    static func malformed(base: String) -> [(String, String)] {
        let good = base == "[]" ? "" : String(base.dropFirst().dropLast()) + ","
        func element(_ run: String) -> String { "\"hazards\":[\(good)\(run)]" }
        let kv = #""value":"gravel","from_index":0,"to_index":1"#
        return [
            ("hazards removed", #""unused":0"#), ("hazards null", #""hazards":null"#), ("hazards number", #""hazards":3"#),
            ("hazards string", #""hazards":"gravel""#), ("hazards object", "\"hazards\":\(gravelRun)"),
            ("element not an object", element("7")),
            ("kind removed", element("{\(kv)}")), ("kind number", element(#"{"kind":1,\#(kv)}"#)),
            ("kind null", element(#"{"kind":null,\#(kv)}"#)),
            ("value removed", element(#"{"kind":"surface","from_index":0,"to_index":1}"#)),
            ("value number", element(#"{"kind":"surface","value":4,"from_index":0,"to_index":1}"#)),
            ("value null", element(#"{"kind":"surface","value":null,"from_index":0,"to_index":1}"#)),
            ("from_index removed", element(#"{"kind":"surface","value":"gravel","to_index":1}"#)),
            ("from_index string", element(#"{"kind":"surface","value":"gravel","from_index":"0","to_index":1}"#)),
            ("from_index 1.5", element(#"{"kind":"surface","value":"gravel","from_index":1.5,"to_index":2}"#)),
            ("to_index removed", element(#"{"kind":"surface","value":"gravel","from_index":0}"#)),
            ("to_index string", element(#"{"kind":"surface","value":"gravel","from_index":0,"to_index":"1"}"#)),
            ("to_index null", element(#"{"kind":"surface","value":"gravel","from_index":0,"to_index":null}"#)),
        ]
    }

    @Test("a trip or loop whose hazards cannot be read is refused")
    func refusesUnreadable() async {
        for answer in Answer.allCases {
            for base in ["[]", Self.full] {
                let baseField = "\"hazards\":\(base)"
                let others = answer == .tripPreview ? [baseField] : []
                let baseBody = Self.body(answer, [baseField] + others)
                #expect(await Self.read(baseBody, answer) != nil, "the base decodes: \(answer) \(base)")
                for (label, bad) in Self.malformed(base: base) {
                    let text = Self.body(answer, [bad] + others)
                    #expect(text != baseBody && !text.hasPrefix("unreachable"), "meta: \(label) differs from its base")
                    let reply = TripWire.reply(200, text)
                    switch answer {
                    case .tripPreview, .tripFull:
                        let got = await TripWire.trip(through: CountingPlanTransport(reply: reply))
                        #expect(got == Result.failure(.unexpectedResponse(status: 200)), "\(answer) \(base) \(label)")
                    case .loop:
                        let got = await LoopWire.loop(through: CountingPlanTransport(reply: reply))
                        #expect(got == Result.failure(.unexpectedResponse(status: 200)), "\(answer) \(base) \(label)")
                    }
                }
            }
        }
    }
}

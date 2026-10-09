import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0341 A2/A3: closures_hazard on a plan, trip or loop 200, sent through the shipping clients and planners, reaches
/// the card's lines - every Worker shape (M1) and every unreadable variant (R3), compared WHOLE against the ruled copy
/// (R2) written out here independently of HazardCopy. Every expected list is a function of the variant.
@Suite("ClosuresHazardTests")
struct ClosuresHazardTests {
    static let crosses =
        "This route crosses a reported road closure - expect the road to be blocked and check before you drive"
    static let stale = "Road closure reports may be out of date for this route - check for closures before you drive"
    static let unavailable =
        "Road closures could not be checked for this route - check for closures before you drive"
    static let dropped =
        "Not every reported road closure near this route was checked - check for closures before you drive"
    /// The plan body's one run (surface/dirt), which the strip reads after the closure lines.
    static let dirt = "Dirt road on part of this route - check it suits your car"

    enum Surface: CaseIterable { case plan, trip, loop }

    /// R2: crosses, then the state line (none when fresh), then dropped.
    static func expected(_ state: ClosuresState, dropped isDropped: Bool, crosses isCrossed: Bool) -> [String] {
        var lines: [String] = []
        if isCrossed { lines.append(crosses) }
        if state == .stale { lines.append(stale) }
        if state == .unavailable { lines.append(unavailable) }
        if isDropped { lines.append(dropped) }
        return lines
    }

    /// One Worker-shaped closures_hazard: ordered (key, JSON) fields, and what it says.
    struct Shape {
        let label: String
        var fields: [(String, String)]
        let state: ClosuresState
        let dropped: Bool
        let crosses: Bool

        var json: String { "{" + fields.map { "\"\($0.0)\":\($0.1)" }.joined(separator: ",") + "}" }
    }

    static let version = #""lcs-d7-0123456789abcdef""#
    static let fetchedAt = #""2026-10-09T10:00:00.000Z""#

    static func shape(_ state: ClosuresState, dropped: Bool = false, crosses: Bool = false) -> Shape {
        var fields: [(String, String)]
        switch state {
        case .fresh: fields = [("state", #""fresh""#), ("version", version), ("fetched_at", fetchedAt)]
        case .stale: fields = [("state", #""stale""#), ("version", version), ("fetched_at", fetchedAt)]
        case .unavailable: fields = [("state", #""unavailable""#), ("version", #""none""#), ("fetched_at", "null")]
        }
        if dropped { fields.append(("dropped", "3")) }
        if crosses { fields.append(("crosses", #"["lcs-1","lcs-2"]"#)) }
        return Shape(label: "\(state) dropped=\(dropped) crosses=\(crosses)", fields: fields, state: state,
                     dropped: dropped, crosses: crosses)
    }

    /// M1: every shape withClosuresHazard can put on a plan, trip or loop 200 (the absent key is tested apart).
    static let workerShapes: [Shape] = [
        shape(.fresh, dropped: true), shape(.fresh, crosses: true), shape(.fresh, dropped: true, crosses: true),
        shape(.stale), shape(.stale, dropped: true), shape(.stale, crosses: true),
        shape(.stale, dropped: true, crosses: true), shape(.unavailable),
    ]

    /// The surface's 200 body with `hazard` as its closures_hazard (nil: the key absent).
    static func body(_ surface: Surface, _ hazard: String?) -> String {
        let base: String
        switch surface {
        case .plan: base = PlanResponseDecodeTests.body
        case .trip: base = TripWire.previewBody
        case .loop: base = LoopWire.squareBody
        }
        guard let hazard else { return base }
        return String(base.dropLast()) + #","closures_hazard":"# + hazard + "}"
    }

    /// The card's lines for that body, through the shipping client and planner; nil when no route came back.
    static func lines(_ surface: Surface, _ hazard: String?) async -> [String]? {
        let reply = PlanHTTPReply(status: 200, body: Data(body(surface, hazard).utf8))
        switch surface {
        case .plan:
            guard case .success(let response) = await PlanWire.plan(through: CountingPlanTransport(reply: reply))
            else { return nil }
            return HazardCopy.lines(for: ClientPlanner.preview(of: response, place: 42, budgetMinutes: 25))
        case .trip:
            guard case .success(let response) = await TripWire.trip(through: CountingPlanTransport(reply: reply))
            else { return nil }
            return HazardCopy.lines(for: ClientTripPlanner.itinerary(of: response))
        case .loop:
            guard case .success(let response) = await LoopWire.loop(through: CountingPlanTransport(reply: reply)),
                  case .preview(let preview) = ClientLoopPlanner.outcome(of: response) else { return nil }
            return HazardCopy.lines(for: preview)
        }
    }

    /// What the surface's card reads for these closure lines: the plan strip adds its one run after them.
    static func card(_ surface: Surface, _ closureLines: [String]) -> [String] {
        surface == .plan ? closureLines + [dirt] : closureLines
    }

    @Test("every Worker closures_hazard reads its ruled lines on the plan, trip and loop cards")
    func everyWorkerShape() async {
        for surface in Surface.allCases {
            let absent = await Self.lines(surface, nil)
            #expect(absent == Self.card(surface, []), "\(surface) absent")
            for shape in Self.workerShapes {
                let want = Self.card(surface, Self.expected(shape.state, dropped: shape.dropped, crosses: shape.crosses))
                let got = await Self.lines(surface, shape.json)
                #expect(got == want, "\(surface) \(shape.label)")
            }
        }
    }

    /// A3's variants of one base shape: (label, closures_hazard JSON, the lines it must read).
    static func variants(of base: Shape) -> [(String, String, [String])] {
        func with(_ key: String, _ value: String?) -> String {
            var copy = base
            copy.fields.removeAll { $0.0 == key }
            if let value { copy.fields.append((key, value)) }
            return copy.json
        }
        let unreadable = expected(.unavailable, dropped: base.dropped, crosses: base.crosses)
        var rows: [(String, String, [String])] = ["null", "1", #""stale""#, "[]", "true"].map {
            ("closures_hazard \($0)", $0, [unavailable])
        }
        for value in [nil, "null", "1", #""Fresh""#, #""STALE""#, #"" stale""#, #""expired""#, #""""#] {
            rows.append(("state \(value ?? "removed")", with("state", value), unreadable))
        }
        for value in [nil, "null", "7"] { rows.append(("version \(value ?? "removed")", with("version", value), unreadable)) }
        for value in [nil, "null", "7", "true"] {
            rows.append(("fetched_at \(value ?? "removed")", with("fetched_at", value), unreadable))
        }
        for value in ["0", "-1", "null", #""x""#] {
            rows.append(("dropped \(value)", with("dropped", value),
                         expected(base.state, dropped: true, crosses: base.crosses)))
        }
        for value in ["[]", "null", #""x""#, "[1]"] {
            rows.append(("crosses \(value)", with("crosses", value),
                         expected(base.state, dropped: base.dropped, crosses: true)))
        }
        return rows
    }

    @Test("an unreadable closures_hazard reads the safest line on every card, never silence and never a refusal")
    func unreadableIsSafe() async {
        let bases = [Self.shape(.fresh, dropped: true), Self.shape(.stale), Self.shape(.stale, crosses: true),
                     Self.shape(.unavailable)]
        var count = 0
        for surface in Surface.allCases {
            for base in bases {
                for (label, json, want) in Self.variants(of: base) {
                    #expect(!want.isEmpty, "\(base.label) \(label): a variant may never expect silence")
                    let got = await Self.lines(surface, json)
                    #expect(got == Self.card(surface, want), "\(surface) \(base.label) \(label)")
                    count += 1
                }
            }
        }
        #expect(count == 3 * 4 * 28)
    }
}

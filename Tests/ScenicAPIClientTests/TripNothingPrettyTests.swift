import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0337 A1, A3: /trip's 422 `nothing_pretty` through the shipping entry point, `TripClient.trip`, read fail-closed
/// over the cross product of every day variant and every percent variant. Each row's expected outcome is a function
/// of its two variants (memory table-rows-as-functions-of-input), compared whole, from exactly one request.
@Suite("TripNothingPrettyTests")
struct TripNothingPrettyTests {
    /// (label, the JSON value or nil for "key missing", the whole number it must read as, or nil for "refused").
    typealias Variant = (String, String?, Int?)

    static let days: [Variant] = [
        ("days 1", "1", 1), ("days 3", "3", 3), ("days 5", "5", 5),
        ("days 0", "0", nil), ("days 6", "6", nil), ("days 1 nextDown", "\((1.0).nextDown)", nil),
        ("days 5 nextUp", "\((5.0).nextUp)", nil), ("days 2.5", "2.5", nil), ("days a string", #""3""#, nil),
        ("days a bool", "true", nil), ("days null", "null", nil), ("days missing", nil, nil),
        ("days 1e999", "1e999", nil),
    ]

    static let percents: [Variant] = [
        ("pct 0", "0", 0), ("pct 25", "25", 25), ("pct 40", "40", 40),
        ("pct -1", "-1", nil), ("pct 41", "41", nil), ("pct 0 nextDown", "\((0.0).nextDown)", nil),
        ("pct 40 nextUp", "\((40.0).nextUp)", nil), ("pct 12.5", "12.5", nil), ("pct a string", #""40""#, nil),
        ("pct a bool", "false", nil), ("pct null", "null", nil), ("pct missing", nil, nil),
    ]

    static func body(_ days: String?, _ percent: String?) -> String {
        var fields = [#""error":"nothing_pretty""#]
        if let days { fields.append(#""days":\#(days)"#) }
        if let percent { fields.append(#""extra_budget_pct":\#(percent)"#) }
        return "{" + fields.joined(separator: ",") + "}"
    }

    /// The expected outcome as a function of the two variants: read only when both are.
    static func expected(_ days: Variant, _ percent: Variant) -> Result<TripResponse, TripError> {
        guard let d = days.2, let p = percent.2 else { return .failure(.unexpectedResponse(status: 422)) }
        return .failure(.nothingPretty(TripNothingPretty(days: d, extraBudgetPercent: p)))
    }

    static let rows: [(String, String, Result<TripResponse, TripError>)] = days.flatMap { d in
        percents.map { p in ("\(d.0) x \(p.0)", body(d.1, p.1), expected(d, p)) }
    }

    @Test("the table is every day variant times every percent variant")
    func tableIsTheCrossProduct() {
        #expect(Self.days.count == 13 && Self.percents.count == 12)
        #expect(Self.rows.count == 13 * 12)
        #expect(Set(Self.rows.map(\.0)).count == Self.rows.count)
        #expect(Self.rows.filter { if case .failure(.nothingPretty) = $0.2 { return true }; return false }.count == 9)
    }

    @Test("a dull trip's 422 nothing_pretty is read whole at every bound, refused otherwise",
          arguments: rows.map(\.0))
    func everyRowWhole(_ label: String) async {
        guard let (_, body, expected) = Self.rows.first(where: { $0.0 == label }) else { return }
        let fake = CountingPlanTransport(reply: TripWire.reply(422, body))
        #expect(await TripWire.trip(through: fake) == expected, "\(label)")
        #expect(await fake.count == 1, "\(label)")
    }

    @Test("nothing_pretty at another status is not trusted")
    func anotherStatus() async {
        let body = Self.body("5", "40")
        for status in [400, 404, 429] {
            let fake = CountingPlanTransport(reply: TripWire.reply(status, body))
            #expect(await TripWire.trip(through: fake) == .failure(.unexpectedResponse(status: status)), "\(status)")
        }
        let fake = CountingPlanTransport(reply: TripWire.reply(500, body))
        #expect(await TripWire.trip(through: fake) == .failure(.routingOffline))
    }

    @Test("a dull trip shows its own calm line")
    func copy() {
        #expect(TripError.nothingPretty(TripNothingPretty(days: 5, extraBudgetPercent: 40)).failure == .nothingPretty)
        #expect(TripFailure.nothingPretty.line
            == "Nothing on the way there was pretty enough to show. Try another place to head for.")
        #expect(TripFailure.allCases.count == 13)
    }
}

import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0337 A2, A3: /loop's 422 `nothing_pretty` through the shipping entry point, `LoopClient.loop`, read fail-closed
/// over every minute variant. Each row's expected outcome is a function of its variant, compared whole, from exactly
/// one request.
@Suite("LoopNothingPrettyTests")
struct LoopNothingPrettyTests {
    /// (label, the JSON value or nil for "key missing", the whole number it must read as, or nil for "refused").
    typealias Variant = (String, String?, Int?)

    static let minutes: [Variant] = [
        ("minutes 10", "10", 10), ("minutes 45", "45", 45), ("minutes 180", "180", 180),
        ("minutes 9", "9", nil), ("minutes 181", "181", nil), ("minutes 10 nextDown", "\((10.0).nextDown)", nil),
        ("minutes 180 nextUp", "\((180.0).nextUp)", nil), ("minutes 44.5", "44.5", nil),
        ("minutes a string", #""45""#, nil), ("minutes a bool", "true", nil), ("minutes null", "null", nil),
        ("minutes missing", nil, nil), ("minutes 1e999", "1e999", nil),
    ]

    static func body(_ minutes: String?) -> String {
        guard let minutes else { return #"{"error":"nothing_pretty"}"# }
        return #"{"error":"nothing_pretty","minutes":\#(minutes)}"#
    }

    /// The expected outcome as a function of the variant: read only when it is.
    static func expected(_ variant: Variant) -> Result<LoopResponse, LoopError> {
        guard let m = variant.2 else { return .failure(.unexpectedResponse(status: 422)) }
        return .failure(.nothingPretty(LoopNothingPretty(minutes: m)))
    }

    static let rows: [(String, String, Result<LoopResponse, LoopError>)] = minutes.map { ($0.0, body($0.1), expected($0)) }

    @Test("the table is every minute variant")
    func tableIsEveryVariant() {
        #expect(Self.rows.count == 13)
        #expect(Set(Self.rows.map(\.0)).count == Self.rows.count)
        #expect(Self.rows.filter { if case .failure(.nothingPretty) = $0.2 { return true }; return false }.count == 3)
    }

    @Test("a dull loop's 422 nothing_pretty is read whole at every bound, refused otherwise",
          arguments: rows.map(\.0))
    func everyRowWhole(_ label: String) async {
        guard let (_, body, expected) = Self.rows.first(where: { $0.0 == label }) else { return }
        let fake = CountingPlanTransport(reply: LoopWire.reply(422, body))
        #expect(await LoopWire.loop(through: fake) == expected, "\(label)")
        #expect(await fake.count == 1, "\(label)")
    }

    @Test("nothing_pretty at another status is not trusted")
    func anotherStatus() async {
        let body = Self.body("45")
        for status in [400, 404, 429] {
            let fake = CountingPlanTransport(reply: LoopWire.reply(status, body))
            #expect(await LoopWire.loop(through: fake) == .failure(.unexpectedResponse(status: status)), "\(status)")
        }
        let fake = CountingPlanTransport(reply: LoopWire.reply(500, body))
        #expect(await LoopWire.loop(through: fake) == .failure(.routingOffline))
    }

    @Test("a dull loop shows its own calm line")
    func copy() {
        #expect(LoopError.nothingPretty(LoopNothingPretty(minutes: 45)).failure == .nothingPretty)
        #expect(LoopFailure.nothingPretty.line
            == "No loop from here was pretty enough to show today. Try another start or another length.")
        #expect(LoopFailure.allCases.count == 10)
    }
}

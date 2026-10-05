import Foundation
import Testing
@testable import Telemetry

/// P-PRIV-05's type half (T-0265 R4), as a WHITELIST: every associated value of every event in the encoding
/// table - which covers every TelemetryEventKind - must have one of these types. A Coordinate, a Double, a
/// Date or a String is refused, and so is any type nobody has added here, by case name.
@Suite("P-PRIV-05 payload whitelist") struct TelemetryPayloadWhitelistTests {
    static let allowed: Set<String> = [
        "PlanFeature", "PlanResultKind", "HandoffApp", "SurpriseNotThisReason", "PaywallStep",
        "CompletionPercent", "H3Cell", "Int", "Bool",
    ]

    /// "caseName: TypeName" for every associated value of `event` whose type is not allowed.
    static func refusals(_ event: TelemetryEvent) -> [String] {
        guard let payload = Mirror(reflecting: event).children.first else { return [] }
        let inner = Mirror(reflecting: payload.value)
        let values: [Any] = inner.displayStyle == .tuple ? inner.children.map(\.value) : [payload.value]
        return values.map { String(describing: type(of: $0)) }
            .filter { !allowed.contains($0) }
            .map { "\(payload.label ?? "?"): \($0)" }
    }

    @Test("no event case carries a type outside the P-PRIV-05 whitelist")
    func everyAssociatedValueIsWhitelisted() {
        let refused = TelemetryEventEncodingTests.rows.flatMap { Self.refusals($0.event) }
        #expect(refused.isEmpty, "refused: \(refused)")
    }

    @Test("the whitelist check itself refuses a coordinate-shaped payload")
    func whitelistRefusesADouble() {
        enum Leaky { case located(latitude: Double, longitude: Double) }
        let payload = Mirror(reflecting: Leaky.located(latitude: 34.1, longitude: -118.6)).children.first!
        let types = Mirror(reflecting: payload.value).children.map { String(describing: type(of: $0.value)) }
        #expect(payload.label == "located")
        #expect(types == ["Double", "Double"])
        #expect(types.allSatisfy { !Self.allowed.contains($0) })
    }
}

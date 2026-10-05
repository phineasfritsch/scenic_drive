import Foundation
import Testing
@testable import Telemetry

/// P-PRIV-05's type half (T-0265 R4), as a WHITELIST: every associated value of every event in the encoding
/// table - which covers every TelemetryEventKind - must have one of these types. A Coordinate, a Double, a
/// Date or a String is refused, and so is any type nobody has added here, by case name. The check descends
/// (T-0265 R9): every value stored at ANY depth below an associated value - a struct's fields, an enum's
/// payload, a tuple's slots - must have a type in `allowedStored`, so a whitelisted wrapper cannot smuggle a
/// Double, and each whitelisted type's own field list is pinned by exact equality.
@Suite("P-PRIV-05 payload whitelist") struct TelemetryPayloadWhitelistTests {
    static let allowed: Set<String> = [
        "PlanFeature", "PlanResultKind", "HandoffApp", "SurpriseNotThisReason", "PaywallStep",
        "CompletionPercent", "H3Cell", "Int", "Bool",
    ]

    /// The only types a value may have BELOW an associated value: CompletionPercent.value and H3Cell.index.
    static let allowedStored: Set<String> = ["Int", "UInt64"]

    /// The type of every value stored at any depth below `value`, depth-first.
    static func stored(_ value: Any) -> [String] {
        Mirror(reflecting: value).children.flatMap { [String(describing: type(of: $0.value))] + stored($0.value) }
    }

    /// "label: Type" for each field `value` stores directly.
    static func fields(_ value: Any) -> [String] {
        Mirror(reflecting: value).children.map { "\($0.label ?? "?"): \(type(of: $0.value))" }
    }

    /// "caseName: TypeName" for every associated value of `event`, or value stored below one, whose type is
    /// not allowed at its depth.
    static func refusals(_ event: TelemetryEvent) -> [String] {
        guard let payload = Mirror(reflecting: event).children.first else { return [] }
        let inner = Mirror(reflecting: payload.value)
        let values: [Any] = inner.displayStyle == .tuple ? inner.children.map(\.value) : [payload.value]
        let top = values.map { String(describing: type(of: $0)) }.filter { !allowed.contains($0) }
        let below = values.flatMap { stored($0) }.filter { !allowedStored.contains($0) }
        return (top + below).map { "\(payload.label ?? "?"): \($0)" }
    }

    @Test("no event case carries a type outside the P-PRIV-05 whitelist")
    func everyAssociatedValueIsWhitelisted() {
        let refused = TelemetryEventEncodingTests.rows.flatMap { Self.refusals($0.event) }
        #expect(refused.isEmpty, "refused: \(refused)")
    }

    @Test("each whitelisted payload type stores exactly its pinned fields")
    func whitelistedTypesStoreExactlyTheirFields() {
        let got: [[String]] = [
            Self.fields(CompletionPercent(fraction: 0.5)), Self.fields(TelemetryEventEncodingTests.origin),
            Self.fields(PlanFeature.scenic), Self.fields(PlanResultKind.noAlternative),
            Self.fields(HandoffApp.appleMaps), Self.fields(SurpriseNotThisReason.beenThere),
            Self.fields(PaywallStep.shown),
        ]
        #expect(got == [["value: Int"], ["index: UInt64"], [], [], [], [], []])
    }

    @Test("the whitelist check itself refuses a coordinate-shaped payload")
    func whitelistRefusesADouble() {
        enum Leaky { case located(latitude: Double, longitude: Double) }
        let payload = Mirror(reflecting: Leaky.located(latitude: 34.1, longitude: -118.6)).children.first!
        let types = Mirror(reflecting: payload.value).children.map { String(describing: type(of: $0.value)) }
        #expect(payload.label == "located")
        #expect(types == ["Double", "Double"])
        #expect(types.allSatisfy { !Self.allowed.contains($0) })
        struct Wrapped { let value = 37; let inner = (fraction: 0.375, step: PaywallStep.shown) }
        #expect(Self.stored(Wrapped()) == ["Int", "(fraction: Double, step: PaywallStep)", "Double", "PaywallStep"])
    }
}

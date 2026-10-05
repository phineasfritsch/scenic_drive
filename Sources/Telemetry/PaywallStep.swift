import Foundation

/// The plan writes `paywall_shown/converted` as ONE of its fourteen events (T-0265 R1): one case,
/// `TelemetryEvent.paywall(_:)`, whose step names which of the two wire events it is.
public enum PaywallStep: String, CaseIterable, Sendable {
    case shown
    case converted
}

import SwiftUI

/// What the paywall calls once a purchase from its store view is verified and finished (T-0370 R1-R3). Entitlements
/// sees no ScenicKit or Telemetry type, so the seam is a closure of its own; the shell sets it from PlanAdapter. The
/// closure takes nothing, so no product, transaction or token leaves the paywall through it. Unset, nothing is called.
struct PaywallConvertedKey: EnvironmentKey {
    static let defaultValue: (@Sendable () -> Void)? = nil
}

extension EnvironmentValues {
    public var paywallConverted: (@Sendable () -> Void)? {
        get { self[PaywallConvertedKey.self] }
        set { self[PaywallConvertedKey.self] = newValue }
    }
}

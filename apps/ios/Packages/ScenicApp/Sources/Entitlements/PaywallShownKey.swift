import SwiftUI

/// What the paywall calls when it comes on screen (T-0361 R1/R7). Entitlements sees no ScenicKit type, so the seam
/// is a closure of its own; the shell sets it from PlanAdapter. Unset, nothing is called.
struct PaywallShownKey: EnvironmentKey {
    static let defaultValue: (@Sendable () -> Void)? = nil
}

extension EnvironmentValues {
    public var paywallShown: (@Sendable () -> Void)? {
        get { self[PaywallShownKey.self] }
        set { self[PaywallShownKey.self] = newValue }
    }
}

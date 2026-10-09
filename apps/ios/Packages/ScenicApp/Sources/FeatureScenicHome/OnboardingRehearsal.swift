import Foundation
import ScenicKit

/// The onboarding a DEBUG build opens on when launched with `-screen disclaimer` - ios-screenshot's disclaimer shot
/// (T-0336 R2): the machine advanced past the vehicle step by its own `.next` event, so the disclaimer step shows.
/// Every other launch, and every release build, starts where a new install does. Nothing is accepted or stored here:
/// SafetyDisclaimer's accept button stays the acknowledgement's one writer. The `-screen` pair lands in UserDefaults'
/// argument domain, read inside `#if DEBUG` and written nowhere (DriveRehearsal's pattern).
enum OnboardingRehearsal {
    /// The onboarding to start from.
    static var atLaunch: Onboarding {
        var onboarding = Onboarding()
        #if DEBUG
        if UserDefaults.standard.string(forKey: "screen") == "disclaimer" {
            onboarding.send(.next)
        }
        #endif
        return onboarding
    }
}

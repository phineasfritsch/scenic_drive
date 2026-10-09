import SwiftUI

/// Which screen the app opens on: home always, except in a DEBUG build launched with `-screen settings` or
/// `-screen paywall` - the ios-screenshot workflow's shots (T-0271, ruling R9).
///
/// `simctl launch` hands trailing arguments to the app and a `-key value` pair lands in UserDefaults' argument
/// domain, read here and written nowhere (the `-homeDetent` pattern, `HomeSheetDetent`). The read sits inside
/// `#if DEBUG`, so a release build has no way to open anywhere but home. It lives in Entitlements, not in the app
/// shell, because the shell may carry no `#` directive at all (ops/lib/check-safety-disclaimer-frozen).
public enum LaunchScreen: String, Sendable {
    case home
    case settings
    case paywall
    /// T-0336: Settings opens and pushes Legal & Attribution (`-screen legal`).
    case legal

    /// The launch argument's key: `-screen paywall`.
    static let launchArgumentKey = "screen"

    /// The screen to open on.
    public static var atLaunch: LaunchScreen {
        #if DEBUG
        return UserDefaults.standard.string(forKey: launchArgumentKey).flatMap(LaunchScreen.init(rawValue:)) ?? .home
        #else
        return .home
        #endif
    }
}

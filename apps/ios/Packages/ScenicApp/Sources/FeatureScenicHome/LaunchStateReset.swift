import Foundation

/// DEBUG builds only: `-resetLaunchState YES` empties this app's persistent UserDefaults domain once per process,
/// before the home screen reads anything from it (T-0180, ruling R3).
///
/// It exists for the UI test bundle, which must start every test from a fresh install's state without naming the
/// acknowledgement's store key: P-SAFE-03 counts that key over every Swift file under apps/ios, and a test that
/// set it through the argument domain would also MASK the accept's own write for the life of the process. Removing
/// the whole persistent domain names no key and no identifier, and it can only ever make the safety disclaimer
/// appear again - the fail-safe direction. A release build compiles the branch out: the property is always false.
///
/// `ScenicHomeScreen` reads `applied` from a stored property, so the reset runs when the first screen value is
/// built - before any `@AppStorage` read in its body - and the `static let` makes it run once, however many times
/// SwiftUI rebuilds the screen value afterwards.
enum LaunchStateReset {
    /// The launch argument: `-resetLaunchState YES`, in UserDefaults' argument domain, which nothing persists.
    static let launchArgumentKey = "resetLaunchState"

    /// Whether this process emptied the persistent domain. Evaluated once, lazily, thread-safely.
    static let applied: Bool = {
        #if DEBUG
        guard UserDefaults.standard.bool(forKey: launchArgumentKey),
              let domain = Bundle.main.bundleIdentifier else { return false }
        UserDefaults.standard.removePersistentDomain(forName: domain)
        return true
        #else
        return false
        #endif
    }()
}

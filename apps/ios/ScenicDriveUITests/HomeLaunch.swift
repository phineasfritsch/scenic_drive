import XCTest

/// How every UI test starts the shipping app, and how it finds what the app draws (T-0180).
///
/// Every launch hands the app the same launch arguments the screenshot workflow does - `-homeDetent` and
/// `-menuRow default` - plus, unless a test is checking what SURVIVED a relaunch, `-resetLaunchState YES`: the app's
/// DEBUG-only reset of its own stored defaults (`LaunchStateReset`, ruling R3), so each test starts from a fresh
/// install. The tests never name the acknowledgement's store key: P-SAFE-03 counts it over every Swift file under
/// apps/ios, and what the flag holds is read through what the app DOES, never across processes (ruling R4).
@MainActor
enum HomeLaunch {
    /// The largest Dynamic Type size there is, as UIKit spells it in the argument domain (ruling R7).
    static let largestAccessibilitySize = "UICTContentSizeCategoryAccessibilityXXXL"

    /// Launch (or relaunch - `launch()` terminates a running copy first) and return the running app.
    static func launch(detent: String = "collapsed", reset: Bool = true, contentSize: String? = nil) -> XCUIApplication {
        let app = XCUIApplication()
        var arguments = ["-homeDetent", detent, "-menuRow", "default"]
        if reset {
            arguments += ["-resetLaunchState", "YES"]
        }
        if let contentSize {
            arguments += ["-UIPreferredContentSizeCategoryName", contentSize]
        }
        app.launchArguments = arguments
        app.launch()
        return app
    }

    /// The element carrying accessibility identifier `id`, whatever its element type.
    static func element(_ app: XCUIApplication, _ id: String) -> XCUIElement {
        app.descendants(matching: .any).matching(identifier: id).firstMatch
    }

    /// Whether `app` stopped being the foreground app within `timeout` seconds: the handoff's tap hands the URL to
    /// Apple Maps, and the app goes to the background (or straight to suspended, which `wait(for:)` on one state
    /// can miss).
    static func leftForeground(_ app: XCUIApplication, timeout: TimeInterval) -> Bool {
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            if app.state != .runningForeground {
                return true
            }
            RunLoop.current.run(until: Date().addingTimeInterval(0.5))
        }
        return app.state != .runningForeground
    }
}

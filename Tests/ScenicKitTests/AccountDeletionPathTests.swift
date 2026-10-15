import Foundation
import ScenicKit
import Testing

/// T-0356 A4 (R1, App Review 5.1.1(v)): Delete account is at most three taps from home - home's settings button,
/// Settings' Delete Account row, the confirmation's destructive button - and each step's identifier is set by
/// exactly one whole `.accessibilityIdentifier("<id>")` line of the shipped app sources, so a renamed or removed
/// control fails here by name. The tap itself is the XCUITest half, which waits on T-0180's xcodeproj lock.
@Suite("AccountDeletionPathTests") struct AccountDeletionPathTests {
    static let appSources = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        .deletingLastPathComponent().appendingPathComponent("apps/ios/Packages/ScenicApp/Sources")

    /// Every non-comment line of every Swift file under the app's package sources, trimmed.
    static func appLines() throws -> [String] {
        let files = FileManager.default.enumerator(at: appSources, includingPropertiesForKeys: nil)?
            .compactMap { $0 as? URL }.filter { $0.pathExtension == "swift" } ?? []
        #expect(files.count > 50)
        return try files.flatMap { url in
            try String(contentsOf: url, encoding: .utf8).split(separator: "\n", omittingEmptySubsequences: false)
                .map { $0.trimmingCharacters(in: .whitespaces) }
                .filter { !$0.hasPrefix("//") }
        }
    }

    @Test("The path is at most three actions, in order: home settings, the row, the confirmation")
    func atMostThreeTaps() {
        #expect(AccountDeletionPath.steps.count <= 3)
        #expect(AccountDeletionPath.steps.map(\.identifier)
            == ["home.settings", "settings.deleteAccount", "settings.deleteAccount.confirm"])
    }

    @Test("Every step's identifier is set by exactly one whole line of the shipped app sources")
    func everyStepIsShipped() throws {
        let lines = try Self.appLines()
        for step in AccountDeletionPath.steps {
            let line = ".accessibilityIdentifier(\"\(step.identifier)\")"
            #expect(lines.filter { $0 == line }.count == 1, "\(step.identifier)")
        }
    }
}

import Foundation

/// The taps from home to the DELETE /account request (T-0356 R1, App Review 5.1.1(v)): home's settings button,
/// Settings' Delete Account row, the confirmation's destructive button - three, each named by the accessibility
/// identifier the shipped control carries. The XCUITest that taps them waits on T-0180's xcodeproj lock.
public enum AccountDeletionPath: String, CaseIterable, Sendable {
    case openSettings = "home.settings"
    case openDeletion = "settings.deleteAccount"
    case confirm = "settings.deleteAccount.confirm"

    /// The path in tap order.
    public static let steps: [AccountDeletionPath] = [.openSettings, .openDeletion, .confirm]

    /// The control's accessibility identifier.
    public var identifier: String { rawValue }
}

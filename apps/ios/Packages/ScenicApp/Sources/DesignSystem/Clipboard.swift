import UIKit

/// The system clipboard, as the one line of UIKit the app needs to put text on it.
///
/// It lives in `DesignSystem` for the same reason `DesignTokens` does: this package is the one place
/// that is allowed to know about UIKit, and everything may import it. The root package (`ScenicKit`,
/// `Handoff`) is Linux-only and must never see `UIPasteboard` - CLAUDE.md's repository shape - and a
/// feature that wants to hand the user some text should not have to reach for a pasteboard to do it.
///
/// Named for what the user calls it. `UIPasteboard` is the API; a clipboard is the thing they paste
/// from, and this type is the whole boundary between the two.
///
/// `@MainActor` because UIKit is: declared here rather than left to the call site, so no screen has to
/// guess. Every caller is already a SwiftUI button action, which is main-actor isolated anyway.
@MainActor
public enum Clipboard {
    /// Replaces the clipboard's contents with `text`.
    ///
    /// No return value and no error: `UIPasteboard.general` cannot fail here, and a `Bool` nobody can
    /// act on would only invite a call site to pretend it checked something. What the user sees is the
    /// button that called this changing its own label - see `HandoffFailureCard`.
    public static func copy(_ text: String) {
        UIPasteboard.general.string = text
    }
}

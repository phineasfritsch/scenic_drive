import DesignSystem
import SwiftUI

/// What a failed handoff leaves on screen: what broke, the roads the drive runs, and two things to do
/// about it.
///
/// ## Why the roads are here
///
/// Before this card the failure state offered one move - "Couldn't open Apple Maps. Try again." - and
/// if the second tap failed too the reader had nothing: no road names to write down, no way to get the
/// drive out of the app. The roads are the part of this screen a person can still act on without the
/// app working, so they are what the failure state shows and what the Copy button hands over.
///
/// The road list is PASSED IN, not written here. It is `ScenicHomeScreen.Copy.route`, the one literal
/// T-0152 ruled on, so the roads under the title and the roads in this card cannot say different
/// things.
///
/// ## Why the retry is a closure
///
/// This card never calls `SkylineHandoff.open()` itself. A second place in the app that leaves for
/// Apple Maps is a second place the safety gate has to be remembered, and the gate lives on the
/// screen's button. So the card asks its owner to try again and the owner decides what that means.
///
/// ## Targets and type
///
/// Both buttons are `frame(maxWidth: .infinity, minHeight: 44)` with the label inside the frame, so
/// the 44 pt target holds at the smallest Dynamic Type setting rather than being sized by the text.
/// Text styles only, no point sizes, and `fixedSize` vertically everywhere including the two labels,
/// so accessibility sizes wrap instead of truncating. Colour is `DesignTokens` only: `destructive` for
/// the message, `fg` on `surface` for the roads, `primary`/`onPrimary` for the copy action and a
/// `border` hairline for the secondary one - `primary` is a fill, never a sentence.
struct HandoffFailureCard: View {
    /// What broke, in a sentence the reader can act on. `ScenicHomeScreen` supplies it.
    let message: String

    /// The drive in words - the same road list the header shows.
    let roadList: String

    /// Try again. The owner's handoff, whatever the owner's handoff is today.
    let onRetry: () -> Void

    /// Whether this card's Copy button has been tapped. A clipboard write has no other visible effect,
    /// and an action with no feedback looks identical to a dead one - which is the failure mode
    /// `ScenicHomeScreen` says it exists to avoid. The identifier does not change with the label, so a
    /// UI test finds one `home.error.copy` either way.
    @State private var hasCopied = false

    /// What the Copy button puts on the clipboard: the roads, the straight line, the timing line, one
    /// per line, in the order the screen shows them.
    ///
    /// The timing line travels with the distance on purpose. A paste has no screen above it to carry
    /// the qualification, and a bare "112 km" in a message is read as an hour and a half - the
    /// unmeasured claim this app refuses to make. The strings are `DriveFacts`' own, so what is pasted
    /// and what is rendered cannot drift apart.
    var clipboardText: String {
        [roadList, DriveFacts.straightLine, DriveFacts.timing].joined(separator: "\n")
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(message)
                .font(.footnote)
                .foregroundStyle(DesignTokens.destructive)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.error")

            Text(roadList)
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.error.route")

            HStack(spacing: 12) {
                copyButton
                retryButton
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(DesignTokens.surface)
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .strokeBorder(DesignTokens.border, lineWidth: 1)
                )
        )
    }

    /// Puts the drive on the clipboard and says so.
    private var copyButton: some View {
        Button {
            Clipboard.copy(clipboardText)
            hasCopied = true
        } label: {
            Text(hasCopied ? "Copied" : "Copy the roads")
                .font(.headline)
                .foregroundStyle(DesignTokens.onPrimary)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(DesignTokens.primary)
                )
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("home.error.copy")
    }

    /// The move that was already here, kept: try the handoff again.
    private var retryButton: some View {
        Button {
            onRetry()
        } label: {
            Text("Try again")
                .font(.headline)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .strokeBorder(DesignTokens.border, lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("home.error.retry")
    }
}

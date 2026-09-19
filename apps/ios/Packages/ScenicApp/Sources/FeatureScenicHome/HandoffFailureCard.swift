import DesignSystem
import Handoff
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

    /// The drive in words - the same road list the header shows, for the same selected drive.
    let roadList: String

    /// Which drive failed. Only the distance line needs it, and it is passed rather than re-derived so
    /// that the roads in this card and the kilometres under them cannot come from different drives.
    let drive: HandoffDrive

    /// Try again. The owner's handoff, whatever the owner's handoff is today.
    let onRetry: () -> Void

    /// Whether this card's Copy button has been tapped. A clipboard write has no other visible effect,
    /// and an action with no feedback looks identical to a dead one - which is the failure mode
    /// `ScenicHomeScreen` says it exists to avoid. The identifier does not change with the label, so a
    /// UI test finds one `home.error.copy` either way.
    @State private var hasCopied = false

    /// This surface's OWN timing sentence.
    ///
    /// `DriveFacts.timing(for:)` ends "Apple Maps gives you the real time when it opens", which is
    /// exactly the promise this card cannot keep: it is on screen because Apple Maps did not open. So
    /// the two surfaces say different things, and the one sentence that served both is gone.
    static let timingNote = "Apple Maps did not open, so nothing here can promise a time."

    /// What the Copy button puts on the clipboard: THE URL FIRST, then the roads, the straight line
    /// and the timing sentence, one per line.
    ///
    /// The whole body is one call to `HandoffDrive.clipboardPayload`, which builds the URL from the
    /// same `AppleMapsDirections` `SkylineHandoff.open(` leaves through - the pasted link and the
    /// tapped link are one construction over one drive, and `HandoffDriveClipboardPayloadTests` is
    /// what holds the order on Linux, where this file has no compiler and no test bundle.
    ///
    /// The paste carries the HOME screen's timing sentence, not `timingNote`: it travels to somebody
    /// who will open Maps themselves from the first line, and "Apple Maps did not open" would be this
    /// phone's failure reported as theirs. The distance never travels without it - a bare distance in
    /// a message is read as an ETA.
    var clipboardText: String {
        drive.clipboardPayload(roadList: roadList,
                               straightLine: DriveFacts.straightLine(for: drive),
                               timing: DriveFacts.timing(for: drive))
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

            Text(Self.timingNote)
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.error.timing")

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
            // NAMES THE PAYLOAD (T-0202). "Copy the roads" was true of three lines of prose and is
            // false of a payload whose first line is the Apple Maps link; a reader who is told what
            // lands on the clipboard knows where to paste it.
            Text(hasCopied ? "Copied" : "Copy link + roads")
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

import DesignSystem
import OSLog
import SwiftUI

/// The one button that leaves the app, and the acknowledgement gate in front of it.
///
/// **Why this is a type and not twenty lines inside `ScenicHomeScreen`.** The gate has to be checkable
/// from Linux, on a box with no Apple toolchain and no simulator, by reading source. The property worth
/// pinning is *the handoff is unreachable without the acknowledgement*, which is a call-graph fact;
/// flattened into something a source-level check can actually decide, it is: this file is the only caller
/// of the handoff, the call is dominated by a `guard` on the acknowledgement, and this type is built in
/// exactly one place with the acknowledgement passed in. `ops/lib/check-safety-disclaimer` (P-SAFE-03)
/// decides those three and refuses when any of them stops holding. Inlined in the screen, none of them has
/// a name to anchor on, and the pin would have to anchor on a comment - which CLAUDE.md forbids, because
/// comments get stripped and the guard would go with them.
///
/// The gate is not an opinion this file holds: `isSafetyDisclaimerAcknowledged` comes in from the screen,
/// which owns the `@AppStorage`. One writer, one reader, one place to look.
///
/// - Note: never rendered, never tapped. The XCUITest that proves the first tap opens the disclaimer
///   instead of Apple Maps needs a simulator; this package has no test target and this tree has never been
///   on a device.
struct GatedHandoffButton: View {
    /// Whether the safety disclaimer has already been accepted on this device. Owned by
    /// `ScenicHomeScreen`; see the `@AppStorage` key there.
    let isSafetyDisclaimerAcknowledged: Bool

    /// Called on a tap that the gate stopped. The screen presents the disclaimer.
    let onBlocked: () -> Void

    /// The sentence to put on screen, or `nil` to clear the last one. The screen owns the error line
    /// (`home.error`), because it owns the layout the line has to fit into.
    let onFailure: (String?) -> Void

    /// Where the reason goes when the user gets the sentence. Subsystem is the app's
    /// `PRODUCT_BUNDLE_IDENTIFIER` from `apps/ios/ScenicDrive.xcodeproj/project.pbxproj`; the category is
    /// this button, so a log predicate can pick out the handoff seam without matching the whole app.
    private static let log = Logger(subsystem: "com.phineasfritsch.scenicdrive",
                                    category: "GatedHandoffButton")

    var body: some View {
        Button {
            // The gate. A `guard` rather than an `if`, so there is no branch after it in which the
            // handoff is still reachable, and so the acknowledgement reads positively: `guard !ack` and
            // `ack == false` are not this spelling and P-SAFE-03 refuses them as an absent gate.
            guard isSafetyDisclaimerAcknowledged else {
                onBlocked()
                return
            }
            do {
                try SkylineHandoff.open()
                onFailure(nil)
            } catch {
                // `.public`: `HandoffError` carries a coordinate pair or a waypoint count, and the
                // coordinates in it are the hard-coded route, never the user's location -
                // `SkylineHandoff.directions()` passes `source: nil` precisely so the app never holds one.
                // Redacting it would log a failure with the reason removed, which is the same defect as
                // showing the user a Swift type name instead of a sentence.
                Self.log.error("handoff refused: \(String(describing: error), privacy: .public)")
                onFailure(Copy.handoffFailed)
            }
        } label: {
            Text(Copy.label)
                .font(.headline)
                .foregroundStyle(DesignTokens.onPrimary)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(DesignTokens.primary)
                )
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("home.openInAppleMaps")
    }

    /// The button's own strings. Nested rather than a second file-scope type so the file still declares
    /// one type and still matches its own name (CLAUDE.md).
    private enum Copy {
        /// Unchanged from the walking skeleton: the button says where you end up, not what it does.
        static let label = "Open in Apple Maps"

        /// Shown when the handoff refuses. What failed, then what to do, and nothing this screen cannot
        /// back up: there is no copy-the-route affordance here yet to point the reader at (T-0170).
        static let handoffFailed = "Couldn't open Apple Maps. Try again."
    }
}

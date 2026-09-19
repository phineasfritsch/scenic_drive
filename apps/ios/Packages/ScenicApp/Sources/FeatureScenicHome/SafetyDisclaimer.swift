import DesignSystem
import SwiftUI

/// The blocking safety disclaimer: what this app does not know about the roads it names.
///
/// The plan's P-SAFE-03 and CLAUDE.md's product invariant - *"The safety disclaimer gates the first plan
/// and stays visible on the route screen"* - and the risk table's mitigation for *sedan onto
/// dirt/gated/closed road*: a blocking disclaimer plus a persistent `Conditions change. Verify locally.`
/// line. This type is the blocking half; `ScenicHomeScreen.Copy.conditions` is the persistent half.
///
/// **Blocking, deliberately.** `interactiveDismissDisabled()` means the sheet has no swipe-away and no
/// cancel: the only way out is the button that records the acknowledgement. A disclaimer a user can flick
/// off the screen is a disclaimer that was never read, and it would still satisfy a check that only looked
/// for a sheet.
///
/// **Acknowledged once, on the device.** The store is `@AppStorage` on `ScenicHomeScreen` - see the key
/// there. No account, no server, nothing leaves the phone: the plan's privacy line is that the server
/// never receives more than one coordinate per user action, and an acknowledgement is not one.
///
/// **The wording says what is unknown, not what is safe.** This build has never been driven and the app
/// has no closure feed, no surface evidence and no weather (plan M4/M5 own those). Copy that implied the
/// route had been vetted would be the claim this repository exists to catch; what is written instead is
/// the boundary of what the app knows.
///
/// - Note: nothing here has been rendered. There is no Apple toolchain on the authoring box and this
///   package has no test target, so the XCUITest that proves the sheet actually blocks the handoff - and
///   that `home.disclaimer.accept` is a 44 pt target at every Dynamic Type size - arrives with the first
///   green Xcode Cloud run. `ops/lib/check-safety-disclaimer` checks the structure and says so itself.
struct SafetyDisclaimer: View {
    /// Called when the user accepts. The caller records the acknowledgement and dismisses; this view owns
    /// no storage of its own, so there is exactly one place the flag is written.
    let onAccept: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(Copy.title)
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)

            // Type styles only, no point sizes, so every line grows with Dynamic Type; `fixedSize`
            // vertically so the largest accessibility sizes wrap instead of truncating a safety sentence.
            Text(Copy.body)
                .font(.body)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)

            Text(Copy.conditions)
                .font(.body)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 0)

            accept
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 20)
        .padding(.top, 28)
        .padding(.bottom, 20)
        // `bg` rather than `surface`: this is a full sheet standing in for a screen, not a card floating
        // on one, and `fg` states its contrast against `bg` (`DesignTokens`).
        .background(DesignTokens.bg)
        // The gate. Without this the sheet is advisory - a swipe down and the handoff is ungated.
        .interactiveDismissDisabled()
    }

    /// The one way out.
    ///
    /// `primary` fill with `onPrimary` text, never `primary` as text on `bg` (`DesignTokens`).
    /// `minHeight: 44` is the plan's target floor, applied to the frame rather than to the label, so it
    /// stays a 44 pt target at the smallest Dynamic Type setting too.
    private var accept: some View {
        Button {
            onAccept()
        } label: {
            Text(Copy.accept)
                .font(.headline)
                .foregroundStyle(DesignTokens.onPrimary)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(DesignTokens.primary)
                )
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("home.disclaimer.accept")
    }

    /// Every user-visible string on this sheet, in one place - the same reason `ScenicHomeScreen.Copy`
    /// exists, and the same later extraction into a string catalog.
    private enum Copy {
        static let title = "Before you drive"

        /// What the app does not know. No reassurance, no duration, no claim that anybody has driven this.
        static let body = """
            This app suggests roads. It does not check them. It has no closure feed, no surface evidence \
            and no weather, and nobody has driven the route it is about to hand you.
            """

        /// The same sentence as the persistent line on the home screen, on purpose: the line the user
        /// keeps seeing is the line they agreed to.
        static let conditions = "Conditions change. Verify locally."

        static let accept = "I understand"
    }
}

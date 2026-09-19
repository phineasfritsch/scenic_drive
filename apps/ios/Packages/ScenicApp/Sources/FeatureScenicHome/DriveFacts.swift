import DesignSystem
import Handoff
import SwiftUI

/// The two lines under the road list: how far the drive is in a straight line, and the plain statement
/// that this build does not time it.
///
/// ## The one number on this screen
///
/// `ScenicHomeScreen`'s rule is that no number appears that nobody measured - which is why there is no
/// duration anywhere and why there was, until this type, no number at all. A straight line through the
/// pins is the exception the rule permits, because it is computed from verified coordinates by
/// `Handoff.StraightLineDistance` on every launch rather than typed in, and because it is labelled as
/// what it is. It is not the driving distance: the roads between those points are longer than the line
/// through them, always.
///
/// ## Why the timing line is here and not in the caption
///
/// A screen that shows a distance and says nothing about time reads as a screen that forgot the time.
/// The sentence is not an apology and not a promise of a later build's number - it says what this build
/// has, next to the number it does have. The two lines travel together into the clipboard for the same
/// reason (`HandoffFailureCard.clipboardText`): a distance with no qualification beside it is read as
/// an ETA.
///
/// The sentence itself is `HandoffDrive.timingSentence`, per drive, in the Linux target that has a test
/// bundle - this view renders it and owns no copy of it (T-0210, and the pre-review mutant pass's M3a).
///
/// Text styles only, no point size, so both lines grow with Dynamic Type; `fixedSize` vertically so
/// the largest accessibility sizes wrap instead of truncating. `fgMuted` is the token for secondary
/// lines under a title, which is what these are - `primary` is a button fill and never a sentence on
/// `bg` (`DesignTokens`).
struct DriveFacts: View {
    /// Which drive's number this is. `ScenicHomeScreen` owns the selection.
    let drive: HandoffDrive

    /// The straight line, in whole kilometres, computed at first use from the SELECTED drive's own
    /// pins - 112 km for the Skyline loop, 47 km for the Santa Monica Mountains loop.
    ///
    /// A function of the drive rather than a stored string, because the selection changes while the
    /// screen is up and a `static let` would hold whichever drive was default when the type was first
    /// touched. Interpolated rather than written out: if a pin moves, this line moves with it, and
    /// `StraightLineDistanceTests` and `SantaMonicaMountainsChainTests` are what refuse a pin that
    /// moves more than a kilometre without the number being looked at again.
    static func straightLine(for drive: HandoffDrive) -> String {
        "About \(StraightLineDistance.wholeMiles(for: drive)) miles as the crow flies, pin to pin. The roads are longer."
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(Self.straightLine(for: drive))
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.distance")

            // The sentence is `HandoffDrive.timingSentence`, not a literal here: this target has no test
            // bundle and no compiler on the authoring box, and a number typed into a literal on this side
            // ships with every gate green. `Handoff` has a test bundle; the words live there.
            Text(drive.timingSentence)
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.timing")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

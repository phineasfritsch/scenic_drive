import DesignSystem
import Handoff
import SwiftUI

/// What the home sheet adds at `medium` (T-0237, rulings R2-R4): the roads the drive runs, the distance and timing
/// lines (`DriveFacts`, unchanged), and the one caption about the map.
///
/// Every string is read from where it already lived - `DriveCopy.route(for:)`, `DriveFacts`, and the caption the
/// screen resolves from the SAME `style` the map is mounted with (handed in as `caption`, so this view cannot
/// resolve a second style of its own). Nothing here is tappable. Type styles only, no point sizes, and `fixedSize`
/// vertically, so every line wraps with Dynamic Type instead of truncating.
struct DriveDetails: View {
    let drive: HandoffDrive
    let caption: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(DriveCopy.route(for: drive))
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.route")

            DriveFacts(drive: drive)

            // Last and smallest: it says what is UNDER the line (the demo tiles show no roads), which matters to
            // the reader who looks for roads and to nobody else.
            Text(caption)
                .font(.footnote)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.caption")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

import DesignSystem
import ScenicKit
import SwiftUI

/// The End confirm (T-0397 R4, the reference library's Uber #077 rule): "End this drive?", one sentence saying what
/// is lost, the FILLED button is the safe choice ("Keep driving") and the destructive one is red text on a gray
/// tonal fill under it. DriveScreen shows it only on the full (stopped) surface and closes it when the drive moves.
/// The conditions line stays its first row, as on the card it replaces.
struct DriveEndConfirm: View {
    let onKeep: () -> Void
    let onEnd: () -> Void

    static let title = "End this drive?"
    static let sentence = "Your drive stops here."
    static let keep = "Keep driving"
    static let end = "End"

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(PlanPreview.conditions)
                .font(.caption)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("drive.conditions")
            Text(Self.title)
                .font(.title3)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
            Text(Self.sentence)
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
            Button(action: onKeep) {
                Text(Self.keep)
                    .font(.headline)
                    .foregroundStyle(DesignTokens.onPrimary)
                    .frame(maxWidth: .infinity, minHeight: 50)
                    .background(Capsule().fill(DesignTokens.primary))
                    .contentShape(Capsule())
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("drive.confirm.keep")
            Button(action: onEnd) {
                Text(Self.end)
                    .font(.headline)
                    .foregroundStyle(DesignTokens.destructive)
                    .frame(maxWidth: .infinity, minHeight: 50)
                    .background(Capsule().fill(DesignTokens.fgMuted.opacity(0.16)))
                    .contentShape(Capsule())
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("drive.confirm.end")
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(DesignTokens.surface)
    }
}

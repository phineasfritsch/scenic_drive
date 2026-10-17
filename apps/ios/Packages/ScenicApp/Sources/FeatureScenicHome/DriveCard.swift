import DesignSystem
import ScenicKit
import SwiftUI

/// The drive's bottom card (T-0397, the reference library's "Drive / turn-by-turn" 3-4): the conditions line first,
/// full width (R5), then "Arrive h:mm", the minutes and miles left, the estimate caption while the corridor is
/// unlearned (P-SAFE-07), the reroute or rejoin caption and the fresh-route note when the screen hands them in, and
/// one short red End pill (R3). AX3 and up stack everything and the pill goes full width (R7).
///
/// It is handed plain values: DriveScreen reads the drive's state and decides what is passed (P-SAFE-09).
struct DriveCard: View {
    @Environment(\.dynamicTypeSize) private var typeSize

    /// Seconds left on the line being driven; the clock plus these is the arrival.
    let remainingSeconds: Double
    /// "N min · N.N mi".
    let glanceLine: String
    let showsEstimate: Bool
    /// The reroute or rejoin state, or nil.
    let caption: String?
    /// The fresh-route note (full surface only), or nil.
    let note: String?
    let endTitle: String
    /// The End target's minimum height: 60 pt while moving, 44 pt stopped.
    let endMinHeight: Double
    let onEnd: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(PlanPreview.conditions)
                .font(.caption)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityIdentifier("drive.conditions")
            if typeSize >= .accessibility3 {
                VStack(alignment: .leading, spacing: 12) {
                    facts
                    endPill(fullWidth: true)
                }
            } else {
                HStack(alignment: .center, spacing: 16) {
                    facts
                    Spacer(minLength: 0)
                    endPill(fullWidth: false)
                }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(DesignTokens.surface)
    }

    /// Arrival, minutes and miles, the estimate caption, then the caption and note when there are any.
    private var facts: some View {
        VStack(alignment: .leading, spacing: 4) {
            TimelineView(.everyMinute) { context in
                Text("Arrive \(context.date.addingTimeInterval(remainingSeconds), format: .dateTime.hour().minute())")
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundStyle(DesignTokens.fg)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("drive.arrive")
            }
            Text(glanceLine)
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("drive.eta")
            if showsEstimate {
                Text(PlanPreview.estimateBadge)
                    .font(.caption)
                    .foregroundStyle(DesignTokens.fgMuted)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("drive.estimate")
            }
            if let caption {
                Text(caption)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(DesignTokens.fg)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("drive.caption")
            }
            if let note {
                Text(note)
                    .font(.subheadline)
                    .foregroundStyle(DesignTokens.fg)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("drive.note")
            }
        }
    }

    /// The one action: a short red pill, never shorter than `endMinHeight`; full width when stacked.
    private func endPill(fullWidth: Bool) -> some View {
        Button(action: onEnd) {
            Text(endTitle)
                .font(.headline)
                .foregroundStyle(DesignTokens.onPrimary)
                .padding(.horizontal, 28)
                .frame(maxWidth: fullWidth ? .infinity : nil,
                       minHeight: fullWidth ? max(50, endMinHeight) : endMinHeight)
                .frame(minWidth: 88)
                .background(Capsule().fill(DesignTokens.destructive))
                .contentShape(Capsule())
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("drive.end")
    }
}

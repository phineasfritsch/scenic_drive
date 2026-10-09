import DesignSystem
import ScenicKit
import SwiftUI

/// The route preview (T-0294 R6): the line, the ETA against the fastest, the estimate badge, the hazard strip and
/// the persistent conditions line, with the attribution footer in the bottom inset at every detent (P-ATTR-01).
struct PlanPreviewCard: View {
    let preview: PlanPreview
    let destination: String
    /// After Save: what happened, in one line; nil until then, and the Save button is offered (T-0306).
    let saveLine: String?
    let onSave: () -> Void
    let onChangePlace: () -> Void
    /// Starts the drive on this preview (T-0324 R4).
    let onDrive: () -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(destination)
                    .font(.title3)
                    .fontWeight(.semibold)
                    .foregroundStyle(DesignTokens.fg)
                PlanRouteShape(route: preview.route)
                    .stroke(DesignTokens.primary, style: StrokeStyle(lineWidth: 4, lineCap: .round, lineJoin: .round))
                    .frame(height: 180)
                    .accessibilityLabel("Route outline")
                Text(preview.etaLine)
                    .font(.body)
                    .foregroundStyle(DesignTokens.fg)
                if preview.showsEstimateBadge {
                    Text(PlanPreview.estimateBadge)
                        .font(.footnote)
                        .foregroundStyle(DesignTokens.fgMuted)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(Capsule().fill(DesignTokens.surface))
                        .accessibilityIdentifier("plan.estimate")
                }
                hazardStrip
                Text(PlanPreview.conditions)
                    .font(.body)
                    .fontWeight(.semibold)
                    .foregroundStyle(DesignTokens.fg)
                    .accessibilityIdentifier("plan.conditions")
                if let saveLine {
                    Text(saveLine)
                        .font(.subheadline)
                        .foregroundStyle(DesignTokens.fgMuted)
                        .accessibilityIdentifier("plan.saved")
                } else {
                    Button("Save this drive", action: onSave)
                        .accessibilityIdentifier("plan.save")
                }
                Button(action: onDrive) {
                    Label("Start the drive", systemImage: "car.fill")
                        .font(.headline)
                        .foregroundStyle(DesignTokens.onPrimary)
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .background(Capsule().fill(DesignTokens.primary))
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("plan.drive")
                Button("Choose another place", action: onChangePlace)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(20)
        }
        .safeAreaInset(edge: .bottom) {
            AttributionFooter(text: PlanPreview.attribution)
        }
    }

    @ViewBuilder private var hazardStrip: some View {
        // T-0339: every word on the strip comes from HazardCopy's closed table - never a raw kind or value.
        let lines = HazardCopy.lines(for: preview)
        if lines.isEmpty {
            Text(HazardCopy.noneFlagged)
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fgMuted)
        } else {
            VStack(alignment: .leading, spacing: 6) {
                ForEach(Array(lines.enumerated()), id: \.offset) { _, line in
                    Label(line, systemImage: "exclamationmark.triangle.fill")
                        .font(.subheadline)
                        .foregroundStyle(DesignTokens.fg)
                        .labelStyle(.titleAndIcon)
                }
            }
            .accessibilityIdentifier("plan.hazards")
        }
    }
}

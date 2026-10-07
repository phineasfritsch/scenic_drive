import DesignSystem
import ScenicKit
import SwiftUI

/// The route preview (T-0294 R6): the line, the ETA against the fastest, the estimate badge, the hazard strip and
/// the persistent conditions line, with the attribution footer in the bottom inset at every detent (P-ATTR-01).
struct PlanPreviewCard: View {
    let preview: PlanPreview
    let destination: String
    let onChangePlace: () -> Void

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
        if preview.hazards.isEmpty {
            Text("Nothing unpaved or restricted is flagged on this route.")
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fgMuted)
        } else {
            VStack(alignment: .leading, spacing: 6) {
                ForEach(Array(preview.hazards.enumerated()), id: \.offset) { _, run in
                    Text("\(run.kind): \(run.value)")
                        .font(.subheadline)
                        .foregroundStyle(DesignTokens.fg)
                }
            }
            .accessibilityIdentifier("plan.hazards")
        }
    }
}

import DesignSystem
import ScenicKit
import SwiftUI

/// The route preview (T-0294 R6, laid out by T-0396): the destination as the title with a "..." menu, the ETA and
/// distance with the estimate badge as a tag on it, the why line, the one hazard row, then Start and Save with the
/// persistent conditions line directly under Start, and the attribution footer in the bottom inset (P-ATTR-01).
struct PlanPreviewCard: View {
    let preview: PlanPreview
    let destination: String
    /// After Save: what happened, in one line; nil until then, and the Save button is offered (T-0306).
    let saveLine: String?
    let onSave: () -> Void
    let onChangePlace: () -> Void
    /// Starts the drive on this preview (T-0324 R4).
    let onDrive: () -> Void
    /// T-0396 R8: the loop and road-trip doors, moved off the visible sheet into the "..." menu.
    let onLoop: () -> Void
    let onTrip: () -> Void
    /// T-0396 R6: whether "+N more" has opened the rest of the hazard lines in place.
    @State private var showsAllHazards = false
    @Environment(\.planMoments) private var moments

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                titleRow
                etaRow
                Text(preview.whyLine)
                    .font(.subheadline)
                    .foregroundStyle(DesignTokens.fgMuted)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("plan.why")
                hazardStrip
                PlanPreviewActions(saveLine: saveLine, onDrive: onDrive, onSave: onSave)
                    .padding(.top, 12)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
        }
        .safeAreaInset(edge: .bottom) {
            AttributionFooter(text: PlanPreview.attribution)
                .background(.bar)
        }
        .onAppear { moments?.report(.planPreviewOnScreen) }
    }

    private var titleRow: some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text(destination)
                .font(.title3)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityAddTraits(.isHeader)
            Menu {
                Button("Choose another place", systemImage: "mappin.and.ellipse", action: onChangePlace)
                Button("Just drive a loop", systemImage: "arrow.triangle.capsulepath", action: onLoop)
                Button("Plan a road trip", systemImage: "map", action: onTrip)
            } label: {
                Image(systemName: "ellipsis.circle")
                    .font(.title3)
                    .foregroundStyle(DesignTokens.primary)
                    .frame(minWidth: 44, minHeight: 44)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel("More options")
            .accessibilityIdentifier("plan.more")
        }
    }

    /// "55 min (14 mi)" with the estimate tag on the same line; under the number when the line does not fit.
    private var etaRow: some View {
        ViewThatFits(in: .horizontal) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                etaText
                estimateTag
            }
            VStack(alignment: .leading, spacing: 6) {
                etaText
                estimateTag
            }
        }
    }

    private var etaText: Text {
        let hero = Text(preview.etaHero).fontWeight(.semibold).foregroundStyle(DesignTokens.fg)
        let distance = preview.distanceLabel.map { Text(" " + $0).foregroundStyle(DesignTokens.fgMuted) }
        return (distance.map { hero + $0 } ?? hero).font(.title2)
    }

    @ViewBuilder private var estimateTag: some View {
        if preview.showsEstimateBadge {
            Text(PlanPreview.estimateBadge)
                .font(.caption)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(DesignTokens.fgMuted.opacity(0.14)))
                .accessibilityIdentifier("plan.estimate")
        }
    }

    @ViewBuilder private var hazardStrip: some View {
        // T-0339: every word on the strip comes from HazardCopy's closed table - never a raw kind or value.
        let lines = HazardCopy.lines(for: preview)
        if let first = lines.first {
            VStack(alignment: .leading, spacing: 6) {
                ForEach(Array((showsAllHazards ? lines : [first]).enumerated()), id: \.offset) { _, line in
                    hazardRow(line)
                }
                if lines.count > 1 && !showsAllHazards {
                    Button("+\(lines.count - 1) more") { showsAllHazards = true }
                        .font(.subheadline)
                        .foregroundStyle(DesignTokens.primary)
                        .frame(minHeight: 44)
                        .contentShape(Rectangle())
                        .accessibilityIdentifier("plan.hazardsMore")
                }
            }
            .accessibilityIdentifier("plan.hazards")
        }
    }

    private func hazardRow(_ line: String) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(DesignTokens.hazard)
                .accessibilityHidden(true)
            Text(line)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
        }
        .font(.subheadline)
        .accessibilityElement(children: .combine)
    }
}

import DesignSystem
import ScenicKit
import SwiftUI

/// The preview's action block (T-0396 R8, R9): "Start the drive" filled and "Save" tonal, 50pt capsules 8pt apart,
/// with the persistent conditions line (P-SAFE-03) directly under Start at every Dynamic Type size - under the pair
/// at default sizes; at accessibility sizes the stack is Start, the line, then Save, all full width.
struct PlanPreviewActions: View {
    /// After Save: what happened, in one line, in the Save slot; nil until then (T-0306).
    let saveLine: String?
    let onDrive: () -> Void
    let onSave: () -> Void
    @Environment(\.dynamicTypeSize) private var typeSize

    var body: some View {
        if typeSize.isAccessibilitySize {
            VStack(alignment: .leading, spacing: 8) {
                start
                conditions
                save
            }
        } else {
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    start
                    save
                        .fixedSize(horizontal: true, vertical: false)
                }
                conditions
            }
        }
    }

    private var start: some View {
        Button(action: onDrive) {
            Label("Start the drive", systemImage: "car.fill")
                .font(.headline)
                .foregroundStyle(DesignTokens.onPrimary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 16)
                .frame(maxWidth: .infinity, minHeight: 50)
                .background(Capsule().fill(DesignTokens.primary))
                .contentShape(Capsule())
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("plan.drive")
    }

    @ViewBuilder private var save: some View {
        if let saveLine {
            Text(saveLine)
                .font(.footnote)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .frame(minHeight: 50)
                .accessibilityIdentifier("plan.saved")
        } else {
            Button(action: onSave) {
                Label("Save", systemImage: "bookmark")
                    .font(.headline)
                    .foregroundStyle(DesignTokens.primary)
                    .padding(.horizontal, 20)
                    .frame(maxWidth: typeSize.isAccessibilitySize ? .infinity : nil, minHeight: 50)
                    .background(Capsule().fill(DesignTokens.primary.opacity(0.14)))
                    .contentShape(Capsule())
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("plan.save")
        }
    }

    private var conditions: some View {
        Text(PlanPreview.conditions)
            .font(.footnote)
            .foregroundStyle(DesignTokens.fgMuted)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityIdentifier("plan.conditions")
    }
}

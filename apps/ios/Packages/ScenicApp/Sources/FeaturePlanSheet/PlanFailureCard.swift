import DesignSystem
import ScenicKit
import SwiftUI

/// A failed plan: its one copy line and its one action (T-0294 R5).
struct PlanFailureCard: View {
    let copy: PlanFailureCopy
    let onAction: (PlanFailureAction) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(copy.line)
                .font(.body)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("plan.failure")
            Button {
                onAction(copy.action)
            } label: {
                Text(copy.action.title)
                    .font(.headline)
                    .foregroundStyle(DesignTokens.onPrimary)
                    .frame(maxWidth: .infinity, minHeight: 44)
                    .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(DesignTokens.primary))
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("plan.failure.action")
            Spacer(minLength: 0)
        }
        .padding(20)
    }
}

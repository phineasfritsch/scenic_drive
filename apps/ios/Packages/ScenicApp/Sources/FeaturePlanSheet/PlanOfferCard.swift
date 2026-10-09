import DesignSystem
import ScenicKit
import SwiftUI

/// A nothing_pretty answer and its ways on (T-0334): the line naming the minutes asked, one button per offer the
/// answer made - each names the minutes it asks for and is ONE fresh plan through the sheet's gate - and the
/// fallback action.
struct PlanOfferCard: View {
    let copy: PlanOfferCopy
    let onMoreTime: () -> Void
    let onBackRoads: () -> Void
    let onAction: (PlanFailureAction) -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(copy.line)
                    .font(.body)
                    .foregroundStyle(DesignTokens.fg)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("plan.offer")
                if let moreTime = copy.moreTime {
                    filled(moreTime, action: onMoreTime).accessibilityIdentifier("plan.offer.moreTime")
                }
                if let backRoads = copy.backRoads {
                    filled(backRoads, action: onBackRoads).accessibilityIdentifier("plan.offer.backRoads")
                }
            }
            .padding(20)
        }
        .safeAreaInset(edge: .bottom) {
            PlanCardExit(copy.action.title) { onAction(copy.action) }
                .accessibilityIdentifier("plan.offer.action")
        }
    }

    private func filled(_ title: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.headline)
                .foregroundStyle(DesignTokens.onPrimary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(DesignTokens.primary))
        }
        .buttonStyle(.plain)
    }
}

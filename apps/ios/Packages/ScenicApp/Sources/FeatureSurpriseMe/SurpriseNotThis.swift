import DesignSystem
import ScenicKit
import SwiftUI

/// The card's four "not this" buttons (T-0273 R6), one per SurpriseFeedback.Reason, 44 pt each, two by two.
/// T-0398: secondary actions, so tonal capsules (a pale fill of the accent, no outline) under the one filled
/// primary; the label stays `fg`, because the accent on white is below 4.5:1 at this size.
struct SurpriseNotThis: View {
    let onReason: @MainActor (SurpriseFeedback.Reason) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Not this one?")
                .font(.footnote.weight(.semibold))
                .foregroundStyle(DesignTokens.fgMuted)
            Grid(horizontalSpacing: 8, verticalSpacing: 8) {
                GridRow {
                    button(.tooFar)
                    button(.notMyThing)
                }
                GridRow {
                    button(.beenThere)
                    button(.wrongTime)
                }
            }
        }
    }

    private func button(_ reason: SurpriseFeedback.Reason) -> some View {
        Button {
            onReason(reason)
        } label: {
            Text(Self.label(reason))
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(DesignTokens.fg)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(Capsule(style: .continuous).fill(DesignTokens.primary.opacity(0.14)))
                .contentShape(Capsule(style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Not this: \(Self.label(reason))")
        .accessibilityIdentifier("surprise.notThis.\(reason.rawValue)")
    }

    static func label(_ reason: SurpriseFeedback.Reason) -> String {
        switch reason {
        case .tooFar: return "Too far"
        case .notMyThing: return "Not my thing"
        case .beenThere: return "Been there"
        case .wrongTime: return "Wrong time"
        }
    }
}

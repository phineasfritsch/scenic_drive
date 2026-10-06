import DesignSystem
import ScenicKit
import SwiftUI

/// The card's four "not this" buttons (T-0273 R6), one per SurpriseFeedback.Reason, 44 pt each, two by two.
struct SurpriseNotThis: View {
    let onReason: @MainActor (SurpriseFeedback.Reason) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Not this one?")
                .font(.caption.weight(.semibold))
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
                .font(.footnote.weight(.medium))
                .foregroundStyle(DesignTokens.fg)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(
                    RoundedRectangle(cornerRadius: 10, style: .continuous)
                        .strokeBorder(DesignTokens.border, lineWidth: 1)
                )
                .contentShape(Rectangle())
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

import DesignSystem
import SwiftUI

/// Surprise (T-0408): a 56 pt circle on the map's right edge, riding the top of the credit and the sheet, under the
/// gear (Google Maps #001's right-edge column; Apple Maps #008). Tonal - `surface` ground, `primary` sparkle, a
/// `border` hairline - so the sheet's handoff button stays the only filled control. A tap shows or hides the
/// Surprise card under the chip row.
struct SurpriseToggle: View {
    @Binding var isShowing: Bool

    let onToggle: () -> Void

    var body: some View {
        Button {
            onToggle()
            isShowing.toggle()
        } label: {
            Image(systemName: isShowing ? "sparkles.rectangle.stack.fill" : "sparkles")
                .font(.title3.weight(.semibold))
                .foregroundStyle(DesignTokens.primary)
                .frame(width: 56, height: 56)
                .background(Circle().fill(DesignTokens.surface))
                .overlay(Circle().strokeBorder(DesignTokens.border, lineWidth: 1))
                .shadow(color: Color.black.opacity(0.18), radius: 6, x: 0, y: 2)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Surprise me")
        .accessibilityAddTraits(isShowing ? .isSelected : [])
        .accessibilityIdentifier("home.surprise")
    }
}

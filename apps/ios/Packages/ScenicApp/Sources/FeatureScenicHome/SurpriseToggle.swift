import DesignSystem
import SwiftUI

/// The chip band's 44 pt "Surprise me" square (T-0273 R5): opens and closes the card under the drive picker. Its own
/// file so ScenicHomeScreen stays under CLAUDE.md's 300-line cap.
struct SurpriseToggle: View {
    @Binding var isShowing: Bool

    let onToggle: () -> Void

    var body: some View {
        Button {
            onToggle()
            isShowing.toggle()
        } label: {
            Image(systemName: isShowing ? "sparkles.rectangle.stack.fill" : "sparkles")
                .font(.body.weight(.semibold))
                .foregroundStyle(DesignTokens.primary)
                .frame(width: 44, height: 44)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(DesignTokens.surface)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .strokeBorder(DesignTokens.border, lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Surprise me")
        .accessibilityAddTraits(isShowing ? .isSelected : [])
        .accessibilityIdentifier("home.surprise")
    }
}

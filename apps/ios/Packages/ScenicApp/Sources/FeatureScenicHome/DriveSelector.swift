import DesignSystem
import Handoff
import SwiftUI

/// The home's ONE chip row (T-0408, Google Maps #001): the drives, and nothing else - no Surprise, no gear - as
/// single-line capsules in a horizontal scroll under the Plan field.
///
/// ## The look
///
/// Each chip is a 36 pt capsule inside a 44 pt hit area. Its name never wraps: one line, and a name longer than the
/// chip's widest is cut with an ellipsis, so no word ever breaks across lines ('West-wood' at AX5 was T-0404's shot).
/// The selected chip is tonal - `surface` with a 2 pt `primary` border and semibold - not a `primary` fill, so the
/// sheet's handoff button stays the only filled control on the screen. Colour is never the only signal: VoiceOver
/// hears `isSelected`.
///
/// ## Accessibility sizes
///
/// At AX1+ the screen does not build this row; the same drives are `DriveRows`, stacked at the top of the sheet.
/// `order` is the one table both read, so the two can never list different drives.
struct DriveSelector: View {
    /// Which drive the home shows.
    @Binding var selection: HandoffDrive

    /// The drives in the order the home lists them, each with the identifier its chip carries.
    static let order: [(drive: HandoffDrive, identifier: String)] = [
        (.saddlePeak, "home.drive.saddlePeak"),
        (.santaMonicaMountains, "home.drive.la"),
        (.skyline, "home.drive.skyline"),
    ]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(Self.order.indices, id: \.self) { index in
                    chip(for: Self.order[index].drive, identifier: Self.order[index].identifier)
                }
            }
            .padding(.horizontal, 16)
        }
        .scrollClipDisabled()
        .accessibilityIdentifier("home.drivePicker")
    }

    private func chip(for drive: HandoffDrive, identifier: String) -> some View {
        let isSelected = selection == drive
        return Button {
            selection = drive
        } label: {
            Text(DriveCopy.shortName(for: drive))
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundStyle(DesignTokens.fg)
                .lineLimit(1)
                .truncationMode(.tail)
                .frame(maxWidth: 220)
                .padding(.horizontal, 14)
                .frame(height: 36)
                .background(Capsule().fill(DesignTokens.surface))
                .overlay(
                    Capsule().strokeBorder(isSelected ? DesignTokens.primary : DesignTokens.border,
                                           lineWidth: isSelected ? 2 : 1)
                )
                .shadow(color: Color.black.opacity(0.12), radius: 4, x: 0, y: 1)
                .frame(minHeight: 44)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        // Stated rather than left to the default: a selected chip is not just a differently drawn one, and
        // VoiceOver has to say which drive is on screen. Colour alone is never the signal.
        .accessibilityAddTraits(isSelected ? [.isButton, .isSelected] : .isButton)
        .accessibilityIdentifier(identifier)
    }
}

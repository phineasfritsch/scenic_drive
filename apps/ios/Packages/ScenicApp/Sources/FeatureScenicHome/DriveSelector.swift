import DesignSystem
import Handoff
import SwiftUI

/// Which of the two hard-coded drives the screen is showing: two rows in one band, above the title.
///
/// ## Why two buttons and not `Picker(.segmented)`
///
/// A segmented control renders with `UISegmentedControl`'s own colours - the system tint, the system
/// selected-segment fill - and those are not `DesignTokens`. The one rule this package holds about
/// colour is that every surface states its contrast through that table, on both appearances; a control
/// that paints itself is a hole in it that no review of this file would see. Two buttons cost eleven
/// lines and are `primary`/`onPrimary` when selected, `surface`/`fg` with a `border` hairline when
/// not, which is the same pairing `GatedHandoffButton` and `HandoffFailureCard` already use.
///
/// ## Targets and type
///
/// Each row is `frame(maxWidth: .infinity, minHeight: 44)` with the label INSIDE the frame, so the
/// 44 pt target holds at the smallest Dynamic Type setting rather than being sized by the text -
/// `HandoffFailureCard`'s two buttons are built the same way and for the same reason. Text styles
/// only, no point sizes, and `fixedSize` vertically so accessibility sizes wrap instead of truncating.
///
/// The identifiers are `home.drive.skyline` and `home.drive.la`, one per row, stable whatever the
/// label says, so a UI test selects a drive by what it is and not by the words on it.
///
/// - Note: never rendered and never tapped on a device. This package has no test target and no
///   simulator on the authoring box; the compiler is the only proof this file has.
struct DriveSelector: View {
    /// The current selection, owned by `ScenicHomeScreen`.
    @Binding var selection: HandoffDrive

    var body: some View {
        HStack(spacing: 8) {
            row(for: .santaMonicaMountains, identifier: "home.drive.la")
            row(for: .skyline, identifier: "home.drive.skyline")
        }
        .accessibilityIdentifier("home.drivePicker")
    }

    /// One row. The LA drive is written first because it is the default (`HandoffDrive.defaultDrive`)
    /// and the owner's; reading order is the one signal a row's position carries.
    private func row(for drive: HandoffDrive, identifier: String) -> some View {
        let isSelected = selection == drive
        return Button {
            selection = drive
        } label: {
            Text(DriveCopy.shortName(for: drive))
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundStyle(isSelected ? DesignTokens.onPrimary : DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(isSelected ? DesignTokens.primary : DesignTokens.surface)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .strokeBorder(DesignTokens.border, lineWidth: isSelected ? 0 : 1)
                )
        }
        .buttonStyle(.plain)
        // Stated rather than left to the default: a selected row is not just a differently coloured
        // one, and VoiceOver has to say which drive is on screen. Colour alone is never the signal.
        .accessibilityAddTraits(isSelected ? [.isButton, .isSelected] : .isButton)
        .accessibilityIdentifier(identifier)
    }
}

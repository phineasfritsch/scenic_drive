import DesignSystem
import Foundation
import Handoff
import SwiftUI

/// The drive's menu as extra-minutes chips (T-0246): one chip per row `ops/plan --menu` printed - 'Fastest',
/// '+13 min', '+18 min' - with the good road each one buys beneath its minutes. Tapping one selects that row: the
/// map redraws it in the route colour with the others muted, and the button hands ITS URL to Apple Maps.
///
/// ## The words
///
/// Calm, the owner's positioning ('calm adventure'; 'Take the long way. Unwind.'): minutes and kilometres,
/// nothing that sells speed or thrill. Every string is `DriveMenuRow`'s, in the Linux target, where
/// `SaddlePeakMenuBundleTests` binds it to the CLI - the minutes are the row's extra rounded UP, so a chip never
/// promises less time than the route takes (P-SAFE-04).
///
/// ## The look
///
/// Each chip is at least 44 pt tall on a `surface` ground. The selected chip carries a 2 pt `route` border -
/// the colour of the line it draws - and semibold minutes; the others a `border` hairline. Not a `primary`
/// fill: the drive picker above and the button below already carry that colour, and colour is never the only
/// signal - VoiceOver hears `isSelected`.
struct DriveMenuChips: View {
    let menu: DriveMenu
    @Binding var selection: Int?

    /// The launch argument that selects a row before any tap (`-menuRow 0` for 'Fastest'), for the screenshot
    /// workflow; absent or not a row, the menu's own default.
    static let launchArgumentKey = "menuRow"

    static var rowAtLaunch: Int? {
        UserDefaults.standard.string(forKey: launchArgumentKey).flatMap { Int($0) }
    }

    var body: some View {
        HStack(spacing: 8) {
            ForEach(menu.rows.indices, id: \.self) { index in
                chip(index)
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("home.menu")
    }

    private func chip(_ index: Int) -> some View {
        let row = menu.rows[index]
        let isSelected = menu.index(selected: selection) == index
        return Button {
            selection = index
        } label: {
            VStack(spacing: 2) {
                Text(row.chipLabel)
                    .font(.subheadline)
                    .fontWeight(isSelected ? .semibold : .regular)
                    .foregroundStyle(DesignTokens.fg)
                Text(row.goodRoadLabel)
                    .font(.caption2)
                    .foregroundStyle(DesignTokens.fgMuted)
            }
            .multilineTextAlignment(.center)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.vertical, 6)
            .padding(.horizontal, 4)
            .frame(maxWidth: .infinity, minHeight: 44)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(DesignTokens.surface)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .strokeBorder(isSelected ? DesignTokens.route : DesignTokens.border, lineWidth: isSelected ? 2 : 1)
            )
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(row.chipLabel), \(row.goodRoadLabel)")
        .accessibilityAddTraits(isSelected ? [.isButton, .isSelected] : .isButton)
        .accessibilityIdentifier("home.menu.row\(index)")
    }
}

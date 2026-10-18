import DesignSystem
import Foundation
import Handoff
import ScenicKit
import SwiftUI

/// The drive's menu (T-0246) as OPTION ROWS (T-0408, library "Home" item 12): one row per row `ops/plan --menu`
/// printed - 'Fastest', '+13 min', '+18 min' at .title3, the roads it adds over the fastest under it - and one
/// estimate caption under the rows. Tapping a row selects it: the map redraws it in the route colour with the
/// others muted, and the button hands ITS URL to Apple Maps. The type keeps its T-0246 name; it draws rows now.
///
/// ## The words
///
/// Calm, the owner's positioning: minutes and road names, nothing that sells speed or thrill. The minutes are
/// `DriveMenuRow.chipLabel` - the row's extra rounded UP, so a row never promises less time than the route takes
/// (P-SAFE-04). The 'km good road' label is gone: every option said it, so it told nobody anything. The "via" line
/// is `OptionVia` (ScenicKit, tested). Home holds no learned samples for any corridor, so the caption
/// `PlanPreview.estimateBadge` is always shown - once, for the menu, not once per row.
///
/// ## The look
///
/// Rows at least 44 pt tall on the sheet's `bg`, `border` hairlines between them. The selected row carries a filled
/// check and semibold minutes; colour is never the only signal - VoiceOver hears `isSelected`.
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
        VStack(alignment: .leading, spacing: 0) {
            ForEach(menu.rows.indices, id: \.self) { index in
                if index > 0 {
                    Rectangle().fill(DesignTokens.border).frame(height: 1)
                }
                option(index)
            }
            Text(PlanPreview.estimateBadge)
                .font(.footnote)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.top, 6)
                .accessibilityIdentifier("home.menu.estimate")
        }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("home.menu")
    }

    /// The roads the menu's fastest row drives: what every other row's "via" is measured against.
    private var fastestRoads: [String] {
        (menu.rows.first { $0.displayedMinutes == 0 } ?? menu.rows[0]).roads
    }

    private func option(_ index: Int) -> some View {
        let row = menu.rows[index]
        let isSelected = menu.index(selected: selection) == index
        let via = OptionVia.line(roads: row.roads, fastest: fastestRoads)
        return Button {
            selection = index
        } label: {
            HStack(alignment: .center, spacing: 12) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(row.chipLabel)
                        .font(.title3)
                        .fontWeight(isSelected ? .semibold : .regular)
                        .foregroundStyle(DesignTokens.fg)
                    if !via.isEmpty {
                        Text(via)
                            .font(.subheadline)
                            .foregroundStyle(DesignTokens.fgMuted)
                            .lineLimit(2)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.title3)
                    .foregroundStyle(isSelected ? DesignTokens.fg : DesignTokens.fgMuted)
                    .accessibilityHidden(true)
            }
            .padding(.vertical, 8)
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel(via.isEmpty ? row.chipLabel : "\(row.chipLabel), \(via)")
        .accessibilityAddTraits(isSelected ? [.isButton, .isSelected] : .isButton)
        .accessibilityIdentifier("home.menu.row\(index)")
    }
}

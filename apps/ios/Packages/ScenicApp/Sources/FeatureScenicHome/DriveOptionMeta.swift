import DesignSystem
import Handoff
import ScenicKit
import SwiftUI

/// The collapsed sheet's one summary line for the selected menu row (T-0408; AllTrails #025, library "Home" item
/// 9): '+18 min · via Fernwood Pacific Drive · Tuna Canyon Road · +3 more'. The minutes come first - they are the
/// price of the scenic choice - then the roads this option adds over the fastest (`OptionVia`). No kilometres: the
/// row carries only its 'good road' length, which is not the drive's distance. The rows themselves, and the
/// estimate caption, are one detent up (`DriveMenuChips`).
struct DriveOptionMeta: View {
    let menu: DriveMenu
    let row: DriveMenuRow

    var body: some View {
        Text(line)
            .font(.subheadline)
            .foregroundStyle(DesignTokens.fgMuted)
            .lineLimit(2)
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityIdentifier("home.meta")
    }

    private var line: String {
        let fastest = menu.rows.first { $0.displayedMinutes == 0 } ?? menu.rows[0]
        let via = OptionVia.line(roads: row.roads, fastest: fastest.roads)
        return via.isEmpty ? row.chipLabel : "\(row.chipLabel) · \(via)"
    }
}

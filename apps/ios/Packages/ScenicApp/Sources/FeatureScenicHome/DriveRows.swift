import DesignSystem
import Handoff
import ScenicKit
import SwiftUI

/// The drives as stacked rows at the top of the sheet, at accessibility text sizes only (T-0408; Waze #062,
/// Transit #016). A chip row that wraps at AX5 breaks names mid-word; a full-width row does not.
///
/// Each row: the drive's short name and "via <road>" on the left; on the right the drive's default menu row's
/// extra minutes as a .title2 numeral over a .caption "min" - a number scans down a list faster than a label.
/// The numbers are the bundled menus' (`DriveRoute.menu`), read in `.task` because that touches the file system,
/// never in `body`. A drive without a menu shows its name only: no number nobody measured.
///
/// The drives and their order are `DriveSelector.order`, the same table the chip row reads.
struct DriveRows: View {
    @Binding var selection: HandoffDrive

    /// Each drive's bundled menu, or nothing for a drive without one; empty until `.task` has read them.
    @State private var menus: [HandoffDrive: DriveMenu] = [:]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(DriveSelector.order.indices, id: \.self) { index in
                if index > 0 {
                    Rectangle().fill(DesignTokens.border).frame(height: 1)
                }
                row(for: DriveSelector.order[index].drive)
            }
        }
        .task {
            for entry in DriveSelector.order {
                menus[entry.drive] = DriveRoute.menu(for: entry.drive)
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("home.driveRows")
    }

    private func row(for drive: HandoffDrive) -> some View {
        let isSelected = selection == drive
        let pick = menus[drive].map { $0.row(selected: nil) }
        let fastest = menus[drive].flatMap { menu in menu.rows.first { $0.displayedMinutes == 0 } }
        let via = pick.map { OptionVia.line(roads: $0.roads, fastest: fastest?.roads ?? []) } ?? ""
        return Button {
            selection = drive
        } label: {
            HStack(alignment: .center, spacing: 12) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(DriveCopy.shortName(for: drive))
                        .font(.headline)
                        .fontWeight(isSelected ? .bold : .semibold)
                        .foregroundStyle(DesignTokens.fg)
                        .fixedSize(horizontal: false, vertical: true)
                    if !via.isEmpty {
                        Text(via)
                            .font(.subheadline)
                            .foregroundStyle(DesignTokens.fgMuted)
                            .lineLimit(2)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                if let pick, pick.displayedMinutes > 0 {
                    VStack(alignment: .trailing, spacing: 0) {
                        Text("+\(pick.displayedMinutes)")
                            .font(.title2)
                            .fontWeight(.semibold)
                            .monospacedDigit()
                            .foregroundStyle(DesignTokens.fg)
                        Text("min")
                            .font(.caption)
                            .foregroundStyle(DesignTokens.fgMuted)
                    }
                    .fixedSize()
                }
            }
            .padding(.vertical, 8)
            .padding(.leading, 10)
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .overlay(alignment: .leading) {
                Capsule().fill(isSelected ? DesignTokens.primary : Color.clear).frame(width: 4)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(isSelected ? [.isButton, .isSelected] : .isButton)
        .accessibilityIdentifier("home.driveRow.\(drive.rawValue)")
    }
}

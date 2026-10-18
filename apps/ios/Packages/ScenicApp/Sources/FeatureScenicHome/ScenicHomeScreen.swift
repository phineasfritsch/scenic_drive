import DesignSystem
import Handoff
import MapAdapter
import ScenicKit
import SwiftUI

/// The home, map-first (T-0237, T-0408): the map fills the screen, one chip row of drives under the Plan field, a
/// right-edge column (gear, Surprise), and a sheet that cannot be dismissed carries the drive.
///
/// ## The credit sits on the map, above the sheet, at every detent (P-ATTR-01)
///
/// The credit pill and `HomeSheet` are the only two children of one `VStack(spacing: 0)`, pill first: the pill is
/// laid out on the map directly above the sheet's top edge whatever the detent and in the middle of a drag, in the
/// lower-right corner the plan reserves for attribution. Limb (h) of `ops/lib/check-map-attribution` reads those
/// lines whole. Why an overlay and not a system sheet is `HomeSheet`'s note (ruling R1 in T-0237's Log).
///
/// ## The camera follows the detent
///
/// The chip band's bottom and the credit band's top are measured in the window's coordinates and handed to
/// `MapView` as the two edges the map is covered past; its camera fits the drawn line between them at both detents.
///
/// ## Three drives, one screen (T-0178, T-0236)
///
/// `selectedDrive` is the one value the title, the road line, the map centre, the caption and the handoff URL read.
/// Saddle Peak is the default, unconditionally (`HandoffDrive.defaultDrive` carries the ruling).
///
/// ## The safety gate (P-SAFE-03)
///
/// CLAUDE.md: *"The safety disclaimer gates the first plan and stays visible on the route screen."* Both halves land
/// here: the first tap on the handoff opens `SafetyDisclaimer` instead of leaving, and `Copy.conditions` is in the
/// sheet at both detents, always. The guard itself is inside `GatedHandoffButton`; `ops/lib/check-safety-disclaimer`
/// says what a source-level check can and cannot decide about it.
public struct ScenicHomeScreen: View {
    /// The basemap ACTUALLY on screen, named once so the tiles, the caption and the credit cannot drift apart.
    /// Resolved from `.task`/`.onChange`, never in `body`: `DriveBasemap.resolve` touches the file system.
    @State private var style = MapStyle.maplibreDemoTiles

    /// The selected drive's road line, or `nil` (T-0236), resolved beside `style` for the same reason.
    @State private var route: MapRoute?

    /// SwiftUI's `ColorScheme`, converted to `MapAppearance` at this boundary (`MapAdapter` knows no environment).
    @Environment(\.colorScheme) private var colorScheme

    /// Whether the safety disclaimer has been accepted on THIS DEVICE: `UserDefaults`, nothing leaves the phone.
    /// The key is versioned so that changing what the user is asked to acknowledge can ask again.
    @AppStorage("safety.disclaimer.acknowledged.v1")
    private var isSafetyDisclaimerAcknowledged = false

    /// Whether the disclaimer sheet is up - where the sheet is right now, not what the user agreed to.
    @State private var isShowingDisclaimer = false

    /// Whatever `Handoff` refused, if it refused, so the button can say what went wrong.
    @State private var handoffFailure: String?

    /// Which drive is on screen. `@State`, not `@AppStorage`: a relaunch is back on the default, the owner's drive.
    @State private var selectedDrive = HandoffDrive.defaultDrive

    /// The selected drive's menu (T-0246), or `nil` for a drive without one - resolved beside `route`.
    @State private var menu: DriveMenu?

    /// Which menu row is selected; `nil` is the menu's own default row. A launch argument can pick one.
    @State private var menuRow = DriveMenuChips.rowAtLaunch

    /// How much of the drive the sheet shows. A launch argument can pick the first one (`HomeSheetDetent`).
    @State private var sheetDetent = HomeSheetDetent.atLaunch

    /// The user's own text size, read ABOVE the body's xxxLarge cap (T-0378 R2) and handed back to the disclaimer.
    @Environment(\.dynamicTypeSize) private var userTypeSize
    /// The chip band's bottom and the credit band's top, in window points: the two edges `MapView` converts into its
    /// own; zero until measured. The map's own height is NOT measured (SwiftUI reports the safe-area height).
    @State private var isShowingSurprise = SurpriseSlot.atLaunch

    @State private var surpriseFailure: String?
    @Environment(\.homeMoments) private var moments
    @State private var chipBandBottom: CGFloat = 0
    @State private var creditBandTop: CGFloat = 0

    /// The settings action (T-0271): a callback the app shell supplies, so this target never imports Entitlements -
    /// feature targets never import each other (CLAUDE.md), and the shell is where Settings and the paywall compose.
    private let onSettings: () -> Void

    private let surprise: SurpriseSlot.Builder
    private let surpriseGate: SurpriseGate

    public init(onSettings: @escaping () -> Void, surpriseGate: SurpriseGate, surprise: @escaping SurpriseSlot.Builder) { self.onSettings = onSettings; self.surpriseGate = surpriseGate; self.surprise = surprise }

    public var body: some View {
        ZStack(alignment: .top) {
            MapView(
                styleURL: style.url,
                // Centred on the SELECTED route's own destination: one verified coordinate per drive.
                centerLatitude: SkylineHandoff.destination(for: selectedDrive).latitude,
                centerLongitude: SkylineHandoff.destination(for: selectedDrive).longitude,
                zoomLevel: 8.5,
                coveredAboveY: chipBandBottom,
                coveredBelowY: creditBandTop,
                // With a line, the camera fits it between the two covered edges; without one, the centre above.
                route: route
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                chips

                Spacer(minLength: 0)

                mapControls

                // The credit for everything drawn - the RESOLVED style's credit for the tiles, then the drawn line's
                // data credit, composed from the same `style` and `route` the map is handed - directly above the
                // sheet. Nothing between them, nothing over either: limb (h) of check-map-attribution.
                VStack(spacing: 0) {
                    AttributionFooter(text: CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit))
                    HomeSheet(detent: $sheetDetent, summary: { sheetSummary }, details: { sheetDetails })
                }
                .onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).minY } action: { creditBandTop = $0 }
            }
        }
        .background(DesignTokens.bg)
        // The three moments the answer can change, and the only three: first appearance, a new drive, light/dark.
        .task { resolveBasemap() }
        .task { if !isSafetyDisclaimerAcknowledged || !VehicleSetting.isChosen { isShowingDisclaimer = true } }
        .onChange(of: selectedDrive) { resolveBasemap() }
        .onChange(of: menuRow) { resolveBasemap() }
        .onChange(of: colorScheme) { resolveBasemap() }
        .sheet(isPresented: $isShowingDisclaimer) {
            SafetyDisclaimer(onAccept: {
                isSafetyDisclaimerAcknowledged = true
                isShowingDisclaimer = false
            })
            .accessibilityIdentifier("home.disclaimer")
            .dynamicTypeSize(userTypeSize)
        }
        .dynamicTypeSize(...HomeTypeSize.cap)
    }

    /// Ask `DriveBasemap` which tiles this drive can have on this device, and keep the answer: the LA drives get the
    /// Protomaps basemap when `la.pmtiles` is on the phone and the demo tiles when it is not (see `DriveBasemap`).
    private func resolveBasemap() {
        menu = DriveRoute.menu(for: selectedDrive)
        route = DriveRoute.resolve(for: selectedDrive, menu: menu, selected: menuRow)
        style = DriveBasemap.resolve(
            for: selectedDrive,
            appearance: colorScheme == .dark ? .dark : .light
        )
    }

    /// The one way out of this app, built in exactly one place. Named, because two things need it: the button in
    /// the sheet and the *Try again* on `HandoffFailureCard`, whose retry goes through the same acknowledgement
    /// gate as the first tap. One construction, one guard, one `SkylineHandoff.open(` in the app - the triple
    /// `ops/lib/check-safety-disclaimer` (P-SAFE-03) decides.
    private var gatedHandoff: GatedHandoffButton {
        GatedHandoffButton(
            isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged,
            drive: selectedDrive,
            row: selectedRow,
            onBlocked: { isShowingDisclaimer = true },
            onFailure: { handoffFailure = $0; if $0 == nil { moments?.report(.driveHandedToAppleMaps) } }
        )
    }

    /// The Surprise card's Apple Maps tap: the SAME gate, a second GatedHandoffButton (T-0273 R4, P-SAFE-03).
    private func openSurprise(_ place: Coordinate) {
        GatedHandoffButton(
            isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged,
            drive: selectedDrive,
            row: nil,
            place: place,
            onBlocked: { isShowingDisclaimer = true },
            onFailure: { surpriseFailure = $0; if $0 == nil { moments?.report(.surpriseHandedToAppleMaps) } }
        ).attempt()
    }

    /// The ONE chip row of drives under the Plan field (T-0408), then the Surprise card when it is open. At AX1+
    /// (`userTypeSize`, read above the body's cap) the row is not built: the drives are `DriveRows` in the sheet.
    /// The band's measured bottom is the map's covered top edge.
    private var chips: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !userTypeSize.isAccessibilitySize {
                DriveSelector(selection: $selectedDrive)
            }
            if isShowingSurprise {
                SurpriseGateSlot(gate: surpriseGate, card: { surprise({ openSurprise($0) }, surpriseFailure) })
                    .padding(.horizontal, 16)
            }
        }
            .padding(.top, 4)
            .onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).maxY } action: { chipBandBottom = $0 }
    }

    /// The right-edge column riding the credit and the sheet (T-0408): the gear, then Surprise. Both tonal circles,
    /// so the sheet's button stays the one filled control. The gear is here until T-0429 puts it in the Plan field.
    private var mapControls: some View {
        VStack(spacing: 10) {
            settingsButton
            SurpriseToggle(isShowing: $isShowingSurprise, onToggle: { surpriseFailure = nil })
        }
        .frame(maxWidth: .infinity, alignment: .trailing)
        .padding(.horizontal, 16)
        .padding(.bottom, 8)
    }

    /// Settings (T-0271): a 44 pt tonal circle (`fg` on `surface`, a `border` hairline) at the top of the right-edge
    /// column; the action is the shell's (`onSettings`).
    private var settingsButton: some View {
        Button(action: onSettings) {
            Image(systemName: "gearshape")
                .font(.body.weight(.semibold))
                .foregroundStyle(DesignTokens.fg)
                .frame(width: 44, height: 44)
                .background(Circle().fill(DesignTokens.surface))
                .overlay(Circle().strokeBorder(DesignTokens.border, lineWidth: 1))
                .shadow(color: Color.black.opacity(0.18), radius: 6, x: 0, y: 2)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Settings")
        .accessibilityIdentifier("home.settings")
    }

    /// The selected menu row (T-0246), or `nil` for a drive without a menu: what the line, the button, the paste
    /// and the road line all read.
    private var selectedRow: DriveMenuRow? {
        menu?.row(selected: menuRow)
    }

    /// The roads the selected row drives (the CLI's), or the drive's own road list when it has no menu.
    private var roadList: String {
        selectedRow?.roadList ?? DriveCopy.route(for: selectedDrive)
    }

    /// The collapsed sheet: the drives as rows at AX sizes, the drive's name, the selected option's one meta line,
    /// a failure card if the handoff refused, the button, and the conditions line directly under it (T-0408).
    @ViewBuilder
    private var sheetSummary: some View {
        PostDriveOpenSlot()
        if userTypeSize.isAccessibilitySize {
            DriveRows(selection: $selectedDrive)
        }

        Text(DriveCopy.title(for: selectedDrive))
            .font(.title3)
            .fontWeight(.semibold)
            .foregroundStyle(DesignTokens.fg)
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityAddTraits(.isHeader)
            .accessibilityIdentifier("home.title")

        if let menu, let selectedRow {
            DriveOptionMeta(menu: menu, row: selectedRow)
        }

        if let handoffFailure {
            HandoffFailureCard(message: handoffFailure,
                               roadList: roadList,
                               drive: selectedDrive,
                               row: selectedRow,
                               onRetry: { gatedHandoff.attempt() })
        }

        gatedHandoff

        conditions
    }

    /// What `medium` adds: the menu's option rows when the drive has one (T-0408), then the details. The caption
    /// reads the resolved `style`: it says what is under the map, the demo basemap on a device with no LA archive.
    private var sheetDetails: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let menu {
                DriveMenuChips(menu: menu, selection: $menuRow)
            }
            DriveDetails(drive: selectedDrive, roads: roadList, caption: DriveCopy.mapCaption(for: selectedDrive, style: style))
        }
    }

    /// The persistent conditions line - the plan's risk table, verbatim, as the mitigation for *sedan onto
    /// dirt/gated/closed road*. In the sheet's collapsed part, so it is on screen at both detents, directly under
    /// the button, whatever the disclaimer has been told. On the sheet's `bg`, where `fgMuted` is a stated pair.
    ///
    /// A text style, so it grows with Dynamic Type; `fixedSize` vertically so the largest sizes wrap rather than
    /// truncate a safety sentence - and the collapsed sheet is as tall as its content, so it grows with it.
    private var conditions: some View {
        Text(Copy.conditions)
            .font(.footnote)
            .foregroundStyle(DesignTokens.fgMuted)
            .frame(maxWidth: .infinity, alignment: .leading)
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityIdentifier("home.conditions")
            // NEVER hidden from accessibility, stated explicitly so that removing it is a visible deletion.
            .accessibilityHidden(false)
    }

    /// The strings that belong to the SCREEN rather than to a drive. A private nested enum, not an `.xcstrings`
    /// catalog: catalogs are serial-only (CLAUDE.md) and there is one language today.
    private enum Copy {
        /// The persistent safety line, from the plan's risk table, word for word - the same sentence the disclaimer
        /// ends on, and the same for every drive, so nobody can edit it away one drive at a time.
        static let conditions = "Conditions change. Verify locally."
    }
}

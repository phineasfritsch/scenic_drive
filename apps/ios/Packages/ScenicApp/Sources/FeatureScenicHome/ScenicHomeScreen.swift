import DesignSystem
import Handoff
import MapAdapter
import ScenicKit
import SwiftUI

/// The walking skeleton's only screen, map-first (T-0237): the map fills the screen, the drive chips float over it
/// below the status bar, and a sheet that cannot be dismissed carries the drive - the title, a line about
/// conditions that never leaves, and one gated button, with the roads and the timing one detent up.
///
/// M1.5 exists to prove the seam, not the product - MapLibre draws on a real phone, `DesignSystem` renders on both
/// appearances, and `Handoff` produces a URL Apple Maps accepts. The map, the credit, the disclaimer and the handoff
/// are the parts that stay when the real surfaces (plan sheet, route preview, hazard strip) arrive in M4.
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
/// `MapView` as the two edges the map is covered past; its camera fits the drawn line between them, and MapLibre's
/// logo and (i) move with them, so the whole route, the logo and the (i) stay on uncovered map at both detents.
///
/// ## Three drives, one screen (T-0178, T-0236)
///
/// `selectedDrive` is the one value the title, the road line, the distance, the map centre, the caption and the
/// handoff URL all read. Saddle Peak is the default; `HandoffDrive.defaultDrive` carries the ruling for why that
/// default is unconditional and why no locale and no location is consulted to pick it. No duration anywhere:
/// nobody has measured one, and a number nobody measured is the kind of claim this repository exists to catch.
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

    /// How much of the drive the sheet shows. A launch argument can pick the first one (`HomeSheetDetent`).
    @State private var sheetDetent = HomeSheetDetent.atLaunch

    /// The chip band's bottom edge and the credit band's top edge, in window points - the two edges `MapView`
    /// converts into its own. Zero until measured, and the map then treats nothing as covered. The map's own height
    /// is NOT measured here: SwiftUI reports the safe-area height for a view that ignores the safe area.
    @State private var chipBandBottom: CGFloat = 0
    @State private var creditBandTop: CGFloat = 0

    public init() {}

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
        .onChange(of: selectedDrive) { resolveBasemap() }
        .onChange(of: colorScheme) { resolveBasemap() }
        .sheet(isPresented: $isShowingDisclaimer) {
            SafetyDisclaimer(onAccept: {
                isSafetyDisclaimerAcknowledged = true
                isShowingDisclaimer = false
            })
            .accessibilityIdentifier("home.disclaimer")
        }
    }

    /// Ask `DriveBasemap` which tiles this drive can have on this device, and keep the answer: the LA drives get the
    /// Protomaps basemap when `la.pmtiles` is on the phone and the demo tiles when it is not (see `DriveBasemap`).
    private func resolveBasemap() {
        route = DriveRoute.resolve(for: selectedDrive)
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
            onBlocked: { isShowingDisclaimer = true },
            onFailure: { handoffFailure = $0 }
        )
    }

    /// The three drives, floating over the map below the status bar. Each chip carries its own opaque ground
    /// (`primary` or `surface`); the band under them is a material with a `border` hairline, so the row reads as one
    /// control over either basemap, in either appearance. Every chip is 44 pt tall (`DriveSelector`).
    private var chips: some View {
        DriveSelector(selection: $selectedDrive)
            .padding(6)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .strokeBorder(DesignTokens.border, lineWidth: 1)
            )
            .padding(.horizontal, 12)
            .padding(.top, 4)
            .onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).maxY } action: { chipBandBottom = $0 }
    }

    /// The collapsed sheet: the drive's name and where it goes, a failure card if the handoff refused, the
    /// conditions line, the button. Short, because it is the first thing anyone sees.
    @ViewBuilder
    private var sheetSummary: some View {
        Text(DriveCopy.title(for: selectedDrive))
            .font(.title3)
            .fontWeight(.semibold)
            .foregroundStyle(DesignTokens.fg)
            .fixedSize(horizontal: false, vertical: true)
            .accessibilityAddTraits(.isHeader)
            .accessibilityIdentifier("home.title")

        if let handoffFailure {
            HandoffFailureCard(message: handoffFailure,
                               roadList: DriveCopy.route(for: selectedDrive),
                               drive: selectedDrive,
                               onRetry: { gatedHandoff.attempt() })
        }

        conditions

        gatedHandoff
    }

    /// What `medium` adds. The caption reads the resolved `style`: it says what is under the map, and on a device
    /// with no LA archive that is the demo basemap whichever drive is selected.
    private var sheetDetails: some View {
        DriveDetails(drive: selectedDrive, caption: DriveCopy.mapCaption(for: selectedDrive, style: style))
    }

    /// The persistent conditions line - the plan's risk table, verbatim, as the mitigation for *sedan onto
    /// dirt/gated/closed road*. In the sheet's collapsed part, so it is on screen at both detents, directly above
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

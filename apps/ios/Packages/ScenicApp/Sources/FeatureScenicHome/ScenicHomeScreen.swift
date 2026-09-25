import DesignSystem
import Handoff
import MapAdapter
import ScenicKit
import SwiftUI

/// The walking skeleton's only screen: the drive named, a map that says what it is, a truthful credit
/// line, a line about conditions that never leaves, and one gated button.
///
/// M1.5 exists to prove the seam, not the product - MapLibre draws on a real phone, `DesignSystem`
/// renders on both appearances, and `Handoff` produces a URL Apple Maps accepts. Every real surface
/// (plan sheet, route preview, hazard strip) arrives in M4 and replaces the middle of this file; the
/// map, the footer, the disclaimer and the handoff at the edges are the parts that stay.
///
/// The title and the road list name the drive `SkylineHandoff.waypoints(for:)` describes, but neither
/// is derived from it: the route types hold coordinates, and no name and no road names. Changing a
/// drive, renaming it and rewriting its road list are three edits, and nothing but review ties them
/// together - see `DriveCopy`, which is where all three live for both drives.
///
/// ## Two drives, one screen (T-0178)
///
/// `selectedDrive` is the one value the title, the road line, the distance, the map centre, the
/// caption and the handoff URL all read. Saddle Peak is the default (T-0236), the loop and the Skyline
/// drive each one 44 pt tap away; `HandoffDrive.defaultDrive` carries the ruling for why that default is unconditional and
/// why no locale and no location is consulted to pick it.
///
/// No duration anywhere on this screen. Nobody has driven this route or measured it, and a number
/// nobody measured is the kind of claim this repository exists to catch.
///
/// ## The safety gate (P-SAFE-03)
///
/// CLAUDE.md's product invariant: *"The safety disclaimer gates the first plan and stays visible on the
/// route screen."* There is no route screen yet (plan M4), so both halves land here, on the only screen
/// there is: the first tap on the handoff opens `SafetyDisclaimer` instead of leaving, and
/// `Copy.conditions` is on screen at every size, always. Accepting records the acknowledgement and
/// dismisses; it does not also leave for Apple Maps, because leaving the app is worth a second,
/// deliberate tap.
///
/// The guard itself is inside `GatedHandoffButton` - see that type for why the gate has a name instead of
/// being twenty inline lines, and `ops/lib/check-safety-disclaimer` for what a source-level check can and
/// cannot decide about it.
public struct ScenicHomeScreen: View {
    /// The basemap ACTUALLY on screen, named once so the tiles, the caption and the credit below
    /// cannot drift apart. It starts on the demo case and is replaced by `resolveBasemap()`.
    ///
    /// `@State`, and resolved from `.task`/`.onChange` rather than here or in `body`:
    /// `DriveBasemap.resolve` materialises a style document and touches the file system, and SwiftUI
    /// re-runs `body` - and may re-run a property initialiser - as often as it likes. One resolve per
    /// selection change and per appearance change, which is what those two modifiers buy.
    @State private var style = MapStyle.maplibreDemoTiles

    /// The selected drive's road line, or `nil` (T-0236). `@State` and resolved beside `style`, for the
    /// same reason: `DriveRoute.resolve` reads a file from the bundle.
    @State private var route: MapRoute?

    /// The appearance the map is drawn for. SwiftUI's `ColorScheme` is converted to `MapAppearance` at
    /// this boundary: `MapAdapter` does not know about SwiftUI's environment (see `MapAppearance`).
    @Environment(\.colorScheme) private var colorScheme

    /// Whether the safety disclaimer has been accepted on THIS DEVICE. `@AppStorage` is `UserDefaults`:
    /// no account, no server, nothing leaves the phone, and nothing to migrate. The key is versioned so
    /// that changing what the user is asked to acknowledge can ask again rather than inherit a stale yes.
    @AppStorage("safety.disclaimer.acknowledged.v1")
    private var isSafetyDisclaimerAcknowledged = false

    /// Whether the disclaimer sheet is up. Separate from the acknowledgement: the flag above is what the
    /// user has agreed to and survives the app, this is where the sheet is right now and does not.
    @State private var isShowingDisclaimer = false

    /// Whatever `Handoff` refused, if it refused. Kept so the button can say what went wrong instead
    /// of doing nothing when tapped - a dead button is the failure mode that gets shipped, because it
    /// looks identical to a working one in a screenshot.
    @State private var handoffFailure: String?

    /// Which drive is on screen. The title, the road line, the distance, the map centre, the caption
    /// and the handoff URL all read this one value, which is why they cannot come apart.
    ///
    /// `HandoffDrive.defaultDrive` and NOT a locale or a location test - see that property for the
    /// ruling. `Locale.current.region` is a country (`US`) and there is no identifier for Southern
    /// California; a last-known coarse position would need a CoreLocation authorization this app has
    /// never asked for and must not. So the plan's 5.1.1(iv) "nothing is known" case is the only case:
    /// the owner in Westwood opens the app on the LA drive with no permission prompt, and a friend who
    /// has denied Location sees exactly the same screen, because nothing here reads a location.
    ///
    /// `@State` and not `@AppStorage`: the acknowledgement is a thing the user agreed to and has to
    /// survive the app, while which drive is showing is where you are right now. A relaunch is back on
    /// the default, which is the owner's drive.
    @State private var selectedDrive = HandoffDrive.defaultDrive

    public init() {}

    public var body: some View {
        VStack(spacing: 0) {
            header

            ZStack(alignment: .bottom) {
                MapView(
                    styleURL: style.url,
                    // Centred by reusing the SELECTED route's own destination rather than a fresh pair
                    // of digits: San Francisco frames the city, the Peninsula and the ridge; Westwood
                    // frames the Santa Monica Mountains, the coast and the Valley. One verified
                    // coordinate per drive, one place each lives, and the map cannot sit over the Bay
                    // while the title names an LA loop.
                    centerLatitude: SkylineHandoff.destination(for: selectedDrive).latitude,
                    centerLongitude: SkylineHandoff.destination(for: selectedDrive).longitude,
                    zoomLevel: 8.5,
                    // With a line, the camera fits it; without one, the centre above (`MapView`).
                    route: route
                )
                .ignoresSafeArea()

                VStack(spacing: 12) {
                    if let handoffFailure {
                        HandoffFailureCard(message: handoffFailure,
                                           roadList: DriveCopy.route(for: selectedDrive),
                                           drive: selectedDrive,
                                           onRetry: { gatedHandoff.attempt() })
                            .padding(.horizontal, 16)
                    }

                    conditions

                    gatedHandoff
                        .padding(.horizontal, 16)

                    // The credit for the tiles actually on screen, asked of the RESOLVED style itself
                    // and never of the selection: on a device with `la.pmtiles` this is the plan's
                    // `© OpenStreetMap contributors · Protomaps` line, and on every device without it
                    // the same value carries MapLibre's credit for the demo tiles it is drawing - see
                    // `MapStyle.attributionText`. Last in the stack, so nothing above it can sit on the
                    // lower-right corner it owns.
                    AttributionFooter(text: style.attributionText)
                }
            }
        }
        .background(DesignTokens.bg)
        // The three moments the answer can change, and the only three: first appearance, a new drive,
        // and light/dark. Never in `body` and never in a property initialiser - see `style`.
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

    /// Ask `DriveBasemap` which tiles this drive can have on this device, and keep the answer.
    ///
    /// The LA drive gets the Protomaps basemap when `la.pmtiles` is on the phone and the demo tiles
    /// when it is not; the Skyline drive keeps the demo tiles, because the LA archive covers
    /// `-119.0,33.7,-117.85,34.45` and the Peninsula is not in it - see `DriveBasemap`.
    private func resolveBasemap() {
        route = DriveRoute.resolve(for: selectedDrive)
        style = DriveBasemap.resolve(
            for: selectedDrive,
            appearance: colorScheme == .dark ? .dark : .light
        )
    }

    /// The one way out of this app, built in exactly one place.
    ///
    /// A named property rather than an expression inside `body` because two things need it: the button
    /// itself, at the bottom of the stack, and the *Try again* on `HandoffFailureCard`, which calls
    /// `attempt()` on this same value. T-0170's card deliberately does not own the retry - see its
    /// `onRetry` - so that a retry after a failure goes through the acknowledgement gate exactly as the
    /// first tap does. One construction, one guard, one `SkylineHandoff.open(` in the app; that triple
    /// is what `ops/lib/check-safety-disclaimer` (P-SAFE-03) decides, and it is what this property keeps
    /// true while two call sites share the behaviour.
    private var gatedHandoff: GatedHandoffButton {
        GatedHandoffButton(
            isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged,
            drive: selectedDrive,
            onBlocked: { isShowingDisclaimer = true },
            onFailure: { handoffFailure = $0 }
        )
    }

    /// The drive's name, the roads it runs, and the one caption, in a band on `bg` above the map
    /// rather than over it.
    ///
    /// Deliberately not an overlay. `DesignTokens` states its contrast against `bg` and `surface`, and
    /// a basemap is neither - `AttributionFooter` carries its own opaque chip for exactly that reason.
    /// On `bg`, `fg` and `fgMuted` are the pairs the token table was written for, no new token is
    /// needed, and a band across the top cannot reach the lower-right corner the attribution owns.
    ///
    /// Type styles only, no point sizes, so every line grows with Dynamic Type; `fixedSize` vertically
    /// so the largest accessibility sizes wrap instead of truncating. Nothing here is tappable, so
    /// there is no 44 pt target to keep.
    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            // Above the title, because it changes what the title says. Padding-free here: the band's
            // own horizontal padding is the one below.
            DriveSelector(selection: $selectedDrive)
                .padding(.bottom, 4)

            Text(DriveCopy.title(for: selectedDrive))
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("home.title")

            Text(DriveCopy.route(for: selectedDrive))
                .font(.subheadline)
                // `fgMuted`, and the same muted pair for the caption below: both are secondary lines
                // under the title, and `primary` is a button fill, never a sentence on `bg`
                // (`DesignTokens`). Same text style for both, because the roads are the longer and
                // more useful of the two and shrinking them would be the wrong way round.
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.route")

            DriveFacts(drive: selectedDrive)

            // The resolved style, not the selection: the caption says what is under the map, and on a
            // device with no LA archive that is the demo basemap whichever drive is selected.
            Text(DriveCopy.mapCaption(for: selectedDrive, style: style))
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.caption")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 16)
        .padding(.top, 8)
        .padding(.bottom, 12)
    }

    /// The persistent conditions line - the plan's risk table, verbatim, as the mitigation for *sedan
    /// onto dirt/gated/closed road*. Always on screen, whatever the disclaimer has been told.
    ///
    /// Directly above the button and above the attribution, never on top of either: it is a sibling in
    /// the same bottom stack, and the footer is the last element in it, so the lower-right corner stays
    /// the attribution's. `fgMuted` is the secondary-text token, and it carries the same opaque `surface`
    /// chip and `border` hairline `AttributionFooter` carries, for the reason that type states - muted
    /// text over a basemap has to bring its own ground, because the tiles underneath are not a token and
    /// their contrast is not stated anywhere.
    ///
    /// A text style, not a point size, so it grows with Dynamic Type; `fixedSize` vertically so the
    /// largest accessibility sizes wrap rather than truncate a safety sentence.
    private var conditions: some View {
        Text(Copy.conditions)
            .font(.footnote)
            .foregroundStyle(DesignTokens.fgMuted)
            .multilineTextAlignment(.center)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(DesignTokens.surface.opacity(0.85))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8, style: .continuous)
                            .strokeBorder(DesignTokens.border, lineWidth: 1)
                    )
            )
            .padding(.horizontal, 16)
            .accessibilityIdentifier("home.conditions")
            // NEVER hidden from accessibility, stated explicitly rather than left to the default so that
            // removing it is a visible deletion in a diff. A screen reader user is entitled to the same
            // safety line as everybody else.
            .accessibilityHidden(false)
    }

    /// Every user-visible string on this screen, in one place.
    ///
    /// A private nested enum, not an `.xcstrings` catalog: string catalogs are serial-only (CLAUDE.md)
    /// and there is one language today, so a catalog would be a fleet-wide lock held for nothing. The
    /// later extraction stays mechanical - each `static let` becomes a key and no call site moves.
    /// Nested rather than a second file-scope type so the file still declares one type and still
    /// matches its own name.
    /// The strings that belong to the SCREEN rather than to a drive. The title, the road line and the
    /// map caption moved to `DriveCopy` when there were two drives to say them about, because those
    /// three have to change together with the selection and this one must not change at all.
    private enum Copy {
        /// The persistent safety line, from the plan's risk table, word for word. The same sentence the
        /// disclaimer ends on, so the line the user keeps seeing is the line they agreed to. It is the
        /// same for both drives on purpose: conditions change on a ridge in San Mateo County and in
        /// Topanga Canyon alike, and a per-drive safety line would be a line somebody could edit away
        /// one drive at a time.
        static let conditions = "Conditions change. Verify locally."
    }
}

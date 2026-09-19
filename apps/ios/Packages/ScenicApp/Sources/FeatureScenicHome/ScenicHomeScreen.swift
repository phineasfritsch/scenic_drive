import DesignSystem
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
/// The title and the road list name the drive `SkylineHandoff.waypoints` describes, but neither is
/// derived from it: that type holds coordinates, and no name and no road names. Changing the drive,
/// renaming it and rewriting the road list are three edits, and nothing but review ties them together.
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
    /// The placeholder basemap. Named once so the style and the credit below cannot drift apart.
    private let style = MapStyle.maplibreDemoTiles

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

    public init() {}

    public var body: some View {
        VStack(spacing: 0) {
            header

            ZStack(alignment: .bottom) {
                MapView(
                    styleURL: style.url,
                    // Centred on the Bay Area by reusing the route's own destination rather than a fresh
                    // pair of digits: San Francisco at zoom 8.5 frames the city, the Peninsula and the
                    // ridge this drive runs along. One verified coordinate, one place it lives.
                    centerLatitude: SkylineHandoff.destination.latitude,
                    centerLongitude: SkylineHandoff.destination.longitude,
                    zoomLevel: 8.5
                )
                .ignoresSafeArea()

                VStack(spacing: 12) {
                    if let handoffFailure {
                        HandoffFailureCard(message: handoffFailure,
                                           roadList: Copy.route,
                                           onRetry: { handoff() })
                            .padding(.horizontal, 16)
                    }

                    conditions

                    GatedHandoffButton(
                        isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged,
                        onBlocked: { isShowingDisclaimer = true },
                        onFailure: { handoffFailure = $0 }
                    )
                    .padding(.horizontal, 16)

                    // The credit for the tiles actually on screen, asked of the style itself. This is
                    // NOT the plan's `© OpenStreetMap contributors · Protomaps` line, because these are
                    // not those tiles - see `MapStyle.attributionText`. Last in the stack, so nothing
                    // above it can sit on the lower-right corner it owns.
                    AttributionFooter(text: style.attributionText)
                }
            }
        }
        .background(DesignTokens.bg)
        .sheet(isPresented: $isShowingDisclaimer) {
            SafetyDisclaimer(onAccept: {
                isSafetyDisclaimerAcknowledged = true
                isShowingDisclaimer = false
            })
            .accessibilityIdentifier("home.disclaimer")
        }
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
            Text(Copy.title)
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("home.title")

            Text(Copy.route)
                .font(.subheadline)
                // `fgMuted`, and the same muted pair for the caption below: both are secondary lines
                // under the title, and `primary` is a button fill, never a sentence on `bg`
                // (`DesignTokens`). Same text style for both, because the roads are the longer and
                // more useful of the two and shrinking them would be the wrong way round.
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.route")

            DriveFacts()

            Text(Copy.mapCaption)
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
    private enum Copy {
        /// The drive, named by the road it is about and by where it both starts and ends. See the type's
        /// note: a literal, not a rendering of the waypoints - `SkylineRoute` is SF to SF, and this line
        /// says so because the round trip is the thing a reader has to know before tapping. No duration
        /// in it - see the type's note for why there is none anywhere on this screen.
        static let title = "Skyline loop · starts and ends in San Francisco"

        /// The roads, in the order the drive takes them - the one line on this screen that says where
        /// you would actually be, while the map says nothing. Also a literal (the type's note). T-0170
        /// reuses this line: when a handoff fails, the roads are what a user can still act on.
        static let route =
            "I-280 south, Cañada Road north, CA-92 west, Skyline Boulevard south, then back to the city."

        /// What is under the header. `MapStyle.maplibreDemoTiles` draws country polygons and nothing at
        /// the scale of this drive, and the route is not drawn on it at all (M4 draws it), so there is
        /// not a road on screen to follow. First clause: what this build is. Then what the map is not,
        /// and what to do instead, pointing at the button directly below it.
        static let mapCaption =
            "Preview build: one fixed Bay Area drive. The map doesn't show roads yet - tap below and it opens in Apple Maps."

        /// The persistent safety line, from the plan's risk table, word for word. The same sentence the
        /// disclaimer ends on, so the line the user keeps seeing is the line they agreed to.
        static let conditions = "Conditions change. Verify locally."
    }
}

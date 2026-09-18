import DesignSystem
import Handoff
import MapAdapter
import OSLog
import ScenicKit
import SwiftUI

/// The walking skeleton's only screen: the drive named, a map that says what it is, a truthful credit
/// line, and one button that leaves.
///
/// M1.5 exists to prove the seam, not the product - MapLibre draws on a real phone, `DesignSystem`
/// renders on both appearances, and `Handoff` produces a URL Apple Maps accepts. Every real surface
/// (plan sheet, route preview, hazard strip) arrives in M4 and replaces the middle of this file; the
/// map, the footer and the handoff at the edges are the parts that stay.
///
/// The title names the drive `SkylineHandoff.waypoints` describes, but it is not derived from it: that
/// type holds coordinates and no name. Changing the drive and renaming it are two edits, and nothing
/// but review ties them together.
public struct ScenicHomeScreen: View {
    /// The placeholder basemap. Named once so the style and the credit below cannot drift apart.
    private let style = MapStyle.maplibreDemoTiles

    /// Whatever `Handoff` refused, if it refused. Kept so the button can say what went wrong instead
    /// of doing nothing when tapped - a dead button is the failure mode that gets shipped, because it
    /// looks identical to a working one in a screenshot.
    @State private var handoffFailure: String?

    /// Where the reason goes when the user gets the sentence. Subsystem is the app's
    /// `PRODUCT_BUNDLE_IDENTIFIER` from `apps/ios/ScenicDrive.xcodeproj/project.pbxproj`; the category
    /// is this screen, so a log predicate can pick out this seam without matching the whole app.
    private static let log = Logger(subsystem: "com.phineasfritsch.scenicdrive",
                                    category: "ScenicHomeScreen")

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
                        Text(handoffFailure)
                            .font(.footnote)
                            .foregroundStyle(DesignTokens.destructive)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 16)
                            .accessibilityIdentifier("home.error")
                    }

                    openInAppleMaps

                    // The credit for the tiles actually on screen, asked of the style itself. This is
                    // NOT the plan's `© OpenStreetMap contributors · Protomaps` line, because these are
                    // not those tiles - see `MapStyle.attributionText`.
                    AttributionFooter(text: style.attributionText)
                }
            }
        }
        .background(DesignTokens.bg)
    }

    /// The drive's name and the one caption, in a band on `bg` above the map rather than over it.
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

            Text(Copy.mapIsAStandIn)
                .font(.subheadline)
                // `fgMuted`: this is secondary text under a title, and `primary` is a button fill,
                // never a sentence on `bg` (`DesignTokens`).
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("home.caption")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 16)
        .padding(.top, 8)
        .padding(.bottom, 12)
    }

    /// The handoff button.
    ///
    /// `primary` fill with `onPrimary` text, never `primary` as text on `bg` (`DesignTokens`).
    /// `minHeight: 44` is the floor from the plan's target size, and the label is inside the frame
    /// rather than the frame being sized to the label, so it stays a 44 pt target at the smallest
    /// Dynamic Type setting too.
    private var openInAppleMaps: some View {
        Button {
            handoff()
        } label: {
            Text("Open in Apple Maps")
                .font(.headline)
                .foregroundStyle(DesignTokens.onPrimary)
                .frame(maxWidth: .infinity, minHeight: 44)
                .background(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .fill(DesignTokens.primary)
                )
        }
        .buttonStyle(.plain)
        .padding(.horizontal, 16)
        .accessibilityIdentifier("home.openInAppleMaps")
    }

    /// Builds the URL and leaves, or puts a sentence the user can act on on screen.
    ///
    /// Two destinations for one failure, on purpose. The screen gets `Copy.handoffFailed` - what broke
    /// and what to do. The raw error goes to `Logger`, where it keeps its type and its associated
    /// values.
    ///
    /// This replaces `String(describing: error)` on screen, whose defence was that rewriting the
    /// message is how the real reason stops reaching anybody. That held only while the on-screen
    /// string was the only record of the failure. It is not one any more, and a Swift type name was
    /// never a sentence the reader could act on.
    private func handoff() {
        do {
            try SkylineHandoff.open()
            handoffFailure = nil
        } catch {
            // `.public`: `HandoffError` carries a coordinate pair or a waypoint count, and the
            // coordinates in it are this file's hard-coded route, never the user's location -
            // `SkylineHandoff.directions()` passes `source: nil` precisely so the app never holds one.
            // Redacting it would log a failure with the reason removed, which is the same defect as
            // showing the type name instead of the sentence.
            Self.log.error("SkylineHandoff.open() refused: \(String(describing: error), privacy: .public)")
            handoffFailure = Copy.handoffFailed
        }
    }

    /// Every user-visible string on this screen, in one place.
    ///
    /// A private nested enum, not an `.xcstrings` catalog: string catalogs are serial-only (CLAUDE.md)
    /// and there is one language today, so a catalog would be a fleet-wide lock held for nothing. The
    /// later extraction stays mechanical - each `static let` becomes a key and no call site moves.
    /// Nested rather than a second file-scope type so the file still declares one type and still
    /// matches its own name.
    private enum Copy {
        /// The drive, named. See the type's note: this is a literal, not a rendering of the waypoints.
        static let title = "Skyline via Cañada Road"

        /// What is actually under the title. `MapStyle.maplibreDemoTiles` draws country polygons and
        /// nothing at the scale of this drive, and the route is not drawn on it at all (M4 draws it),
        /// so the user is looking at neither their route nor their roads. Saying which of the two is
        /// missing would still be wrong; both are.
        static let mapIsAStandIn =
            "Preview build - this map is a stand-in, not your route. The drive opens in Apple Maps."

        /// Shown when `Handoff` refuses. What failed, then what to do, and nothing this screen cannot
        /// back up: there is no copy-the-route affordance here to point the reader at.
        static let handoffFailed = "Couldn't open Apple Maps. Try again."
    }
}

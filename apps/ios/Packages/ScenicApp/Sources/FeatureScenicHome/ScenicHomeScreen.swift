import DesignSystem
import Handoff
import MapAdapter
import ScenicKit
import SwiftUI

/// The walking skeleton's only screen: a map, a truthful credit line, and one button that leaves.
///
/// M1.5 exists to prove the seam, not the product - MapLibre draws on a real phone, `DesignSystem`
/// renders on both appearances, and `Handoff` produces a URL Apple Maps accepts. Every real surface
/// (plan sheet, route preview, hazard strip) arrives in M4 and replaces the middle of this file; the
/// map, the footer and the handoff at the edges are the parts that stay.
public struct ScenicHomeScreen: View {
    /// The placeholder basemap. Named once so the style and the credit below cannot drift apart.
    private let style = MapStyle.maplibreDemoTiles

    /// Whatever `Handoff` refused, if it refused. Kept so the button can say what went wrong instead
    /// of doing nothing when tapped - a dead button is the failure mode that gets shipped, because it
    /// looks identical to a working one in a screenshot.
    @State private var handoffFailure: String?

    public init() {}

    public var body: some View {
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
                }

                openInAppleMaps

                // The credit for the tiles actually on screen, asked of the style itself. This is
                // NOT the plan's `© OpenStreetMap contributors · Protomaps` line, because these are
                // not those tiles - see `MapStyle.attributionText`.
                AttributionFooter(text: style.attributionText)
            }
        }
        .background(DesignTokens.bg)
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

    /// Builds the URL and leaves, or keeps the refusal on screen.
    ///
    /// The error text is `HandoffError`'s own description rather than a rewritten sentence: this
    /// screen cannot tell the user anything more accurate than the type that refused, and inventing a
    /// friendlier message here is how the real reason stops reaching anybody.
    private func handoff() {
        do {
            try SkylineHandoff.open()
            handoffFailure = nil
        } catch {
            handoffFailure = String(describing: error)
        }
    }
}

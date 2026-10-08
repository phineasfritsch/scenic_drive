import DesignSystem
import Handoff
import MapAdapter
import ScenicKit
import SwiftUI

/// The drive (T-0324): the planned line on the map with its credit, and exactly what ScenicKit's DriveDisplay says to
/// show for the navigator's surface and mode. This target never imports NavAdapter: the shell composes DriveHost's
/// published display into it (R1). It reads `display` and nothing else about the drive's state (P-SAFE-09, R7).
///
/// Moving (the minimal surface): the map, its credit and the one large action - the reroute or rejoin state is a
/// caption inside that action. Stopped (full): a status banner, PlanPreview's ETA line with its estimate badge and
/// the conditions line are added (Ferrostar's step durations are 0, so the ETA is the plan's).
public struct DriveScreen: View {
    @Environment(\.colorScheme) private var colorScheme

    /// The basemap ACTUALLY on screen, named once so the tiles and the credit cannot drift apart (P-ATTR-01).
    @State private var style = MapStyle.maplibreDemoTiles
    /// The drive's current line as the map draws it - the plan's, then each taken reroute's (T-0328 R4); its data
    /// credit joins the footer.
    @State private var route: MapRoute?
    @State private var bannerBottom: CGFloat = 0
    @State private var creditBandTop: CGFloat = 0

    private let preview: PlanPreview
    private let display: DriveDisplay
    private let onEnd: () -> Void

    public init(preview: PlanPreview, display: DriveDisplay, onEnd: @escaping () -> Void) {
        self.preview = preview
        self.display = display
        self.onEnd = onEnd
    }

    public var body: some View {
        ZStack(alignment: .top) {
            MapView(
                styleURL: style.url,
                centerLatitude: preview.route.first?.latitude ?? 0,
                centerLongitude: preview.route.first?.longitude ?? 0,
                zoomLevel: 12,
                coveredAboveY: bannerBottom,
                coveredBelowY: creditBandTop,
                route: route
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                banner
                    .onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).maxY } action: { bannerBottom = $0 }

                Spacer(minLength: 0)

                VStack(spacing: 0) {
                    AttributionFooter(text: CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit))
                    controls
                }
                .onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).minY } action: { creditBandTop = $0 }
            }
        }
        .background(DesignTokens.bg)
        .task { resolveMap() }
        .onChange(of: colorScheme) { resolveMap() }
        .onChange(of: display.line) { resolveMap() }
    }

    /// The full surface's status, as a sentence under the status bar. Nothing on the minimal surface.
    @ViewBuilder private var banner: some View {
        if display.showsDetails, let status = display.status {
            Label(status, systemImage: "arrow.triangle.turn.up.right.circle")
                .font(.body)
                .foregroundStyle(DesignTokens.fg)
                .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                .padding(.horizontal, 16)
                .background(DesignTokens.surface)
                .accessibilityIdentifier("drive.status")
        }
    }

    /// The ETA, the badge and the conditions when stopped; the one action always.
    private var controls: some View {
        VStack(alignment: .leading, spacing: 12) {
            if display.showsDetails {
                Text(preview.etaLine)
                    .font(.body)
                    .foregroundStyle(DesignTokens.fg)
                if preview.showsEstimateBadge {
                    Text(PlanPreview.estimateBadge)
                        .font(.footnote)
                        .foregroundStyle(DesignTokens.fgMuted)
                        .accessibilityIdentifier("drive.estimate")
                }
                Text(PlanPreview.conditions)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(DesignTokens.fg)
                    .accessibilityIdentifier("drive.conditions")
            }
            endButton
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(DesignTokens.surface)
    }

    /// The one action. While moving it is the one large target, and it carries the reroute or rejoin caption.
    private var endButton: some View {
        Button(action: onEnd) {
            VStack(spacing: 2) {
                Label(display.actionTitle, systemImage: "xmark.circle.fill")
                    .font(.title3)
                    .fontWeight(.semibold)
                if !display.showsDetails, let status = display.status {
                    Text(status)
                        .font(.subheadline)
                        .accessibilityIdentifier("drive.caption")
                }
            }
            .foregroundStyle(DesignTokens.onPrimary)
            .frame(maxWidth: .infinity, minHeight: display.actionMinHeight)
            .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(DesignTokens.primary))
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("drive.end")
    }

    /// The LA basemap when the archive is on the phone, the demo tiles when it is not, and the line the drive is on.
    private func resolveMap() {
        route = DriveMapLine.route(for: display.line)
        style = DriveBasemap.planned(appearance: colorScheme == .dark ? .dark : .light)
    }
}

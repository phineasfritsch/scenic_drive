import DesignSystem
import Handoff
import MapAdapter
import ScenicKit
import SwiftUI

/// The plan preview's map (T-0405 R1-R4): the previewed route drawn on the planned basemap, fitted to the route's
/// bounds above the credit band, with the one composed credit on the map's bottom edge (P-ATTR-01). The plan sheet
/// cannot import MapAdapter, so the shell hands this view to PlanSheetScreen as its `previewMap`.
public struct PlanPreviewMap: View {
    @Environment(\.colorScheme) private var colorScheme
    /// The basemap ACTUALLY on screen, named once so the tiles and the credit cannot drift apart (P-ATTR-01).
    @State private var style = MapStyle.maplibreDemoTiles
    /// The previewed line as the map draws it; its data credit is composed into the footer.
    @State private var route: MapRoute?
    /// The window y of the credit band's top edge: the route is fitted into the map above it.
    @State private var creditBandTop: CGFloat = 0

    private let preview: PlanPreview

    public init(preview: PlanPreview) {
        self.preview = preview
    }

    public var body: some View {
        ZStack(alignment: .bottom) {
            MapView(
                styleURL: style.url,
                centerLatitude: preview.route.first?.latitude ?? 0,
                centerLongitude: preview.route.first?.longitude ?? 0,
                zoomLevel: 11,
                coveredBelowY: creditBandTop,
                route: route
            )
            AttributionFooter(text: CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit))
                .onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).minY } action: { creditBandTop = $0 }
        }
        .clipped()
        .accessibilityIdentifier("plan.map")
        .task { resolveMap() }
        .onChange(of: colorScheme) { resolveMap() }
        .onChange(of: preview.route) { resolveMap() }
    }

    /// The LA basemap when the archive is on the phone, the demo tiles when it is not, and the previewed line.
    private func resolveMap() {
        route = DriveMapLine.route(for: preview.route)
        style = DriveBasemap.planned(appearance: colorScheme == .dark ? .dark : .light)
    }
}

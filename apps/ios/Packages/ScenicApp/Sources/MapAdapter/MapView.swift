import CoreLocation
import MapLibre
import SwiftUI

/// SwiftUI's view of an `MLNMapView`.
///
/// **The only `import MapLibre` in the repository** (CLAUDE.md) outside this target's own files. Every other
/// target reaches the renderer through this type, which is what keeps a map SDK swap to one target instead of
/// a search across the feature layer.
///
/// It takes latitude and longitude as plain `Double`s rather than a `ScenicKit.Coordinate`, because
/// `MapAdapter` depends on MapLibre and nothing else. Bridging to `CLLocationCoordinate2D` happens
/// here, at the boundary, so CoreLocation never appears in the Linux-buildable core.
///
/// ## Covered edges (T-0237)
///
/// The map is full-bleed under floating chrome: `obscuredTop` is how far down from the map's top edge the chips
/// cover it, `obscuredBottom` how far up from its bottom edge the credit band and the sheet do, both in points of
/// this view. The camera fits the drive's line between them, and MapLibre's logo and (i) are kept on the uncovered
/// map - see `MapRouteCoordinator`. Zero means "nothing covers this edge", which is what a caller that measures
/// nothing gets.
public struct MapView: UIViewRepresentable {
    /// The style JSON to render. See `MapStyle` for what is actually behind it today.
    public let styleURL: URL

    /// The camera when there is no route: centre and zoom. See `MapRouteCoordinator` for when it is applied.
    public let centerLatitude: Double
    public let centerLongitude: Double
    public let zoomLevel: Double

    /// How far the floating chrome covers the map from its top and its bottom edge, in points.
    public let obscuredTop: CGFloat
    public let obscuredBottom: CGFloat

    /// The drive's road line, or `nil` for a drive with no recorded geometry (T-0236). With a route the camera
    /// fits the line's box; without one it is the centre and zoom above, exactly as before.
    public let route: MapRoute?

    public init(styleURL: URL,
                centerLatitude: Double,
                centerLongitude: Double,
                zoomLevel: Double,
                obscuredTop: CGFloat = 0,
                obscuredBottom: CGFloat = 0,
                route: MapRoute? = nil) {
        self.styleURL = styleURL
        self.centerLatitude = centerLatitude
        self.centerLongitude = centerLongitude
        self.zoomLevel = zoomLevel
        self.obscuredTop = obscuredTop
        self.obscuredBottom = obscuredBottom
        self.route = route
    }

    public func makeCoordinator() -> MapRouteCoordinator {
        MapRouteCoordinator()
    }

    public func makeUIView(context: Context) -> MLNMapView {
        let mapView = MLNMapView(frame: .zero, styleURL: styleURL)
        mapView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        mapView.delegate = context.coordinator

        // MapLibre's own attribution control stays on. `AttributionFooter` is the app's visible
        // credit line (P-ATTR-01); this button is the licence detail sheet behind it, and hiding it to
        // tidy the map would remove the only place the full terms appear.
        mapView.attributionButton.isHidden = false
        mapView.logoView.isHidden = false

        // MOVED, NEVER HIDDEN (T-0236 R4, T-0237 R6). The (i) top-left and the compass top-right, both below the
        // chips; the logo bottom-left, in the band beside the pill, above the sheet. The margins follow the two
        // covered edges and are set by the coordinator, which knows the safe area they are measured from.
        mapView.attributionButtonPosition = .topLeft
        mapView.compassViewPosition = .topRight
        mapView.logoViewPosition = .bottomLeft

        context.coordinator.update(mapView, route: route, target: cameraTarget, covered: covered)
        return mapView
    }

    public func updateUIView(_ uiView: MLNMapView, context: Context) {
        if uiView.styleURL != styleURL {
            uiView.styleURL = styleURL
        }
        context.coordinator.update(uiView, route: route, target: cameraTarget, covered: covered)
    }

    private var covered: MapRouteCoordinator.Covered {
        MapRouteCoordinator.Covered(top: max(0, obscuredTop), bottom: max(0, obscuredBottom))
    }

    private var cameraTarget: MapRouteCoordinator.Target {
        if let route {
            return .fit(west: route.west, south: route.south, east: route.east, north: route.north)
        }
        return .center(latitude: centerLatitude, longitude: centerLongitude, zoom: zoomLevel)
    }
}

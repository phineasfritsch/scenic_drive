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
public struct MapView: UIViewRepresentable {
    /// The style JSON to render. See `MapStyle` for what is actually behind it today.
    public let styleURL: URL

    /// The camera when there is no route: centre and zoom. See `MapRouteCoordinator` for when it is applied.
    public let centerLatitude: Double
    public let centerLongitude: Double
    public let zoomLevel: Double

    /// The drive's road line, or `nil` for a drive with no recorded geometry (T-0236). With a route the camera
    /// fits the line's box; without one it is the centre and zoom above, exactly as before.
    public let route: MapRoute?

    public init(styleURL: URL,
                centerLatitude: Double,
                centerLongitude: Double,
                zoomLevel: Double,
                route: MapRoute? = nil) {
        self.styleURL = styleURL
        self.centerLatitude = centerLatitude
        self.centerLongitude = centerLongitude
        self.zoomLevel = zoomLevel
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

        // MOVED, NEVER HIDDEN (T-0236, R4). At its default bottom-right the (i) sat under the credit pill
        // in the first screenshots (PR #127) - present, and untappable. The map's top-left corner is the one
        // nothing else uses: the header band is above it, the compass takes the top-right when the map is
        // rotated, the MapLibre logo the bottom-left and the credit pill the bottom-right.
        mapView.attributionButtonPosition = .topLeft
        mapView.attributionButtonMargins = CGPoint(x: 8, y: 8)

        context.coordinator.update(mapView, route: route, target: cameraTarget)
        return mapView
    }

    /// Reconciles the style, the line and the camera TARGET.
    ///
    /// SwiftUI calls this on every body re-evaluation of every ancestor. The coordinator applies a camera
    /// target only when it differs from the last one it applied, so a redraw never snaps the map back
    /// mid-pan; a new selection is a new target and moves it once.
    public func updateUIView(_ uiView: MLNMapView, context: Context) {
        if uiView.styleURL != styleURL {
            uiView.styleURL = styleURL
        }
        context.coordinator.update(uiView, route: route, target: cameraTarget)
    }

    /// Fit the route's box when there is a route; otherwise today's centre and zoom.
    private var cameraTarget: MapRouteCoordinator.Target {
        if let route {
            return .fit(west: route.west, south: route.south, east: route.east, north: route.north)
        }
        return .center(latitude: centerLatitude, longitude: centerLongitude, zoom: zoomLevel)
    }
}

import CoreLocation
import MapLibre
import SwiftUI

/// SwiftUI's view of an `MLNMapView`.
///
/// **The only `import MapLibre` in the repository** (CLAUDE.md). Every other target reaches the
/// renderer through this type, which is what keeps a map SDK swap to one target instead of a search
/// across the feature layer.
///
/// It takes latitude and longitude as plain `Double`s rather than a `ScenicKit.Coordinate`, because
/// `MapAdapter` depends on MapLibre and nothing else. Bridging to `CLLocationCoordinate2D` happens
/// here, at the boundary, so CoreLocation never appears in the Linux-buildable core.
public struct MapView: UIViewRepresentable {
    /// The style JSON to render. See `MapStyle` for what is actually behind it today.
    public let styleURL: URL

    /// Initial camera - applied once, at creation. See `updateUIView(_:context:)`.
    public let centerLatitude: Double
    public let centerLongitude: Double
    public let zoomLevel: Double

    public init(styleURL: URL,
                centerLatitude: Double,
                centerLongitude: Double,
                zoomLevel: Double) {
        self.styleURL = styleURL
        self.centerLatitude = centerLatitude
        self.centerLongitude = centerLongitude
        self.zoomLevel = zoomLevel
    }

    public func makeUIView(context: Context) -> MLNMapView {
        let mapView = MLNMapView(frame: .zero, styleURL: styleURL)
        mapView.autoresizingMask = [.flexibleWidth, .flexibleHeight]

        // MapLibre's own attribution control stays on. `AttributionFooter` is the app's visible
        // credit line and the thing the plan's P-ATTR-01 will anchor on - that pin is not yet filed
        // in pins/PINS.yaml, so nothing checks this today; this button is the licence detail sheet
        // behind it, and hiding it to tidy the map would remove the only place the full terms appear.
        mapView.attributionButton.isHidden = false
        mapView.logoView.isHidden = false

        // The initial camera, and the ONLY place it is set.
        mapView.setCenter(
            CLLocationCoordinate2D(latitude: centerLatitude, longitude: centerLongitude),
            zoomLevel: zoomLevel,
            animated: false
        )
        return mapView
    }

    /// Reconciles the style only.
    ///
    /// The camera is pointedly absent. SwiftUI calls this on every body re-evaluation of every
    /// ancestor, and re-applying `centerLatitude`/`centerLongitude` here would snap the map back to
    /// the Bay Area mid-pan, every time anything above it redrew - the classic `UIViewRepresentable`
    /// bug, and one that looks like a MapLibre gesture fault rather than a SwiftUI one. The camera is
    /// an *initial* camera; when the app needs to move it programmatically that becomes an explicit
    /// binding with its own type, not a silent side effect of re-rendering.
    public func updateUIView(_ uiView: MLNMapView, context: Context) {
        if uiView.styleURL != styleURL {
            uiView.styleURL = styleURL
        }
    }
}

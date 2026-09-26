import CoreLocation
import MapLibre
import SwiftUI
import UIKit

/// `MapView`'s coordinator: draws the drive's line, moves the camera, and keeps MapLibre's ornaments on the
/// uncovered map - and nothing else.
///
/// ## The line (T-0236, R3)
///
/// One `MLNShapeSource` and two `MLNLineStyleLayer`s - a casing `MapRoute.lineWidth + 2 * casingWidth` wide
/// under the line `MapRoute.lineWidth` wide, round joins and caps - inserted BELOW the style's first
/// `MLNSymbolStyleLayer`: above every fill and line of the basemap, under its labels, so a town name is never
/// painted over. A style load throws every runtime layer away, so they are installed again on every
/// `didFinishLoading` (a light/dark style swap, a basemap swap). A drive without geometry sets the source's
/// shape to `nil`: the layers stay and draw nothing. Never straight lines between pins - there is no code
/// here that could draw one.
///
/// ## The camera
///
/// Applied once per distinct TARGET AND COVERED EDGES - "fit these bounds between these edges" or "centre here at
/// this zoom" - and never because SwiftUI re-rendered: `MapView.updateUIView` runs on every ancestor's redraw, and
/// re-applying an unchanged camera there would snap the map back mid-pan. A new selection or a new sheet detent is
/// a new camera and moves it once. A fit needs the view's size, which is `.zero` in `makeUIView`, so it waits for
/// the first frame the map renders at a real size.
///
/// ## The covered edges (T-0237, R5/R6)
///
/// The fit padding is each covered edge plus `margin`, and it is the WHOLE padding: MapLibre 6.31 adds its
/// `contentInset` to every fit's padding (MLNMapView.mm, `setVisibleCoordinates:`) and by default sets that inset to
/// the safe area, so `MapView` zeroes it and turns the adjustment off. The ornaments hang from the TOP covered edge:
/// they are anchored to the safe area (`mgl_safeTopAnchor`), so their margins are that edge less
/// `safeAreaInsets.top`, read from the view itself when they are placed - nothing here assumes a device.
@MainActor
public final class MapRouteCoordinator: NSObject, @preconcurrency MLNMapViewDelegate {
    /// What the camera should show. Equatable, so "the same target again" is a comparison, not a guess.
    enum Target: Equatable {
        case fit(west: Double, south: Double, east: Double, north: Double)
        case center(latitude: Double, longitude: Double, zoom: Double)
    }

    /// How far the floating chrome covers the map from its top and bottom edges, in points (`MapView`).
    struct Covered: Equatable {
        var top: CGFloat
        var bottom: CGFloat
    }

    static let sourceIdentifier = "scenic-route"
    static let lineIdentifier = "scenic-route-line"
    static let casingIdentifier = "scenic-route-casing"

    /// The clear space a fit leaves between the line and each covered edge, and at the sides.
    static let margin: CGFloat = 24

    /// The (i) and the compass share the top-right corner under the chips; the compass (shown only when the map
    /// is rotated) sits one tap target below the (i).
    static let compassDrop: CGFloat = 44

    private var route: MapRoute?
    private var paintedStyle: UIUserInterfaceStyle?
    private var target: Target?
    private var covered = Covered(top: 0, bottom: 0)
    private var appliedTarget: Target?
    private var appliedCovered: Covered?

    /// The one entry point `MapView` calls, from `makeUIView` and from every `updateUIView`.
    func update(_ mapView: MLNMapView, route: MapRoute?, target: Target, covered: Covered) {
        if route != self.route || mapView.traitCollection.userInterfaceStyle != paintedStyle {
            self.route = route
            if let style = mapView.style {
                install(on: style, in: mapView)
            }
        }
        self.target = target
        self.covered = covered
        placeOrnaments(mapView)
        applyCamera(mapView)
    }

    public func mapView(_ mapView: MLNMapView, didFinishLoading style: MLNStyle) {
        install(on: style, in: mapView)
        applyCamera(mapView)
    }

    public func mapViewDidFinishRenderingFrame(_ mapView: MLNMapView, fullyRendered: Bool) {
        placeOrnaments(mapView)
        applyCamera(mapView)
    }

    /// The logo top-left, the (i) top-right and the compass under it, all just below the chips: margins from the
    /// safe area the ornaments are anchored to. Set only when they change - this runs on every rendered frame.
    private func placeOrnaments(_ mapView: MLNMapView) {
        let safe = mapView.safeAreaInsets
        let top = CGPoint(x: 8, y: max(8, covered.top - safe.top + 8))
        let compass = CGPoint(x: 8, y: top.y + Self.compassDrop)
        if mapView.logoViewMargins != top {
            mapView.logoViewMargins = top
        }
        if mapView.attributionButtonMargins != top {
            mapView.attributionButtonMargins = top
        }
        if mapView.compassViewMargins != compass {
            mapView.compassViewMargins = compass
        }
    }

    private func applyCamera(_ mapView: MLNMapView) {
        guard let target, target != appliedTarget || covered != appliedCovered else { return }
        let animated = appliedTarget != nil
        switch target {
        case let .fit(west, south, east, north):
            // Not laid out yet: the next rendered frame asks again.
            guard mapView.bounds.width > 0, mapView.bounds.height > 0 else { return }
            let padding = UIEdgeInsets(top: covered.top + Self.margin,
                                       left: Self.margin,
                                       bottom: covered.bottom + Self.margin,
                                       right: Self.margin)
            // Covered edges that leave no map between them (a sheet measured before the map was) wait for the
            // next frame rather than hand MapLibre a padding taller than the view.
            let open = mapView.bounds.height - padding.top - padding.bottom
            guard open > Self.margin else { return }
            let bounds = MLNCoordinateBounds(
                sw: CLLocationCoordinate2D(latitude: south, longitude: west),
                ne: CLLocationCoordinate2D(latitude: north, longitude: east)
            )
            mapView.setVisibleCoordinateBounds(bounds, edgePadding: padding,
                                               animated: animated, completionHandler: nil)
        case let .center(latitude, longitude, zoom):
            mapView.setCenter(CLLocationCoordinate2D(latitude: latitude, longitude: longitude),
                              zoomLevel: zoom, animated: false)
        }
        appliedTarget = target
        appliedCovered = covered
    }

    private func install(on style: MLNStyle, in mapView: MLNMapView) {
        let shape = route.flatMap { try? MLNShape(data: $0.geoJSON, encoding: String.Encoding.utf8.rawValue) }
        let source: MLNShapeSource
        if let existing = style.source(withIdentifier: Self.sourceIdentifier) as? MLNShapeSource {
            existing.shape = shape
            source = existing
        } else {
            source = MLNShapeSource(identifier: Self.sourceIdentifier, shape: shape, options: nil)
            style.addSource(source)
        }

        let casing: MLNLineStyleLayer
        if let existing = style.layer(withIdentifier: Self.casingIdentifier) as? MLNLineStyleLayer {
            casing = existing
        } else {
            casing = MLNLineStyleLayer(identifier: Self.casingIdentifier, source: source)
            if let labels = style.layers.first(where: { $0 is MLNSymbolStyleLayer }) {
                style.insertLayer(casing, below: labels)
            } else {
                style.addLayer(casing)
            }
        }
        let line: MLNLineStyleLayer
        if let existing = style.layer(withIdentifier: Self.lineIdentifier) as? MLNLineStyleLayer {
            line = existing
        } else {
            line = MLNLineStyleLayer(identifier: Self.lineIdentifier, source: source)
            style.insertLayer(line, above: casing)
        }

        let traits = mapView.traitCollection
        let lineColor = UIColor(route?.lineColor ?? .clear).resolvedColor(with: traits)
        let casingColor = UIColor(route?.casingColor ?? .clear).resolvedColor(with: traits)
        for (layer, color, width) in [(casing, casingColor, MapRoute.lineWidth + 2 * MapRoute.casingWidth),
                                      (line, lineColor, MapRoute.lineWidth)] {
            layer.lineColor = NSExpression(forConstantValue: color)
            layer.lineWidth = NSExpression(forConstantValue: width)
            layer.lineJoin = NSExpression(forConstantValue: "round")
            layer.lineCap = NSExpression(forConstantValue: "round")
        }
        paintedStyle = traits.userInterfaceStyle
    }
}

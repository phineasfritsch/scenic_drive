import CoreLocation
import MapLibre
import SwiftUI
import UIKit

/// `MapView`'s coordinator: draws the drive's line and moves the camera - and nothing else.
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
/// Applied once per distinct TARGET - "fit these bounds" or "centre here at this zoom" - and never because
/// SwiftUI re-rendered: `MapView.updateUIView` runs on every ancestor's redraw, and re-applying an unchanged
/// target there would snap the map back mid-pan. A new selection is a new target and moves the camera once.
/// A fit needs the view's size, which is `.zero` in `makeUIView`, so it waits for the first frame the map
/// renders at a real size; a centre does not, and is applied at once, as it always was.
@MainActor
public final class MapRouteCoordinator: NSObject, @preconcurrency MLNMapViewDelegate {
    /// What the camera should show. Equatable, so "the same target again" is a comparison, not a guess.
    enum Target: Equatable {
        case fit(west: Double, south: Double, east: Double, north: Double)
        case center(latitude: Double, longitude: Double, zoom: Double)
    }

    static let sourceIdentifier = "scenic-route"
    static let lineIdentifier = "scenic-route-line"
    static let casingIdentifier = "scenic-route-casing"

    /// The padding a fit leaves, in points. Measured on the first screenshots (PR #127, T-0236's Log): the
    /// bottom stack - conditions chip, button, credit pill, home indicator - covers ~184 pt of the map, so 200;
    /// 48 on top clears MapLibre's (i), which `MapView` moves to the top-left corner; 24 at the sides.
    static let edgePadding = UIEdgeInsets(top: 48, left: 24, bottom: 200, right: 24)

    private var route: MapRoute?
    private var paintedStyle: UIUserInterfaceStyle?
    private var target: Target?
    private var appliedTarget: Target?

    /// The one entry point `MapView` calls, from `makeUIView` and from every `updateUIView`.
    func update(_ mapView: MLNMapView, route: MapRoute?, target: Target) {
        if route != self.route || mapView.traitCollection.userInterfaceStyle != paintedStyle {
            self.route = route
            if let style = mapView.style {
                install(on: style, in: mapView)
            }
        }
        self.target = target
        applyCamera(mapView)
    }

    public func mapView(_ mapView: MLNMapView, didFinishLoading style: MLNStyle) {
        install(on: style, in: mapView)
        applyCamera(mapView)
    }

    public func mapViewDidFinishRenderingFrame(_ mapView: MLNMapView, fullyRendered: Bool) {
        applyCamera(mapView)
    }

    private func applyCamera(_ mapView: MLNMapView) {
        guard let target, target != appliedTarget else { return }
        switch target {
        case let .fit(west, south, east, north):
            // Not laid out yet: the next rendered frame asks again.
            guard mapView.bounds.width > 0, mapView.bounds.height > 0 else { return }
            let bounds = MLNCoordinateBounds(
                sw: CLLocationCoordinate2D(latitude: south, longitude: west),
                ne: CLLocationCoordinate2D(latitude: north, longitude: east)
            )
            mapView.setVisibleCoordinateBounds(bounds, edgePadding: Self.edgePadding,
                                               animated: false, completionHandler: nil)
        case let .center(latitude, longitude, zoom):
            mapView.setCenter(CLLocationCoordinate2D(latitude: latitude, longitude: longitude),
                              zoomLevel: zoom, animated: false)
        }
        appliedTarget = target
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

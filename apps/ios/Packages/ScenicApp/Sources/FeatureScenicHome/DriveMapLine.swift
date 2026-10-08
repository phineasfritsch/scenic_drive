import DesignSystem
import Foundation
import MapAdapter
import ScenicKit

/// The planned line as the drive map draws it (T-0324): one GeoJSON LineString with its bbox, carrying the plan
/// preview's own route-data line - the same OpenStreetMap data the preview card names.
enum DriveMapLine {
    static func route(for preview: PlanPreview) -> MapRoute? {
        let lats = preview.route.map(\.latitude)
        let lons = preview.route.map(\.longitude)
        guard preview.route.count >= 2, let south = lats.min(), let north = lats.max(),
              let west = lons.min(), let east = lons.max() else { return nil }
        let doc: [String: Any] = [
            "type": "FeatureCollection",
            "bbox": [west, south, east, north],
            "features": [[
                "type": "Feature",
                "properties": [String: String](),
                "geometry": ["type": "LineString", "coordinates": preview.route.map { [$0.longitude, $0.latitude] }],
            ]],
        ]
        guard let data = try? JSONSerialization.data(withJSONObject: doc) else { return nil }
        return MapRoute(geoJSON: data, dataCredit: PlanPreview.attribution, lineColor: DesignTokens.route, casingColor: DesignTokens.surface)
    }
}

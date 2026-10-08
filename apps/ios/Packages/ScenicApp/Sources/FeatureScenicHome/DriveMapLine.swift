import DesignSystem
import Foundation
import MapAdapter
import ScenicKit

/// The line the drive is on as the drive map draws it (T-0324; T-0328 R4: the session's current line, so a taken
/// reroute is drawn): one GeoJSON LineString with its bbox, carrying the plan preview's own route-data line - the
/// same OpenStreetMap data the preview card names.
enum DriveMapLine {
    static func route(for line: [Coordinate]) -> MapRoute? {
        let lats = line.map(\.latitude)
        let lons = line.map(\.longitude)
        guard line.count >= 2, let south = lats.min(), let north = lats.max(),
              let west = lons.min(), let east = lons.max() else { return nil }
        let geometry: [String: Any] = ["type": "LineString", "coordinates": line.map { [$0.longitude, $0.latitude] }]
        let properties: [String: String] = [:]
        let feature: [String: Any] = ["type": "Feature", "properties": properties, "geometry": geometry]
        let doc: [String: Any] = ["type": "FeatureCollection", "bbox": [west, south, east, north], "features": [feature]]
        guard let data = try? JSONSerialization.data(withJSONObject: doc) else { return nil }
        return MapRoute(geoJSON: data, dataCredit: PlanPreview.attribution, lineColor: DesignTokens.route, casingColor: DesignTokens.surface)
    }
}

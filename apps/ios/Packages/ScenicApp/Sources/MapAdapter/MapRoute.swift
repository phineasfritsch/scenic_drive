import Foundation
import SwiftUI

/// A drive's road line, ready to draw: the GeoJSON bytes, the box the camera fits, and the two colours.
///
/// ## Why the colours arrive as parameters
///
/// `MapAdapter` depends on MapLibre and nothing else (`Package.swift` says so and means it), so it cannot read
/// `DesignTokens`. The feature target passes `DesignTokens.route` and `DesignTokens.surface` in; the map view
/// resolves them against its own trait collection when it paints, so light and dark each get their row of the
/// token table (`route` #2563EB / #3B82F6, 6 pt over a 2 pt casing).
///
/// ## Why the box is READ and not computed
///
/// `ops/lib/make-route-geojson.py` writes a top-level `bbox` computed from the very positions it writes, and
/// `SaddlePeakGeometryTests` (Linux) refuses a file whose `bbox` is not its positions' extent. This type does no
/// arithmetic on the line at all - it reads four numbers, and a file without them is not a route it will draw.
public struct MapRoute: Equatable, Sendable {
    /// The FeatureCollection with one LineString, exactly as bundled.
    public let geoJSON: Data
    /// The line's extent, from the file's `bbox` ([west, south, east, north], RFC 7946 order).
    public let west: Double
    public let south: Double
    public let east: Double
    public let north: Double
    /// The `route` token, and the casing under it.
    public let lineColor: Color
    public let casingColor: Color
    /// What this line's DATA must be credited as - required, so no route is drawn without its credit. The
    /// footer shows it after the basemap's (`CreditLine.composed`): MLNShapeSource takes no attribution, so
    /// MapLibre's (i) sheet cannot carry it and the footer is the credit of record (rv1-t0236 B1).
    public let dataCredit: String

    /// The plan's Tokens row: a 6 pt line over a 2 pt casing on each side.
    public static let lineWidth = 6.0
    public static let casingWidth = 2.0

    /// A route from GeoJSON bytes, or `nil` when the bytes carry no four-number `bbox` or the credit is empty.
    public init?(geoJSON: Data, dataCredit: String, lineColor: Color, casingColor: Color) {
        guard let doc = try? JSONSerialization.jsonObject(with: geoJSON) as? [String: Any],
              let box = doc["bbox"] as? [Double], box.count == 4,
              box.allSatisfy({ $0.isFinite }), !dataCredit.isEmpty else {
            return nil
        }
        self.geoJSON = geoJSON
        self.dataCredit = dataCredit
        self.west = box[0]
        self.south = box[1]
        self.east = box[2]
        self.north = box[3]
        self.lineColor = lineColor
        self.casingColor = casingColor
    }

    /// The bundled line called `name`, or `nil` when this build does not carry it.
    ///
    /// Two lookups, as `BasemapResolver.archiveURL` does for the tiles: `subdirectory/name.ext` if Xcode 26's
    /// buildable folder kept the folder's shape, `name.ext` at the bundle root if it flattened it.
    public static func bundled(named name: String,
                               subdirectory: String,
                               withExtension ext: String,
                               dataCredit: String,
                               lineColor: Color,
                               casingColor: Color,
                               bundle: Bundle = .main) -> MapRoute? {
        let url = bundle.url(forResource: name, withExtension: ext, subdirectory: subdirectory)
            ?? bundle.url(forResource: name, withExtension: ext)
        guard let url, let data = try? Data(contentsOf: url) else {
            return nil
        }
        return MapRoute(geoJSON: data, dataCredit: dataCredit, lineColor: lineColor, casingColor: casingColor)
    }
}

import Foundation
import Handoff
import MapAdapter

/// Which basemap a given drive renders on, and in which appearance.
///
/// ## The mount is PER DRIVE, and that is not a convenience
///
/// `BasemapResolver.losAngeles()` returns the Protomaps style when `la.pmtiles` is on the device and
/// `MapStyle.maplibreDemoTiles` when it is not, with the credit travelling inside the returned value
/// either way. The archive covers `-119.0,33.7,-117.85,34.45` (`services/etl/regions/la/region.json`)
/// and nothing else. The Skyline loop is centred on the Peninsula, roughly 500 km north of that box:
/// mounting the LA basemap globally would draw an EMPTY map under the Protomaps credit whenever the
/// Bay Area drive is selected - tiles credited to OpenStreetMap and Protomaps with no OpenStreetMap
/// data anywhere on screen, which is the exact failure `MapStyle` exists to make impossible. So the
/// Skyline drive keeps the demo case, honestly credited to MapLibre and Natural Earth, until a Bay
/// Area archive exists.
///
/// ## Why the caller must keep this off the body's hot path
///
/// `BasemapResolver.losAngeles` is not a lookup: on the success path it MATERIALISES a style document
/// into the caches directory (`ScenicStyleDocument`) and touches the bundle and the file system on the
/// way. SwiftUI re-runs `body` whenever anything it reads changes, and it may re-run a `View`'s
/// property initialisers as it rebuilds the value, so neither is a place to call this. The resolved
/// style is held in `@State` by `ScenicHomeScreen` and this function is called exactly once per
/// selection change and once per appearance change, from `.task` and `.onChange`.
enum DriveBasemap {
    /// The style for this drive on this device, in this appearance.
    ///
    /// The returned `MapStyle` is the answer to both halves - what to draw and what to credit - so a
    /// caller that renders `style.url` under `style.attributionText` cannot get one without the other.
    /// A fallback to the demo tiles is a normal result, not an error: it is what every ios-compile run
    /// and every phone without the copied archive gets (see `BasemapResolver`).
    static func resolve(for drive: HandoffDrive, appearance: MapAppearance) -> MapStyle {
        switch drive {
        case .santaMonicaMountains:
            return BasemapResolver.losAngeles(appearance: appearance)
        case .skyline:
            return .maplibreDemoTiles
        }
    }
}

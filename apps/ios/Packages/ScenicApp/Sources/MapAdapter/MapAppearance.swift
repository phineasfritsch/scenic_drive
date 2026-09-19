import Foundation

/// Which of the two basemap styles an appearance asks for.
///
/// `services/tiles/make_styles.py` emits exactly two style documents - `scenic-light.json` and
/// `scenic-dark.json` - from one layer spec plus the `DesignTokens` table, so the two cannot drift
/// apart. This type is the app's half of that pair: it names them, it names the `MapStyle` case that
/// renders each, and it holds nothing else.
///
/// It is deliberately **not** SwiftUI's `ColorScheme`. `MapAdapter` may depend on MapLibre and on
/// nothing else (CLAUDE.md), and a basemap file name is not a property of SwiftUI's environment; the
/// screen that owns the environment converts at its own boundary, the same way `MapView` converts a
/// pair of `Double`s into a `CLLocationCoordinate2D` rather than teaching the core about CoreLocation.
public enum MapAppearance: String, Sendable, CaseIterable {
    case light
    case dark

    /// The embedded style document for this appearance, byte-equal to the file of the same name under
    /// `services/tiles/styles/`. See `ScenicLightStyle` for why it is a literal and not a resource.
    public var styleJSON: String {
        switch self {
        case .light:
            return ScenicLightStyle.json
        case .dark:
            return ScenicDarkStyle.json
        }
    }

    /// The `MapStyle` case that renders the LA PMTiles archive in this appearance.
    ///
    /// Only `BasemapResolver` should reach for this: a `MapStyle` returned from here has a `url`
    /// naming a document that `ScenicStyleDocument` has to have written first.
    public var protomapsStyle: MapStyle {
        switch self {
        case .light:
            return .protomapsLALight
        case .dark:
            return .protomapsLADark
        }
    }

    /// The generator's own file name for this appearance - `scenic-light.json` / `scenic-dark.json`.
    ///
    /// Built from `rawValue` rather than written twice: the materialised document on the device keeps
    /// the name of the file it was generated from, so a support-bundle listing of the caches directory
    /// says which style the renderer was handed.
    public var styleFileName: String {
        "scenic-\(rawValue).json"
    }
}

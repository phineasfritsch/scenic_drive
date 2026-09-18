import Foundation

/// Which basemap the map renders, and the credit that basemap requires.
///
/// The URL and its attribution travel together in one type on purpose. They are two halves of one
/// fact, and every way of splitting them ends with a style swapped in one file while the credit line
/// in another keeps naming the old tiles.
public enum MapStyle: String, Sendable, CaseIterable {
    /// **PLACEHOLDER.** MapLibre's public demo style - no key, no account, no cost.
    ///
    /// It is here because `services/tiles/` does not exist yet: there is no Bay Area PMTiles archive
    /// and no R2 bucket to serve one from. The skeleton's job is to prove a map draws on a phone and
    /// that a button hands off to Apple Maps, and this style does that without inventing a basemap
    /// that has not been built.
    ///
    /// It is **not** a fallback and must not become one. It renders country polygons and nothing else
    /// - no roads, no water detail, no place labels at the zoom this app lives at - so a release that
    /// quietly fell back to it would show a blank ocean where Skyline Boulevard should be. When the
    /// PMTiles style lands, this case goes away rather than moving to the back of an ordered list.
    case maplibreDemoTiles

    public var url: URL {
        switch self {
        case .maplibreDemoTiles:
            // Force-unwrapping a string literal that is a constant of this type: this URL cannot vary
            // at runtime, so there is no input that could make it nil and nothing to recover from.
            // swiftlint:disable:next force_unwrapping
            return URL(string: "https://demotiles.maplibre.org/style.json")!
        }
    }

    /// What this basemap must be credited as - the text to hand `AttributionFooter(text:)`.
    ///
    /// **This is deliberately not the plan's `© OpenStreetMap contributors · Protomaps`.** The demo
    /// tiles contain no OpenStreetMap data and are not served by Protomaps, so printing that string
    /// under them would credit two parties for somebody else's work and silently satisfy any check
    /// that greps for the final wording while the map underneath is wrong.
    ///
    /// The string is ours because the tiles ship none. Verified on 2026-09-18:
    ///
    ///   - `https://demotiles.maplibre.org/style.json` has one vector source, `maplibre`, pointing at
    ///     `https://demotiles.maplibre.org/tiles/tiles.json`;
    ///   - that TileJSON's `attribution` field is `" "` - a single space, i.e. empty. A renderer that
    ///     only echoes source attribution would therefore display nothing at all;
    ///   - `github.com/maplibre/demotiles` README: *"Country polygons are from Natural Earth Data."*
    ///
    /// Natural Earth is public domain and requires no credit; MapLibre is credited for the tiles and
    /// style. The line names both because a footer that renders empty is indistinguishable from a
    /// footer that is broken.
    public var attributionText: String {
        switch self {
        case .maplibreDemoTiles:
            return "© MapLibre · Natural Earth"
        }
    }
}

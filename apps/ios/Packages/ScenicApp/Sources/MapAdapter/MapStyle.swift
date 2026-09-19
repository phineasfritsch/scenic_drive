import Foundation

/// Which basemap the map renders, and the credit that basemap requires.
///
/// The URL and its attribution travel together in one type on purpose. They are two halves of one
/// fact, and every way of splitting them ends with a style swapped in one file while the credit line
/// in another keeps naming the old tiles. `BasemapResolver` therefore returns a value of this type
/// rather than a URL: choosing a basemap and choosing its credit are one act.
public enum MapStyle: String, Sendable, CaseIterable {
    /// The LA Protomaps basemap, light appearance - `services/tiles/styles/scenic-light.json` over
    /// `la.pmtiles`.
    case protomapsLALight

    /// The LA Protomaps basemap, dark appearance - `services/tiles/styles/scenic-dark.json` over the
    /// same archive.
    ///
    /// **Why two cases and not one with an appearance attached.** This enum is `RawRepresentable` and
    /// `CaseIterable`; a case with an associated value is neither, and both are load-bearing here (the
    /// raw value is what a future crash report or telemetry field prints, and `allCases` is what any
    /// exhaustiveness check walks). The two generated styles are two documents at two paths, so
    /// `url` cannot answer for "protomaps" without knowing which - and making `url` take an argument
    /// would let a caller ask for a URL without asking for the matching credit, which is the one thing
    /// this type exists to prevent.
    case protomapsLADark

    /// MapLibre's public demo style - no key, no account, no cost.
    ///
    /// **This is the fallback, and it is the only one.** It was written as a placeholder while
    /// `services/tiles/` did not exist, with a note saying it must never become a fallback; that note
    /// was protecting against a *silent* one - tiles quietly swapped underneath a credit line that
    /// keeps naming the old ones. That cannot happen here, because the credit is not a separate
    /// string: it is `attributionText` on this same case. So the case stays, as the honest answer to
    /// "this device has no LA archive" - which is every ios-compile run and every phone before the
    /// owner copies the file in (see `BasemapResolver`).
    ///
    /// What it draws is country polygons and nothing else - no roads, no water detail, no place labels
    /// at the zoom this app lives at. A device that falls back to it shows a blank ocean where Mulholland
    /// Drive should be, under a credit line that says MapLibre and Natural Earth rather than
    /// OpenStreetMap and Protomaps. That is the point: the map and the credit are wrong together or
    /// right together, never one without the other.
    case maplibreDemoTiles

    /// The plan's basemap credit, verbatim (CLAUDE.md: "Attribution (`© OpenStreetMap contributors ·
    /// Protomaps`) is visible on every map surface at every sheet detent").
    ///
    /// A named constant rather than two inline literals: the pin that will guard this string
    /// (P-ATTR-01, recorded for T-0197) can anchor on this identifier, and CLAUDE.md forbids anchoring
    /// a pin on a comment. The Protomaps tiles are an OpenStreetMap extract of the Protomaps basemap
    /// build (`services/tiles/README.md`: `build.protomaps.com/20260915.pmtiles`), so both parties
    /// named here are parties that actually contributed to what is on screen.
    public static let protomapsAttribution = "© OpenStreetMap contributors · Protomaps"

    /// What the demo tiles must be credited as - **deliberately not** `protomapsAttribution`.
    ///
    /// The demo tiles contain no OpenStreetMap data and are not served by Protomaps, so printing that
    /// string under them would credit two parties for somebody else's work and silently satisfy any
    /// check that greps for the final wording while the map underneath is wrong.
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
    public static let demoAttribution = "© MapLibre · Natural Earth"

    /// The style document to hand the renderer.
    ///
    /// For the protomaps cases this is the file `ScenicStyleDocument` writes into the caches
    /// directory - the generated style with its `pmtiles://la.pmtiles` placeholder replaced by the
    /// archive's real location on this device. One definition of that path, shared by the writer and
    /// by this property, so the two cannot disagree; and `BasemapResolver` is the only thing that
    /// returns these cases, only after that write succeeded.
    public var url: URL {
        switch self {
        case .protomapsLALight:
            return ScenicStyleDocument.documentURL(for: .light)
        case .protomapsLADark:
            return ScenicStyleDocument.documentURL(for: .dark)
        case .maplibreDemoTiles:
            // Force-unwrapping a string literal that is a constant of this type: this URL cannot vary
            // at runtime, so there is no input that could make it nil and nothing to recover from.
            // swiftlint:disable:next force_unwrapping
            return URL(string: "https://demotiles.maplibre.org/style.json")!
        }
    }

    /// What this basemap must be credited as - the text to hand `AttributionFooter(text:)`.
    ///
    /// Switched over the same cases as `url`, in the same file, so a case that draws Protomaps tiles
    /// cannot be given MapLibre's credit without the diff showing both lines.
    public var attributionText: String {
        switch self {
        case .protomapsLALight, .protomapsLADark:
            return MapStyle.protomapsAttribution
        case .maplibreDemoTiles:
            return MapStyle.demoAttribution
        }
    }
}

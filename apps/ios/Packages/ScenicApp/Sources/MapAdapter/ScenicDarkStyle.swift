import Foundation

/// The dark-appearance basemap style, byte-equal to `services/tiles/styles/scenic-dark.json`.
///
/// **Why a string literal and not a bundle resource.** `MapAdapter`'s target in
/// `apps/ios/Packages/ScenicApp/Package.swift` declares no `resources:`, so a `.json` dropped into
/// `Sources/MapAdapter/` is an unhandled file: SPM warns, does not copy it, and the app loads nothing.
/// Declaring it would mean editing that manifest - a SERIAL-ONLY file for the whole agent fleet
/// (CLAUDE.md) - for a document read once at launch. The literal is raw (`#"""`), so nothing in the JSON
/// is escaped and the bytes here are the file's bytes; the closing delimiter sits at column zero so the
/// compiler strips no indentation.
///
/// **It is a copy, and a copy drifts.** `services/tiles/make_styles.py` is the generator: every colour in
/// it is a `DesignTokens` value and `services/tiles/tests/test_style_tokens.py` asserts it. Regenerating
/// the JSON without regenerating this file would ship a basemap the repository no longer describes, so
/// T-0195 recorded the byte-equality assertion for T-0197/T-0201 to add to `services/tiles/tests`:
/// extract the lines between the literal delimiters and compare them with the JSON file.
///
/// `sources.protomaps.url` below is the placeholder `pmtiles://la.pmtiles`. `ScenicStyleDocument`
/// replaces it with the archive's real on-device URL; if it is ever missing, that substitution fails and
/// `BasemapResolver` falls back to the demo basemap rather than rendering a broken map under the
/// Protomaps credit.
public enum ScenicDarkStyle {
    /// The style document, exactly as `make_styles.py` emits it.
    public static let json = #"""
{
  "version": 8,
  "name": "Scenic Drive dark",
  "metadata": {
    "scenic:appearance": "dark",
    "scenic:attribution_owner": "DesignSystem.AttributionFooter",
    "scenic:archive": "la.pmtiles"
  },
  "sources": {
    "protomaps": {
      "type": "vector",
      "url": "pmtiles://la.pmtiles"
    },
    "route": {
      "type": "geojson",
      "data": {
        "type": "FeatureCollection",
        "features": []
      }
    }
  },
  "layers": [
    {
      "id": "background",
      "type": "background",
      "paint": {
        "background-color": "#0F172A"
      }
    },
    {
      "id": "earth",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "earth",
      "paint": {
        "fill-color": "#0F172A"
      }
    },
    {
      "id": "landcover",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landcover",
      "paint": {
        "fill-color": "#4ADE80",
        "fill-opacity": 0.22
      }
    },
    {
      "id": "landuse-green",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "paint": {
        "fill-color": "#4ADE80",
        "fill-opacity": 0.35
      },
      "filter": ["match", ["get", "pmap:kind"], ["park", "forest", "nature_reserve", "wood", "grass", "scrub", "cemetery"], true, false]
    },
    {
      "id": "landuse-built",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "landuse",
      "paint": {
        "fill-color": "rgba(255,255,255,0.08)",
        "fill-opacity": 0.6
      },
      "filter": ["match", ["get", "pmap:kind"], ["park", "forest", "nature_reserve", "wood", "grass", "scrub", "cemetery"], false, true]
    },
    {
      "id": "water",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "water",
      "paint": {
        "fill-color": "#192134"
      }
    },
    {
      "id": "buildings",
      "type": "fill",
      "source": "protomaps",
      "source-layer": "buildings",
      "paint": {
        "fill-color": "rgba(255,255,255,0.08)",
        "fill-opacity": 0.9
      },
      "minzoom": 13
    },
    {
      "id": "roads-minor",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "paint": {
        "line-color": "#94A3B8",
        "line-width": ["interpolate", ["linear"], ["zoom"], 11, 0.4, 14, 2.0],
        "line-opacity": 0.55
      },
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      },
      "filter": ["match", ["get", "pmap:kind"], ["highway", "major_road"], false, true]
    },
    {
      "id": "roads-major",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "paint": {
        "line-color": "#94A3B8",
        "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.6, 14, 4.0],
        "line-opacity": 0.85
      },
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      },
      "filter": ["==", ["get", "pmap:kind"], "major_road"]
    },
    {
      "id": "roads-motorway",
      "type": "line",
      "source": "protomaps",
      "source-layer": "roads",
      "paint": {
        "line-color": "#FBBF24",
        "line-width": ["interpolate", ["linear"], ["zoom"], 6, 0.8, 14, 5.0]
      },
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      },
      "filter": ["==", ["get", "pmap:kind"], "highway"]
    },
    {
      "id": "boundaries",
      "type": "line",
      "source": "protomaps",
      "source-layer": "boundaries",
      "paint": {
        "line-color": "#94A3B8",
        "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.5, 10, 1.2],
        "line-opacity": 0.5
      },
      "layout": {
        "line-cap": "butt",
        "line-join": "round"
      }
    },
    {
      "id": "route-casing",
      "type": "line",
      "source": "route",
      "paint": {
        "line-color": "#192134",
        "line-width": 10
      },
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      }
    },
    {
      "id": "route-line",
      "type": "line",
      "source": "route",
      "paint": {
        "line-color": "#3B82F6",
        "line-width": 6
      },
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      }
    },
    {
      "id": "route-scenic",
      "type": "line",
      "source": "route",
      "filter": ["==", ["get", "scenic"], true],
      "paint": {
        "line-color": "#4ADE80",
        "line-width": 6
      },
      "layout": {
        "line-cap": "round",
        "line-join": "round"
      }
    }
  ]
}
"""#
}

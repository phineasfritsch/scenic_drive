"""Emit the light and dark basemap styles from ONE layer spec and the DesignTokens table.

    python3 services/tiles/make_styles.py --out-dir services/tiles/styles
    python3 services/tiles/make_styles.py --check --archive <la.pmtiles>   # source-layers must exist

Two styles from one spec, because a light and a dark style maintained as two files drift: a layer added to
one is missing from the other and nobody sees it until somebody switches appearance. Every layer here names
a ROLE; the role resolves to a DesignTokens value per appearance, and `TOKENS` below is that table
transcribed from apps/ios/Packages/ScenicApp/Sources/DesignSystem/DesignTokens.swift.

THE LOWER-RIGHT CORNER. No source declares `attribution`, so the renderer's own control has nothing to add;
the corner belongs to DesignSystem's `AttributionFooter`, a SwiftUI view drawn ABOVE the map on its own 85%
`surface` ground, so a label the renderer places underneath cannot cover the credit. The symbol layers are
the label ids `LABEL_LAYERS` names and nothing else (T-0196 R6).

LABELS. `glyphs` and `sprite` hang off ONE variable, `ASSETS_BASE`, a placeholder like the archive's
`pmtiles://la.pmtiles`: the files live beside the archive under the same prefix (`basemap_assets.py`
builds and checks them; `ops/publish-tiles` uploads them). The app does NOT rewrite the base yet, so the
EMBEDDED styles (`styles/embedded/`, the Swift literals) carry no glyphs, sprite or symbol layer at all.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# DesignTokens.swift, light and dark. `border`'s dark value is not a hex triple - the plan writes it
# rgba(255,255,255,0.08) and flattening it would look right on bg and wrong on every surface.
TOKENS = {
    "bg": {"light": "#FFF7ED", "dark": "#0F172A"},
    "surface": {"light": "#FFFFFF", "dark": "#192134"},
    "fg": {"light": "#0F172A", "dark": "#F8FAFC"},
    "fgMuted": {"light": "#64748B", "dark": "#94A3B8"},
    "primary": {"light": "#EA580C", "dark": "#FB923C"},
    "onPrimary": {"light": "#FFFFFF", "dark": "#0F172A"},
    "route": {"light": "#2563EB", "dark": "#3B82F6"},
    "scenic": {"light": "#15803D", "dark": "#4ADE80"},
    "hazard": {"light": "#B45309", "dark": "#FBBF24"},
    "destructive": {"light": "#DC2626", "dark": "#F87171"},
    "border": {"light": "#FCEAE1", "dark": "rgba(255,255,255,0.08)"},
}

# Role -> token, per appearance. Roles differ by appearance where the two palettes order their lightness
# differently: in light, land is the pale ground and water is the darker mass; in dark, land is the darkest
# thing on screen and water has to come UP off it, not down into it.
ROLES = {
    "land": {"light": "bg", "dark": "bg"},
    "water": {"light": "fgMuted", "dark": "surface"},
    "green": {"light": "scenic", "dark": "scenic"},
    "built": {"light": "border", "dark": "border"},
    "road": {"light": "surface", "dark": "fgMuted"},
    "motorway": {"light": "hazard", "dark": "hazard"},
    "boundary": {"light": "fgMuted", "dark": "fgMuted"},
    "route": {"light": "route", "dark": "route"},
    "routeCasing": {"light": "surface", "dark": "surface"},
    "scenicEpisode": {"light": "scenic", "dark": "scenic"},
    "label": {"light": "fg", "dark": "fg"},
    "labelHalo": {"light": "bg", "dark": "bg"},
}

# The vector layers the archive actually carries, from `pmtiles show --metadata` on the built LA extract
# (T-0165's Log quotes the run). A source-layer not in here draws nothing, silently.
SOURCE_LAYERS = ("boundaries", "buildings", "earth", "landcover", "landuse", "places", "pois", "roads", "water")

SOURCE_ID = "protomaps"
ROUTE_SOURCE_ID = "route"
# Protomaps Basemap v4 names the class field `kind`; `pmap:kind` was v3's and the LA archive carries no such
# field (T-0196 M2), so a filter on it matched nothing.
KIND = "kind"
ASSETS_BASE = "basemap://"
GLYPHS = ASSETS_BASE + "glyphs/{fontstack}/{range}.pbf"
LABEL_LAYERS = ("roads-label", "places-label")
EMBEDDED_DIR = "embedded"


def fill(layer_id: str, source_layer: str, role: str, opacity: float | None = None, **extra) -> dict:
    paint = {"fill-color": {"role": role}}
    if opacity is not None:
        paint["fill-opacity"] = opacity
    return {"id": layer_id, "type": "fill", "source": SOURCE_ID, "source-layer": source_layer,
            "paint": paint, **extra}


def line(layer_id: str, source_layer: str, role: str, width, opacity: float | None = None, **extra) -> dict:
    paint = {"line-color": {"role": role}, "line-width": width}
    if opacity is not None:
        paint["line-opacity"] = opacity
    return {"id": layer_id, "type": "line", "source": SOURCE_ID, "source-layer": source_layer,
            "paint": paint, "layout": {"line-cap": "round", "line-join": "round"}, **extra}


def label(layer_id: str, source_layer: str, font: str, size, **layout) -> dict:
    """Names in `fg` on a `bg` halo: the same two tokens every other piece of text in the app uses."""
    return {"id": layer_id, "type": "symbol", "source": SOURCE_ID, "source-layer": source_layer,
            "layout": {"text-field": ["get", "name"], "text-font": [font], "text-size": size, **layout},
            "paint": {"text-color": {"role": "label"}, "text-halo-color": {"role": "labelHalo"},
                      "text-halo-width": 1.5}}


# Width by zoom, MapLibre interpolate form. Roads stay quiet: a driving map that shouts every residential
# street is unreadable at the speed this app is used.
def width(stops: list[tuple[int, float]]) -> list:
    out: list = ["interpolate", ["linear"], ["zoom"]]
    for zoom, value in stops:
        out += [zoom, value]
    return out


def spec(labels: bool = True) -> list[dict]:
    """The layer list, bottom to top, with roles where colours go; `labels=False` drops `LABEL_LAYERS`."""
    layers = [
        {"id": "background", "type": "background", "paint": {"background-color": {"role": "land"}}},
        fill("earth", "earth", "land"),
        fill("landcover", "landcover", "green", opacity=0.22),
        fill("landuse-green", "landuse", "green", opacity=0.35,
             filter=["match", ["get", KIND],
                     ["park", "forest", "nature_reserve", "wood", "grass", "scrub", "cemetery"], True, False]),
        fill("landuse-built", "landuse", "built", opacity=0.6,
             filter=["match", ["get", KIND],
                     ["park", "forest", "nature_reserve", "wood", "grass", "scrub", "cemetery"], False, True]),
        fill("water", "water", "water"),
        fill("buildings", "buildings", "built", opacity=0.9, minzoom=13),
        line("roads-minor", "roads", "road", width([(11, 0.4), (14, 2.0)]), opacity=0.55,
             filter=["match", ["get", KIND], ["highway", "major_road"], False, True]),
        line("roads-major", "roads", "road", width([(8, 0.6), (14, 4.0)]), opacity=0.85,
             filter=["==", ["get", KIND], "major_road"]),
        line("roads-motorway", "roads", "motorway", width([(6, 0.8), (14, 5.0)]),
             filter=["==", ["get", KIND], "highway"]),
        line("boundaries", "boundaries", "boundary", width([(4, 0.5), (10, 1.2)]), opacity=0.5,
             layout={"line-cap": "butt", "line-join": "round"}),
        # The route rides on an EMPTY GeoJSON source the app replaces at runtime with setData. The 6 pt line
        # over a 2 pt casing is DesignTokens' own description of the route line; it lives here rather than
        # being re-typed in MapAdapter, so the style is the one place the route's colour and weight are set.
        {"id": "route-casing", "type": "line", "source": ROUTE_SOURCE_ID,
         "paint": {"line-color": {"role": "routeCasing"}, "line-width": 10},
         "layout": {"line-cap": "round", "line-join": "round"}},
        {"id": "route-line", "type": "line", "source": ROUTE_SOURCE_ID,
         "paint": {"line-color": {"role": "route"}, "line-width": 6},
         "layout": {"line-cap": "round", "line-join": "round"}},
        {"id": "route-scenic", "type": "line", "source": ROUTE_SOURCE_ID,
         "filter": ["==", ["get", "scenic"], True],
         "paint": {"line-color": {"role": "scenicEpisode"}, "line-width": 6},
         "layout": {"line-cap": "round", "line-join": "round"}},
        # Labels last, so a route never hides the name of the road it is on.
        {**label("roads-label", "roads", "Noto Sans Regular", width([(12, 10), (16, 13)]),
                 **{"symbol-placement": "line"}), "minzoom": 12,
         "filter": ["match", ["get", KIND], ["highway", "major_road", "minor_road"], True, False]},
        {**label("places-label", "places", "Noto Sans Medium", width([(8, 11), (14, 15)])),
         "filter": ["match", ["get", KIND], ["locality", "neighbourhood"], True, False]},
    ]
    return layers if labels else [layer for layer in layers if layer["id"] not in LABEL_LAYERS]


def resolve(node, appearance: str):
    """Replace every {"role": X} with that role's token value for this appearance."""
    if isinstance(node, dict):
        if set(node) == {"role"}:
            role = node["role"]
            if role not in ROLES:
                raise KeyError(f"unknown role {role!r}")
            return TOKENS[ROLES[role][appearance]][appearance]
        return {k: resolve(v, appearance) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve(v, appearance) for v in node]
    return node


def style(appearance: str, archive_name: str, labels: bool = True) -> dict:
    """`labels=False` is the EMBEDDED style: no glyphs, no sprite, no symbol layer (T-0196 rv1 B1)."""
    layers = resolve(spec(labels), appearance)
    for layer in layers:
        if layer.get("source-layer") and layer["source-layer"] not in SOURCE_LAYERS:
            raise KeyError(f"{layer['id']} names source-layer {layer['source-layer']!r}, not in the archive")
    return {
        "version": 8,
        "name": f"Scenic Drive {appearance}",
        "metadata": {
            # Not decoration and not a comment: a reader of the file, and the style test, need to know that
            # the absence of `attribution` on the source is deliberate.
            "scenic:appearance": appearance,
            "scenic:attribution_owner": "DesignSystem.AttributionFooter",
            "scenic:archive": archive_name,
        },
        **({"glyphs": GLYPHS, "sprite": f"{ASSETS_BASE}sprites/v4/{appearance}"} if labels else {}),
        "sources": {
            # The app rewrites this to the on-device file URL after the first-run download. The committed
            # value is the artifact's own name so the style never ships pointing at a URL nobody built.
            SOURCE_ID: {"type": "vector", "url": f"pmtiles://{archive_name}"},
            ROUTE_SOURCE_ID: {"type": "geojson", "data": {"type": "FeatureCollection", "features": []}},
        },
        "layers": layers,
    }


def fields_named(node, out: set | None = None) -> set[str]:
    """Every feature property a layer reads with `["get", F]` - a field the archive must carry."""
    out = set() if out is None else out
    if isinstance(node, list):
        if len(node) == 2 and node[0] == "get" and isinstance(node[1], str):
            out.add(node[1])
        for value in node:
            fields_named(value, out)
    elif isinstance(node, dict):
        for value in node.values():
            fields_named(value, out)
    return out


def missing_fields(layers: list[dict], have: dict[str, set[str]]) -> list[str]:
    """`layer-id: field` for every field a protomaps layer reads that its source-layer does not declare."""
    return sorted(f"{layer['id']}: {field}" for layer in layers if layer.get("source") == SOURCE_ID
                  for field in fields_named(layer) - have.get(layer.get("source-layer"), set()))


def inlineable(node) -> bool:
    """A list with no object in it anywhere - a filter or an interpolate expression."""
    if isinstance(node, dict):
        return False
    if isinstance(node, list):
        return all(inlineable(v) for v in node)
    return True


def dumps(node, indent: int = 0) -> str:
    """JSON at two-space indent, with expressions kept on ONE line.

    `json.dumps(indent=2)` puts every element of `["interpolate", ["linear"], ["zoom"], 11, 0.4, 14, 2]`
    on its own line, which turns fourteen layers into 309 lines - over this repo's 300-line file cap, and
    unreadable besides: a filter you have to scroll is a filter nobody checks.
    """
    pad = " " * indent
    if isinstance(node, dict):
        if not node:
            return "{}"
        body = ",\n".join(f"{pad}  {json.dumps(k)}: {dumps(v, indent + 2)}" for k, v in node.items())
        return "{\n" + body + f"\n{pad}}}"
    if isinstance(node, list):
        if not node:
            return "[]"
        if inlineable(node):
            return json.dumps(node, separators=(", ", ": "))
        body = ",\n".join(f"{pad}  {dumps(v, indent + 2)}" for v in node)
        return "[\n" + body + f"\n{pad}]"
    return json.dumps(node)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the light and dark basemap styles.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "styles")
    parser.add_argument("--archive-name", default="la.pmtiles")
    parser.add_argument("--check", action="store_true", help="verify source-layers against a built archive")
    parser.add_argument("--archive", type=Path, help="the .pmtiles to check source-layers against")
    args = parser.parse_args(argv)

    if args.check:
        if not args.archive:
            print("make_styles: --check needs --archive", file=sys.stderr)
            return 2
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from check_pmtiles import read_metadata  # noqa: PLC0415 - same directory, no package

        vector_layers = read_metadata(args.archive)["vector_layers"]
        have = {layer["id"] for layer in vector_layers}
        missing = sorted(set(SOURCE_LAYERS) - have)
        if missing:
            print(f"make_styles: archive is missing source-layer(s): {missing}", file=sys.stderr)
            return 1
        unread = missing_fields(spec(), {layer["id"]: set(layer.get("fields", {})) for layer in vector_layers})
        if unread:
            print(f"make_styles: layers read field(s) the archive does not carry: {unread}", file=sys.stderr)
            return 1
        print(f"make_styles: all {len(SOURCE_LAYERS)} source-layers and every field the layers read present "
              f"in {args.archive.name}")
        return 0

    # The published styles carry the labels; the embedded ones (the Swift literals) carry none until the app
    # rewrites `basemap://` - a glyph URL that resolves to nothing stalls tile layout in MapLibre native.
    for directory, labels in ((args.out_dir, True), (args.out_dir / EMBEDDED_DIR, False)):
        directory.mkdir(parents=True, exist_ok=True)
        for appearance in ("light", "dark"):
            path = directory / f"scenic-{appearance}.json"
            text = dumps(style(appearance, args.archive_name, labels)) + "\n"
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"make_styles: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

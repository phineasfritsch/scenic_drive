"""Build the curvature oracle fixture from the Curvature project's own published Vermont output.

  python -m etl.oracle --list-ways          way ids of every SINGLE-WAY collection, one per line
  python -m etl.oracle --build FIXTURE.json --geojson SUBSET.geojson

The oracle is `inputs/vermont-curvature.kmz`, pinned by sha256 in the manifest. Every Placemark description
carries a table of the collection's constituent ways, each row holding the OSM way id, surface, that way's
curvature value, its length and its name. Those values come from their code, so they are something this repo
cannot talk itself into.

WHY ONLY SINGLE-WAY COLLECTIONS. Curvature runs its deflection filter across a whole collection - every way
in it joined end to end - so a way sharing a collection with others can have segments zeroed by a straight
run in a neighbour. Reproducing that would mean reproducing collection assembly, splitting and filtering too.
A collection containing exactly one way has no neighbour, so its published value is directly comparable to
`curvature.way_curvature`. Comparing the rest would be comparing against a different computation and calling
it agreement.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KMZ = ROOT / "inputs" / "vermont-curvature.kmz"

PLACEMARK = re.compile(r"<Placemark>(.*?)</Placemark>", re.S)
DESCRIPTION = re.compile(r"<description>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</description>", re.S)
NAME = re.compile(r"<name>(.*?)</name>", re.S)
# One row of the constituent-ways table: the way id inside an openstreetmap.org/way/N link, then surface,
# then that way's curvature. Anchored on the link because the id is the only field that cannot be reworded.
WAY_ROW = re.compile(
    r"<tr>\s*<td>\s*<a[^>]*openstreetmap\.org/way/(\d+)[^>]*>\s*\d+\s*</a>\s*</td>"
    r"\s*<td>([^<]*)</td>\s*<td>\s*([0-9.]+)\s*</td>",
    re.S,
)
COLLECTION_CURVATURE = re.compile(r"Curvature:\s*([0-9.]+)")


def collections(kmz: Path = KMZ):
    """Every Placemark as (name, collection_curvature, [(way_id, surface, curvature), ...])."""
    with zipfile.ZipFile(kmz) as z:
        doc = next(n for n in z.namelist() if n.endswith(".kml"))
        kml = z.read(doc).decode("utf-8", "replace")
    for block in PLACEMARK.findall(kml):
        m = DESCRIPTION.search(block)
        if not m:
            continue
        desc = html.unescape(m.group(1))
        rows = [(int(w), s.strip(), float(c)) for w, s, c in WAY_ROW.findall(desc)]
        if not rows:
            continue
        n = NAME.search(block)
        total = COLLECTION_CURVATURE.search(desc)
        yield (html.unescape(n.group(1)).strip() if n else "",
               float(total.group(1)) if total else None,
               rows)


def single_way_collections(kmz: Path = KMZ) -> dict[int, dict]:
    """way_id -> {name, curvature, surface} for collections that contain exactly one way."""
    out: dict[int, dict] = {}
    for name, _total, rows in collections(kmz):
        if len(rows) != 1:
            continue
        way_id, surface, curvature = rows[0]
        out[way_id] = {"name": name, "curvature": curvature, "surface": surface}
    return out


def load_geojson_ways(path: Path) -> dict[int, list[list[float]]]:
    """way_id -> [[lat, lon], ...] from `osmium export --add-unique-id=type_id` output.

    osmium writes GeoJSON coordinates as [lon, lat]; everything here is (lat, lon), because that is the order
    the Curvature code uses and mixing them silently halves every distance at this latitude.
    """
    ways: dict[int, list[list[float]]] = {}
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        if not line.startswith("{"):
            continue
        try:
            feature = json.loads(line)
        except json.JSONDecodeError:
            continue
        ident = str(feature.get("id") or feature.get("properties", {}).get("@id") or "")
        geom = feature.get("geometry") or {}
        if not ident.startswith("w") or geom.get("type") != "LineString":
            continue
        ways[int(ident[1:])] = [[lat, lon] for lon, lat in geom["coordinates"]]
    return ways


def build(fixture: Path, geojson: Path, kmz: Path = KMZ, limit: int | None = None) -> int:
    published = single_way_collections(kmz)
    ways = load_geojson_ways(geojson)
    records = []
    for way_id, meta in sorted(published.items()):
        coords = ways.get(way_id)
        if not coords or len(coords) < 3:
            continue
        records.append({
            "way_id": way_id,
            "name": meta["name"],
            "surface": meta["surface"],
            "oracle_curvature": meta["curvature"],
            "coords": [[round(lat, 7), round(lon, 7)] for lat, lon in coords],
        })
        if limit and len(records) >= limit:
            break
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(json.dumps({
        "source": "https://kml.roadcurvature.com/north_america/us/vermont.c_300.kmz",
        "note": "Single-way collections only: Curvature's deflection filter runs across a whole collection, "
                "so a way with collection-mates is not comparable to a per-way computation.",
        "ways": records,
    }, indent=1) + "\n", encoding="utf-8", newline="\n")
    return len(records)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="etl.oracle", description=__doc__)
    ap.add_argument("--kmz", type=Path, default=KMZ)
    ap.add_argument("--list-ways", action="store_true")
    ap.add_argument("--build", type=Path)
    ap.add_argument("--geojson", type=Path)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    if not args.kmz.is_file():
        print(f"oracle: {args.kmz} is missing - run ops/etl-fetch-inputs", file=sys.stderr)
        return 2

    if args.list_ways:
        for way_id in sorted(single_way_collections(args.kmz)):
            print(f"w{way_id}")
        return 0

    if args.build:
        if not args.geojson or not args.geojson.is_file():
            print("oracle: --build needs --geojson pointing at an osmium export of those ways", file=sys.stderr)
            return 2
        n = build(args.build, args.geojson, args.kmz, args.limit)
        print(f"oracle: wrote {n} way(s) to {args.build}")
        return 0 if n else 2

    total = sum(1 for _ in collections(args.kmz))
    single = len(single_way_collections(args.kmz))
    print(f"oracle: {total} collections, {single} of them single-way and directly comparable")
    return 0


if __name__ == "__main__":
    sys.exit(main())

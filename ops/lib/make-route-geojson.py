#!/usr/bin/env python3
"""Derive a drive's bundled route line from a recorded GraphHopper path - deterministically.

THE ONE WAY `apps/ios/ScenicDrive/Routes/*.geojson` IS MADE. The app draws the line in that file over the
map (MapAdapter.MapView's route layer) and fits its camera to the file's `bbox`; the file is committed, and
this script is how anybody re-derives it from the recorded response the engine produced, so the line on the
screen is never a hand-drawn or hand-edited shape.

    python ops/lib/make-route-geojson.py            # the Saddle Peak drive (T-0236), from PR #124's fixture
    python ops/lib/make-route-geojson.py --fixture F --out O --name N --tolerance-m T

WHAT IT DOES, in order:
  1. reads `paths[0].points` of the fixture - a GeoJSON LineString, `points_encoded: false` - and refuses
     anything else (an encoded polyline, fewer than two points, a coordinate that is not a pair of numbers);
  2. simplifies it with Douglas-Peucker at `--tolerance-m` METRES, measured in a local equirectangular plane
     about the path's mean latitude (at 34 N and a 30 km extent the plane's distortion is far below a metre),
     using the distance from a point to the SEGMENT, not to the infinite line - so every dropped vertex lies
     within the tolerance of the kept polyline, which is the property the Linux test leans on;
  3. rounds every kept coordinate to 5 decimals (about 1.1 m, `AppleMapsDirections.coordinateDecimals`);
  4. writes a FeatureCollection with ONE LineString feature and a top-level `bbox` computed from the ROUNDED
     coordinates ([minLon, minLat, maxLon, maxLat], RFC 7946 order), LF line endings, one position per line.

DETERMINISM: no clock, no randomness, no dict-order dependence (every key is written in a fixed order by
hand), fixed-precision formatting. Running it twice gives byte-identical output; the acceptance quotes the
sha256 of two runs.
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EARTH_RADIUS_M = 6_371_008.8  # ScenicKit.Geo.earthRadiusMeters - one radius across the two languages
DECIMALS = 5

DEFAULT_FIXTURE = "Tests/Fixtures/t0182/plan-pair/lambda-7.75.json"
DEFAULT_OUT = "apps/ios/ScenicDrive/Routes/saddle-peak.geojson"
DEFAULT_NAME = "saddle-peak"
# The STATED tolerance. 5 m is inside one lane-and-a-shoulder of the carriageway: the simplified line cannot
# leave the road it was recorded on by more than that, while the switchbacks of Tuna Canyon, Saddle Peak and
# Piuma - the reason the drive exists - keep their shape at any zoom the home screen shows.
DEFAULT_TOLERANCE_M = 5.0


def fail(message):
    print(f"make-route-geojson: {message}", file=sys.stderr)
    sys.exit(1)


def read_path(fixture):
    try:
        doc = json.loads(fixture.read_text(encoding="utf-8"))
        path = doc["paths"][0]
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        fail(f"cannot read paths[0] from {fixture}: {exc!r}")
    if path.get("points_encoded") is not False:
        fail(f"{fixture}: paths[0].points_encoded is {path.get('points_encoded')!r}, expected false")
    points = path.get("points") or {}
    if points.get("type") != "LineString":
        fail(f"{fixture}: paths[0].points.type is {points.get('type')!r}, expected LineString")
    coords = points.get("coordinates") or []
    out = []
    for c in coords:
        if not (isinstance(c, list) and len(c) >= 2
                and all(isinstance(v, (int, float)) and math.isfinite(v) for v in c[:2])):
            fail(f"{fixture}: not a coordinate: {c!r}")
        out.append((float(c[0]), float(c[1])))
    if len(out) < 2:
        fail(f"{fixture}: {len(out)} point(s); a line needs two")
    return out


def to_plane(coords):
    """(lon, lat) -> (x, y) metres in an equirectangular plane about the mean latitude."""
    lat0 = math.radians(sum(lat for _, lat in coords) / len(coords))
    k = math.cos(lat0)
    return [(EARTH_RADIUS_M * math.radians(lon) * k, EARTH_RADIUS_M * math.radians(lat)) for lon, lat in coords]


def segment_distance(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 == 0.0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def douglas_peucker(plane, tolerance):
    """Indices kept, ascending. Iterative, so no recursion limit; first and last are always kept."""
    keep = {0, len(plane) - 1}
    stack = [(0, len(plane) - 1)]
    while stack:
        first, last = stack.pop()
        worst, worst_index = -1.0, None
        for i in range(first + 1, last):
            d = segment_distance(plane[i], plane[first], plane[last])
            if d > worst:
                worst, worst_index = d, i
        if worst_index is not None and worst > tolerance:
            keep.add(worst_index)
            stack.append((first, worst_index))
            stack.append((worst_index, last))
    return sorted(keep)


def fmt(v):
    return format(round(v, DECIMALS), f".{DECIMALS}f")


def render(name, source, tolerance, source_points, kept):
    rounded = [(float(fmt(lon)), float(fmt(lat))) for lon, lat in kept]
    lons = [lon for lon, _ in rounded]
    lats = [lat for _, lat in rounded]
    bbox = ",".join(fmt(v) for v in (min(lons), min(lats), max(lons), max(lats)))
    positions = ",\n".join(f"        [{fmt(lon)},{fmt(lat)}]" for lon, lat in rounded)
    props = (f'"name":{json.dumps(name)},"source":{json.dumps(source)},'
             f'"tolerance_m":{json.dumps(tolerance)},"source_points":{source_points},"points":{len(rounded)}')
    return ("{\n"
            '  "type":"FeatureCollection",\n'
            f'  "bbox":[{bbox}],\n'
            '  "features":[{\n'
            '    "type":"Feature",\n'
            f"    \"properties\":{{{props}}},\n"
            '    "geometry":{"type":"LineString","coordinates":[\n'
            f"{positions}\n"
            "    ]}\n"
            "  }]\n"
            "}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--name", default=DEFAULT_NAME)
    ap.add_argument("--tolerance-m", type=float, default=DEFAULT_TOLERANCE_M)
    args = ap.parse_args(argv)
    if not (math.isfinite(args.tolerance_m) and args.tolerance_m > 0):
        fail(f"--tolerance-m must be a positive number of metres, got {args.tolerance_m}")

    fixture = ROOT / args.fixture
    coords = read_path(fixture)
    kept_indices = douglas_peucker(to_plane(coords), args.tolerance_m)
    kept = [coords[i] for i in kept_indices]
    text = render(args.name, args.fixture, args.tolerance_m, len(coords), kept)

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"make-route-geojson: {args.fixture} {len(coords)} points -> {len(kept)} points "
          f"at Douglas-Peucker tolerance {args.tolerance_m:g} m -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

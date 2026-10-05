#!/usr/bin/env python3
"""Bundle the Saddle Peak trip's menu for the home sheet from the SHIPPING `ops/plan --menu` - deterministically.

THE ONE WAY `apps/ios/ScenicDrive/Routes/saddle-peak-menu.json` IS MADE (T-0246). The home sheet shows one chip
per row of this file, draws the selected row's line in the route colour and the others muted, and hands the
selected row's URL to Apple Maps. Every number, road name and URL in it is the CLI's printed text; the lines are
the recorded paths those rows were computed from.

    python ops/lib/make-menu-bundle.py

WHAT IT DOES, in order:
  1. runs `bash ops/plan --menu <origin> <destination> --recorded <dir>` from the repository root and keeps its
     stdout WHOLE, line for line (`printed`) - the Linux test compares that list to `MenuCommand.run`'s;
  2. reads each `ROW i` / `URL i` pair: `extra=`, `km=`, `fun_km=` and `roads=` from the ROW line, the URL as the
     last word of the URL line - copied as printed, never re-formatted;
  3. finds each row's line in the recording: the path, in any *.json of `--recorded`, whose distance prints as the
     row's `km=` AND on whose vertices every pin of the row's URL lies (within PIN_ON_VERTEX_M after the URL's
     5-decimal rounding). The ladder repeats paths, so several files may match: they must carry the SAME
     coordinates, or the script refuses; no match refuses;
  4. simplifies each line with make-route-geojson.py's own Douglas-Peucker at its DEFAULT_TOLERANCE_M (T-0236's
     5 m) and rounds to its 5 decimals - imported, not retyped;
  5. rules the default row: the ONE row whose roads name `Saddle Peak Road` (the owner's first drive), or refuses;
  6. writes the bundle with every key in a fixed order, LF endings, one position per line, and a top-level `bbox`
     over every row's rounded positions ([west, south, east, north]).

DETERMINISM: no clock, no randomness, no dict order, the printed text copied verbatim. Two runs give
byte-identical output; the task Log quotes the sha256 of two.
"""
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "34.0944,-118.6013"
DESTINATION = "34.0365,-118.687"
RECORDED = "Tests/Fixtures/t0239/topanga-malibu"
COMMAND = ["--menu", ORIGIN, DESTINATION, "--recorded", RECORDED]
OUT = "apps/ios/ScenicDrive/Routes/saddle-peak-menu.json"
DEFAULT_ROAD = "Saddle Peak Road"
PIN_ON_VERTEX_M = 1.5
SCHEMA = "scenic-drive.drive-menu/1"


def fail(message):
    print(f"make-menu-bundle: {message}", file=sys.stderr)
    sys.exit(1)


def route_geojson():
    spec = importlib.util.spec_from_file_location("make_route_geojson", ROOT / "ops/lib/make-route-geojson.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_menu():
    done = subprocess.run(["bash", "ops/plan", *COMMAND], cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    if done.returncode != 0:
        fail(f"ops/plan --menu exited {done.returncode}: {done.stderr.decode('utf-8', 'replace')[-400:]}")
    return [line.rstrip("\r") for line in done.stdout.decode("utf-8").split("\n") if line.rstrip("\r")]


def read_rows(printed):
    rows = []
    for index, line in enumerate(l for l in printed if l.startswith("ROW ")):
        head, sep, roads = line.partition(" roads=")
        fields = dict(w.split("=", 1) for w in head.split(" ")[2:] if "=" in w)
        if not sep or not head.startswith(f"ROW {index} ") or not fields.get("extra", "").startswith("+"):
            fail(f"not a menu row: {line!r}")
        urls = [l for l in printed if l.startswith(f"URL {index} ")]
        if len(urls) != 1:
            fail(f"row {index} has {len(urls)} URL line(s)")
        rows.append({"extra": fields["extra"][1:-len("min")], "km": fields["km"], "fun_km": fields["fun_km"],
                     "roads": roads.split(", "), "url": urls[0].split(" ")[-1]})
    if not rows:
        fail("ops/plan --menu printed no rows")
    return rows


def pins(url):
    query = url.split("?", 1)[1].split("&")
    out = []
    for item in query:
        if item.startswith("waypoint="):
            lat, lon = item[len("waypoint="):].split(",")
            out.append((float(lat), float(lon)))
    return out


def metres(a_lat, a_lon, b_lat, b_lon, radius):
    k = math.cos(math.radians((a_lat + b_lat) / 2))
    return radius * math.hypot(math.radians(a_lon - b_lon) * k, math.radians(a_lat - b_lat))


def recorded_paths():
    for fixture in sorted((ROOT / RECORDED).glob("*.json")):
        doc = json.loads(fixture.read_text(encoding="utf-8"))
        for number, path in enumerate(doc.get("paths") or []):
            coords = [(float(c[0]), float(c[1])) for c in path["points"]["coordinates"]]
            yield f"{fixture.name}#{number}", float(path["distance"]), coords


def match(row, paths, radius):
    wanted = pins(row["url"])
    found = {}
    for name, distance, coords in paths:
        if f"{distance / 1000:.2f}" != row["km"]:
            continue
        if all(min(metres(lat, lon, c[1], c[0], radius) for c in coords) <= PIN_ON_VERTEX_M for lat, lon in wanted):
            found.setdefault(tuple(coords), []).append(name)
    if len(found) != 1:
        fail(f"row +{row['extra']} (km={row['km']}): {len(found)} distinct recorded path(s) carry its pins")
    (coords, names), = found.items()
    return list(coords), names


def render(printed, rows, default_row, tolerance, fmt):
    q = lambda v: json.dumps(v, ensure_ascii=False)
    everything = [p for row in rows for p in row["kept"]]
    bbox = ",".join(fmt(v) for v in (min(p[0] for p in everything), min(p[1] for p in everything),
                                     max(p[0] for p in everything), max(p[1] for p in everything)))
    out = ["{", f'  "schema":{q(SCHEMA)},', f'  "command":[{",".join(q(c) for c in COMMAND)}],', '  "printed":[']
    out.append(",\n".join(f"    {q(line)}" for line in printed))
    out += ["  ],", f'  "tolerance_m":{q(tolerance)},', f'  "default_row":{default_row},', f'  "bbox":[{bbox}],',
            '  "rows":[{']
    blocks = []
    for row in rows:
        positions = ",\n".join(f"      [{fmt(lon)},{fmt(lat)}]" for lon, lat in row["kept"])
        blocks.append("\n".join([
            f'    "extra_minutes":{row["extra"]},',
            f'    "fun_km":{row["fun_km"]},',
            f'    "roads":[{",".join(q(r) for r in row["roads"])}],',
            f'    "apple_maps_url":{q(row["url"])},',
            f'    "matched":[{",".join(q(n) for n in row["names"])}],',
            f'    "source_points":{row["source_points"]},',
            f'    "points":{len(row["kept"])},',
            '    "line":[',
            positions,
            "    ]"]))
    out.append("\n  },{\n".join(blocks))
    out += ["  }]", "}", ""]
    return "\n".join(out)


def main():
    mr = route_geojson()
    printed = run_menu()
    rows = read_rows(printed)
    paths = list(recorded_paths())
    for row in rows:
        coords, row["names"] = match(row, paths, mr.EARTH_RADIUS_M)
        kept = [coords[i] for i in mr.douglas_peucker(mr.to_plane(coords), mr.DEFAULT_TOLERANCE_M)]
        row["kept"] = [(float(mr.fmt(lon)), float(mr.fmt(lat))) for lon, lat in kept]
        row["source_points"] = len(coords)
    defaults = [i for i, row in enumerate(rows) if DEFAULT_ROAD in row["roads"]]
    if len(defaults) != 1:
        fail(f"{len(defaults)} row(s) name {DEFAULT_ROAD}; the default row is the ONE that does")
    text = render(printed, rows, defaults[0], mr.DEFAULT_TOLERANCE_M, mr.fmt)
    with open(ROOT / OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    summary = ", ".join(f"+{r['extra']} {r['source_points']}->{len(r['kept'])} pts" for r in rows)
    print(f"make-menu-bundle: {len(rows)} rows ({summary}); default row {defaults[0]} (+{rows[defaults[0]]['extra']}, "
          f"{DEFAULT_ROAD}); Douglas-Peucker {mr.DEFAULT_TOLERANCE_M:g} m -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

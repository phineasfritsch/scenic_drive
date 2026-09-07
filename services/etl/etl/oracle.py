"""Build the curvature oracle fixture from the Curvature project's own published Vermont output.

  python -m etl.oracle --list-ways          way ids of every SINGLE-WAY collection, one per line
  python -m etl.oracle --build FIXTURE.json --export SUBSET.geojsonseq
  ops/etl-curvature-fixture                 the whole thing end to end, from the pinned inputs

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

# The brief's 2%. Defined ONCE, here, because it was defined twice: `oracle_report.py` carried its own copy
# and no test imported that module, so sweeping it to 0.5 printed `fixture 400/400 = 100.000%` with the whole
# suite green (agent/reviewer-34, round 5). A second copy of a threshold is a second answer to the question
# the threshold exists to settle.
ORACLE_TOLERANCE = 0.02


def pinned_digest(name: str, manifest: Path | None = None) -> str | None:
    """The sha256 `inputs/manifest.yaml` pins for one input, or None if it names no digest.

    Read from the manifest rather than repeated in code. `oracle_select.build` used to write a hardcoded
    literal into the fixture's `source_sha256`, so the fixture asserted its own provenance and a rebuild from
    a DIFFERENT kmz still claimed the pinned digest - which is exactly the claim the field exists to make
    checkable.
    """
    path = manifest or (ROOT / "inputs" / "manifest.yaml")
    if not path.is_file():
        return None
    current, want = None, None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- name:"):
            current = line.split(":", 1)[1].strip()
        elif line.startswith("sha256:") and current == name:
            want = line.split(":", 1)[1].strip()
            break
    return want or None

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
PLACEMARK_COORDS = re.compile(r"<coordinates>(.*?)</coordinates>", re.S)
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


def kml_geometry(kmz: Path = KMZ) -> dict[int, list[tuple[float, float]]]:
    """The geometry Curvature actually computed over, per single-way collection, as (lat, lon).

    This is what makes condition 2 checkable at all: OSM moves, and the Placemark carries the coordinates as
    they were when the KMZ was generated. KML writes lon,lat[,alt] - the order is reversed here, because
    mixing them silently halves every distance at this latitude.
    """
    with zipfile.ZipFile(kmz) as z:
        doc = next(n for n in z.namelist() if n.endswith(".kml"))
        kml = z.read(doc).decode("utf-8", "replace")
    out: dict[int, list[tuple[float, float]]] = {}
    for block in PLACEMARK.findall(kml):
        m = DESCRIPTION.search(block)
        if not m:
            continue
        rows = WAY_ROW.findall(html.unescape(m.group(1)))
        if len(rows) != 1:
            continue
        cm = PLACEMARK_COORDS.search(block)
        if not cm:
            continue
        pts = []
        for token in cm.group(1).split():
            parts = token.split(",")
            if len(parts) >= 2:
                pts.append((float(parts[1]), float(parts[0])))
        out[int(rows[0][0])] = pts
    return out


def build(fixture: Path, export: Path, kmz: Path = KMZ, cap: int = 400, seed: int = 20260907):
    """Delegates to oracle_select, which owns the three selection conditions and the deterministic sample.

    Kept as a one-liner here so `python -m etl.oracle --build` still works, but the selection deliberately
    lives in one place. The previous version of this function implemented NONE of the conditions the fixture
    was actually built with - the real selection happened in throwaway scripts, and the fixture could not be
    regenerated from the repository at all. agent/reviewer-30 caught it.
    """
    from . import oracle_select
    return oracle_select.build(fixture, export, kmz, cap=cap, seed=seed)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="etl.oracle", description=__doc__)
    ap.add_argument("--kmz", type=Path, default=KMZ)
    ap.add_argument("--list-ways", action="store_true")
    ap.add_argument("--build", type=Path)
    ap.add_argument("--export", type=Path, help="osmium export -f geojsonseq of the oracle ways")
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
        if not args.export or not args.export.is_file():
            print("oracle: --build needs --export pointing at an osmium export of those ways; "
                  "ops/etl-curvature-fixture produces one", file=sys.stderr)
            return 2
        n, stages = build(args.build, args.export, args.kmz, cap=args.limit or 400)
        for stage, count in stages.items():
            print(f"  {stage:20s} {count:6d}")
        print(f"oracle: wrote {n} way(s) to {args.build}")
        return 0 if n else 2

    total = sum(1 for _ in collections(args.kmz))
    single = len(single_way_collections(args.kmz))
    print(f"oracle: {total} collections, {single} of them single-way and directly comparable")
    return 0


if __name__ == "__main__":
    sys.exit(main())

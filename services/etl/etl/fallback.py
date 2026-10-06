"""`python -m etl.fallback` - the tiny places-only corpus the app ships in its bundle (T-0270).

    python -m etl.fallback --places-osm work/t0266/la-places.osm.xml \
        --out ../../apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite --built-at 2026-10-06T00:00:00Z --region la

Before the first-run download there is no corpus on the device, so Surprise and the plan sheet's typed search
would be empty. This writes the file the bundle carries instead: the SHIPPING `placeallow.select` over an OSM
places stream (T-0266), capped per class by `CAPS`, handed to the SHIPPING `corpus.build` as an extract with no
ways - so the schema, application_id, schema_version, table_licenses, content_sha256 and build_complete are the
ones a full corpus gets, from the same writer - with meta.kind = 'fallback' (task Log, rulings F1-F4).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

from . import corpus, placeallow
from .segid import place_id

# Ruling F2: ONE ordered table, scenic first and cafes last. Within a class the rank is place_id ascending.
CAPS = (
    ("viewpoint", 200),
    ("peak", 200),
    ("waterfall", 200),
    ("beach", 200),
    ("trailhead", 200),
    ("museum", 150),
    ("garden", 150),
    ("park", 400),
    ("town", 150),
    ("cafe", 50),
)

# Ruling F3: 1 MiB, refused with corpus.py's own `>=` rule and exit code; the file is left on disk.
FALLBACK_BUDGET_BYTES = 1048576

KIND = "fallback"


def choose(places: list) -> list:
    """The capped selection, in CAPS order then place_id order. A class outside CAPS is REFUSED: a new
    allowlist class has to be ruled into the table, never kept or dropped by default."""
    caps = dict(CAPS)
    by_class = {cls: [] for cls in caps}
    for place in places:
        if place["cls"] not in caps:
            raise ValueError(f"place class {place['cls']!r} has no cap in etl.fallback.CAPS")
        by_class[place["cls"]].append(place)
    chosen = []
    for cls, cap in CAPS:
        ranked = sorted(by_class[cls], key=lambda p: place_id(p["osm_type"], p["osm_id"]))
        chosen.extend(ranked[:cap])
    return chosen


def build(places_osm, out_path, built_at: str, region: str) -> dict:
    """Select, cap, and write through corpus.build. Returns corpus.build's report plus the kept count per
    class; raises corpus.CorpusTooLargeError at or over FALLBACK_BUDGET_BYTES."""
    places, _counts = placeallow.select(places_osm)
    chosen = choose(places)
    with tempfile.TemporaryDirectory() as tmp:
        extract = os.path.join(tmp, "fallback-extract.json")
        with open(extract, "w", encoding="utf-8") as handle:
            json.dump({"region": region, "ways": [], "places": chosen}, handle)
        report = corpus.build(extract, out_path, built_at, region=region,
                              budget_bytes=FALLBACK_BUDGET_BYTES, kind=KIND)
    report["kept"] = {cls: sum(1 for p in chosen if p["cls"] == cls) for cls, _cap in CAPS}
    report["selected_from"] = len(places)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etl.fallback", description=__doc__.splitlines()[0])
    parser.add_argument("--places-osm", required=True, help="the OSM XML places stream placeallow reads")
    parser.add_argument("--out", required=True, help="the fallback .sqlite to write; overwritten if it exists")
    parser.add_argument("--built-at", required=True, metavar="ISO", help="build stamp; an INPUT, no clock")
    parser.add_argument("--region", required=True, help="meta.region, e.g. la")
    args = parser.parse_args(argv)
    try:
        corpus.compact_built_at(args.built_at)
    except ValueError:
        print(f"--built-at must be YYYY-MM-DDTHH:MM:SSZ, got {args.built_at!r}", file=sys.stderr)
        return 2
    try:
        report = build(args.places_osm, args.out, args.built_at, args.region)
    except corpus.CorpusTooLargeError as too_large:
        print(f"FALLBACK REFUSED {too_large}", file=sys.stderr)
        return corpus.BUDGET_EXIT
    print("FALLBACK selected_from=%d places=%d " % (report["selected_from"], sum(report["kept"].values()))
          + " ".join("%s=%d" % (cls, n) for cls, n in report["kept"].items()))
    print(f"FALLBACK bytes={report['bytes']} budget={report['budget_bytes']}")
    print(f"FALLBACK content_sha256={report['content_sha256']}")
    print(f"FALLBACK file_sha256={report['file_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

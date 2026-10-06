"""The places stages of a region build (T-0274): the T-0266 osmium pass and the T-0270 bundle corpus.

    places    the allowlist osmium pass over the region's OWN input, the UNFILTERED clip <region>.osm.pbf
              (the keep-pass clip holds no cafe, museum, garden, trailhead or place tags - T-0266's INPUT),
              with the SHIPPING `placeallow.keep_expressions()`, then `osmium cat` to <region>-places.osm.xml;
              prints the osmium counts and placeallow's PLACES count line over the stream it wrote
    fallback  the SHIPPING `etl.fallback.main` over that stream into the store as <region>-corpus-fallback.sqlite,
              then the same bytes to the region's bundle path under --bundle-root (the checkout by default,
              /repo in the ETL image) - for LA, the file the app bundles, at T-0270's build stamp

A region with no BUNDLE entry is refused: the bundle ships one region's places, at one stamp, and a rebuild
under any other stamp would not be the committed file.
"""
from __future__ import annotations

import hashlib
import pathlib
import shutil

from etl import fallback, placeallow

from . import osm

REPO = pathlib.Path(__file__).resolve().parents[3]
BUNDLE = {"la": ("apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite", "2026-10-06T00:00:00Z")}
REFUSED = 2


def osmium_pass(layout, names, jobs) -> int:
    del names, jobs
    if not layout.source.is_file():
        print("PLACES REFUSED: no unfiltered clip %s" % layout.source, flush=True)
        return REFUSED
    osm.run("osmium", "tags-filter", layout.source, *placeallow.keep_expressions(),
            "-o", layout.places_pbf, "--overwrite")
    osm.run("osmium", "cat", layout.places_pbf, "-o", layout.places_xml, "--overwrite")
    counts = [int(osm.run("osmium", "fileinfo", "-e", "-g", "data.count.%s" % kind, layout.places_pbf).strip())
              for kind in ("nodes", "ways", "relations")]
    print("PLACES OSM nodes=%d ways=%d relations=%d xml_bytes=%d"
          % (*counts, layout.places_xml.stat().st_size), flush=True)
    print(placeallow.count_line(placeallow.select(layout.places_xml)[1]), flush=True)
    return 0


def bundle(layout, names, jobs, root=None) -> int:
    del names, jobs
    if layout.region not in BUNDLE:
        print("BUNDLE REFUSED: region %s has no bundle in %s" % (layout.region, sorted(BUNDLE)), flush=True)
        return REFUSED
    path, built_at = BUNDLE[layout.region]
    code = fallback.main(["--places-osm", str(layout.places_xml), "--out", str(layout.fallback),
                          "--built-at", built_at, "--region", layout.region])
    if code != 0:
        return code
    target = pathlib.Path(root if root is not None else REPO) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(layout.fallback, target)
    print("BUNDLE %s sha256=%s" % (target, hashlib.sha256(target.read_bytes()).hexdigest()), flush=True)
    return 0

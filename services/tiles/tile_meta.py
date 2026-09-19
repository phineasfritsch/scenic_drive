"""Region and build provenance for a PMTiles artifact: the metadata stamp and the sidecar.

Two facts have to travel with the extract. `meta.region` and `built_at` are P-DATA-03's, and go-pmtiles
CAN carry them: `pmtiles edit --metadata=FILE` replaces the archive's JSON metadata wholesale, so `merge`
below reads the source metadata out of the archive, adds ours, and hands the result back to `edit`. The v3
header has no free-form field - it is 127 fixed bytes - so nothing of ours goes there.

The sidecar exists for the two facts that cannot be inside the file: its own byte count and its own sha256.
A first-run download sheet needs both before it has the file. Everything else in the sidecar is a copy of
what the archive already carries, which is why `check_pmtiles.py` reads the archive, not the sidecar.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Keys this module owns inside the archive metadata. Listed once so `merge` and the sidecar agree, and so a
# reader can see exactly what we added to somebody else's metadata.
OURS = ("region", "built_at", "bbox", "maxzoom", "source_build", "source_url", "source_replication_time")


def _provenance(args: argparse.Namespace, src: dict) -> dict:
    """Our keys, including whatever the source build says about the OSM data it was cut from."""
    return {
        "region": args.region,
        "built_at": args.built_at,
        "bbox": args.bbox,
        "maxzoom": int(args.maxzoom),
        "source_build": args.build,
        "source_url": args.source_url,
        # Planetiler stamps the OSM replication time it imported. That outlives the build URL, which
        # build.protomaps.com deletes after a few days, so it is the durable provenance of the tiles.
        "source_replication_time": src.get("planetiler:osm:osmosisreplicationtime", ""),
    }


def merge(args: argparse.Namespace) -> int:
    src = json.loads(Path(args.src_meta).read_text(encoding="utf-8"))
    if not isinstance(src, dict):
        print(f"tile_meta: {args.src_meta} is not a JSON object", file=sys.stderr)
        return 1
    if "vector_layers" not in src:
        # Writing this back would destroy the layer declarations every style depends on.
        print("tile_meta: source metadata has no vector_layers - refusing to write it back", file=sys.stderr)
        return 1
    merged = dict(src)
    merged.update(_provenance(args, src))
    Path(args.out).write_text(json.dumps(merged, sort_keys=True), encoding="utf-8")
    kept = len(src)
    print(f"tile_meta: merged {len(OURS)} keys into {kept} source keys -> {args.out}")
    return 0


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sidecar(args: argparse.Namespace) -> int:
    archive = Path(args.archive)
    if not archive.is_file():
        print(f"tile_meta: no archive at {archive}", file=sys.stderr)
        return 1
    record = _provenance(args, {})
    # The source replication time is read back out of the archive we just stamped rather than passed in
    # again, so the sidecar cannot claim a provenance the file does not carry.
    from check_pmtiles import read_metadata  # noqa: PLC0415 - same directory, no package

    inside = read_metadata(archive)
    record["source_replication_time"] = inside.get("source_replication_time", "")
    record["bytes"] = archive.stat().st_size
    record["sha256"] = sha256_of(archive)
    record["file"] = archive.name
    Path(args.out).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--region", required=True)
    parser.add_argument("--bbox", required=True)
    parser.add_argument("--maxzoom", required=True)
    parser.add_argument("--build", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--built-at", required=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("merge", help="write the metadata JSON for `pmtiles edit --metadata`")
    m.add_argument("--src-meta", required=True)
    m.add_argument("--out", required=True)
    _common(m)
    m.set_defaults(func=merge)

    s = sub.add_parser("sidecar", help="write <archive>.json beside the artifact")
    s.add_argument("--archive", required=True)
    s.add_argument("--out", required=True)
    _common(s)
    s.set_defaults(func=sidecar)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())

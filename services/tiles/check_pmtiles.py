"""Refuse a PMTiles artifact that does not cover its region, or does not fit the 120 MB budget.

Run it on the built file (`build-la.sh` step 6 does) or by hand:

    python3 services/tiles/check_pmtiles.py <file.pmtiles> --region-json services/etl/regions/la/region.json

The v3 header is parsed here in pure Python rather than shelled out to the go-pmtiles image, for two
reasons. A check that needs docker cannot run in CI, where there is none; and a bad fixture can then be
constructed in-process - 127 bytes with the bounds moved - which is how this check is seen red without
downloading a wrong archive from somewhere. The parser is only worth trusting if it agrees with the tool,
so its output is compared against `pmtiles show --header-json` on the real build in T-0165's Log.

Exit 0 when every property holds; exit 1 naming each one that does not.
"""

from __future__ import annotations

import argparse
import gzip
import json
import struct
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HEADER_BYTES = 127
MAGIC = b"PMTiles"
SPEC_VERSION = 3
# 120 MB, the plan's M2 exit ceiling, as 120 * 1024 * 1024.
BUDGET_BYTES = 125_829_120
# P-DATA-03: built_at under 30 days.
MAX_AGE_DAYS = 30
# Internal-compression enum from the PMTiles v3 spec; only these two are produced by go-pmtiles today.
COMPRESSION_NONE = 1
COMPRESSION_GZIP = 2


def parse_header(path: Path) -> dict:
    """The fixed 127-byte v3 header. Raises ValueError on anything that is not one."""
    blob = path.read_bytes()[:HEADER_BYTES] if path.stat().st_size >= HEADER_BYTES else b""
    if len(blob) < HEADER_BYTES:
        raise ValueError(f"{path.name} is {path.stat().st_size} bytes, shorter than a {HEADER_BYTES}-byte header")
    if blob[:7] != MAGIC:
        raise ValueError(f"{path.name} does not start with the PMTiles magic")
    version = blob[7]
    if version != SPEC_VERSION:
        raise ValueError(f"{path.name} is spec version {version}, not {SPEC_VERSION}")
    (root_off, root_len, meta_off, meta_len, leaf_off, leaf_len, data_off, data_len,
     addressed, entries, contents) = struct.unpack_from("<11Q", blob, 8)
    clustered, internal_compression, tile_compression, tile_type, min_zoom, max_zoom = struct.unpack_from(
        "<6B", blob, 96
    )
    min_lon, min_lat, max_lon, max_lat = (v / 1e7 for v in struct.unpack_from("<4i", blob, 102))
    return {
        "spec_version": version,
        "root_offset": root_off, "root_length": root_len,
        "metadata_offset": meta_off, "metadata_length": meta_len,
        "leaf_directory_offset": leaf_off, "leaf_directory_length": leaf_len,
        "tile_data_offset": data_off, "tile_data_length": data_len,
        "addressed_tiles_count": addressed,
        "tile_entries_count": entries,
        "tile_contents_count": contents,
        "clustered": bool(clustered),
        "internal_compression": internal_compression,
        "tile_compression": tile_compression,
        "tile_type": tile_type,
        "min_zoom": min_zoom,
        "max_zoom": max_zoom,
        "min_lon": min_lon, "min_lat": min_lat, "max_lon": max_lon, "max_lat": max_lat,
    }


def read_metadata(path: Path) -> dict:
    """The archive's own JSON metadata, decompressed. {} when there is none."""
    header = parse_header(path)
    length = header["metadata_length"]
    if length == 0:
        return {}
    with path.open("rb") as handle:
        handle.seek(header["metadata_offset"])
        blob = handle.read(length)
    if header["internal_compression"] == COMPRESSION_GZIP:
        blob = gzip.decompress(blob)
    elif header["internal_compression"] != COMPRESSION_NONE:
        raise ValueError(f"unsupported internal compression {header['internal_compression']}")
    return json.loads(blob.decode("utf-8"))


def bbox_from_region(region_json: Path) -> tuple[float, float, float, float]:
    box = json.loads(region_json.read_text(encoding="utf-8"))["bbox"]
    return (box["min_lon"], box["min_lat"], box["max_lon"], box["max_lat"])


def check(path: Path, bbox: tuple[float, float, float, float], *, region: str | None = None,
          budget: int = BUDGET_BYTES, max_age_days: int = MAX_AGE_DAYS,
          now: datetime | None = None) -> list[str]:
    """Every failure, named. Empty list = the artifact is publishable."""
    failures: list[str] = []
    try:
        header = parse_header(path)
    except ValueError as exc:
        return [f"not a PMTiles v3 archive: {exc}"]

    min_lon, min_lat, max_lon, max_lat = bbox
    # Cover, not equal: an extract's bounds are snapped out to whole tiles, so they are always at least the
    # requested box. Anything short of it is a hole in the map where the region says there are roads.
    if header["min_lon"] > min_lon or header["min_lat"] > min_lat \
            or header["max_lon"] < max_lon or header["max_lat"] < max_lat:
        failures.append(
            "header bounds ({:.6f},{:.6f},{:.6f},{:.6f}) do not cover the region bbox "
            "({},{},{},{})".format(header["min_lon"], header["min_lat"], header["max_lon"],
                                   header["max_lat"], min_lon, min_lat, max_lon, max_lat)
        )

    size = path.stat().st_size
    if size > budget:
        failures.append(f"{size} bytes exceeds the {budget}-byte budget by {size - budget}")

    try:
        meta = read_metadata(path)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        failures.append(f"metadata unreadable: {exc}")
        return failures

    if region is not None and meta.get("region") != region:
        failures.append(f"meta.region is {meta.get('region')!r}, expected {region!r} (P-DATA-03)")

    stamp = meta.get("built_at")
    if not stamp:
        failures.append("meta.built_at is missing (P-DATA-03)")
    else:
        try:
            built = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        except ValueError:
            failures.append(f"meta.built_at {stamp!r} is not an ISO-8601 timestamp (P-DATA-03)")
        else:
            reference = now or datetime.now(timezone.utc)
            if built < reference - timedelta(days=max_age_days):
                failures.append(f"meta.built_at {stamp} is older than {max_age_days} days (P-DATA-03)")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refuse a PMTiles that misses its region or its budget.")
    parser.add_argument("archive", type=Path)
    parser.add_argument("--region-json", type=Path, required=True,
                        help="the region file the bbox is READ from, never typed")
    parser.add_argument("--budget-bytes", type=int, default=BUDGET_BYTES)
    parser.add_argument("--max-age-days", type=int, default=MAX_AGE_DAYS)
    args = parser.parse_args(argv)

    region = json.loads(args.region_json.read_text(encoding="utf-8"))
    failures = check(args.archive, bbox_from_region(args.region_json), region=region["id"],
                     budget=args.budget_bytes, max_age_days=args.max_age_days)
    if failures:
        print(f"PMTILES REFUSED: {args.archive}")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    header = parse_header(args.archive)
    print("PMTILES OK: {} region={} bytes={} zoom={}-{} bounds=({:.6f},{:.6f},{:.6f},{:.6f})".format(
        args.archive.name, region["id"], args.archive.stat().st_size,
        header["min_zoom"], header["max_zoom"],
        header["min_lon"], header["min_lat"], header["max_lon"], header["max_lat"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Refuse a PMTiles artifact that does not cover its region, is too coarse, is empty, or misses the budget.

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
# T-0165 R3 ruled maxzoom 14 by measurement (z15 is 197 MB, over the ceiling; z13 is 20 MB and needlessly
# coarse). The budget limb alone cannot see this: every zoom BELOW 14 is smaller, so `--maxzoom 12` yields a
# 20 MB archive that passes the budget while the map goes soft two zoom levels early. This is that floor.
MIN_MAXZOOM = 14
# rv1-pr109 R2. `tile_entries_count == 0` was the only tile limb, so a 330-byte truncation carrying three
# entries - right bounds, right stamp, inside the budget - came back publishable. The measured LA build
# carries 2549 entries, and this floor is an order of magnitude under it (2549/10 = 254.9, rounded up to a
# power of two): far enough below that a re-pinned planet build or a bbox nudged by a tenth of a degree
# cannot trip it, far enough above 3 that a truncated or half-written archive cannot pass.
MIN_TILE_ENTRIES = 256
# The same failure measured in bytes. Deliberately NOT one order of magnitude under the measured
# 63,520,949 but about sixty: a byte floor's job is to catch a truncation or an interrupted download, not to
# track the size of the build. A floor set near the real size refuses the first legitimate smaller region
# and gets lowered in a hurry by whoever hits it, which is how a floor stops meaning anything.
MIN_BYTES = 1_048_576
# rv1-pr109 R1. The age limb was one-sided, so `built_at` in 2099 passed it. The recipe stamps built_at at
# step 1 and runs this check at step 6 on the SAME clock minutes later; across two hosts the only legitimate
# gap is NTP drift, which is seconds. One hour is three orders of magnitude under MAX_AGE_DAYS, so it cannot
# mask a stale build, and it still refuses every wrong-DATE stamp - a year typed wrong, a host set ahead.
MAX_FUTURE_SKEW = timedelta(hours=1)
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
          min_maxzoom: int = MIN_MAXZOOM, min_entries: int = MIN_TILE_ENTRIES,
          min_bytes: int = MIN_BYTES, max_future_skew: timedelta = MAX_FUTURE_SKEW,
          now: datetime | None = None) -> list[str]:
    """Every failure, named. Empty list = the artifact is publishable.

    The floors are parameters rather than constants read from the module body so a second region can state
    its own numbers instead of inheriting the ones measured off the LA build.
    """
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

    if header["max_zoom"] < min_maxzoom:
        failures.append(
            f"header max_zoom {header['max_zoom']} is below the required {min_maxzoom} "
            "(T-0165 R3: z14 is the highest zoom inside the 120 MB budget, and a coarser build is a "
            "smaller file that passes the budget by giving up detail)"
        )

    # A directory-less archive is the failure mode a size check cannot see from the other side: an extract
    # that wrote a header and no tiles is small, in-bounds, correctly stamped, and draws nothing at all.
    entries = header["tile_entries_count"]
    if entries == 0:
        failures.append("header tile_entries_count is 0: the archive carries no tiles")
    elif entries < min_entries:
        failures.append(
            f"header tile_entries_count {entries} is below the floor of {min_entries} "
            "(the measured LA build carries 2549): the archive is truncated or was cut to a sliver"
        )

    size = path.stat().st_size
    if size > budget:
        failures.append(f"{size} bytes exceeds the {budget}-byte budget by {size - budget}")
    elif size < min_bytes:
        failures.append(
            f"{size} bytes is below the {min_bytes}-byte floor: a metro extract at z14 is tens of "
            "megabytes, so this is a truncation or an interrupted download, not a map"
        )

    try:
        meta = read_metadata(path)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        failures.append(f"metadata unreadable: {exc}")
        return failures

    if region is not None and meta.get("region") != region:
        failures.append(f"meta.region is {meta.get('region')!r}, expected {region!r} (P-DATA-03)")

    # The two zooms are written by different steps - the header by `pmtiles extract`, the metadata by the
    # recipe's own stamp - so they disagree exactly when a rebuild changed one and not the other, and the
    # sidecar and the app's download sheet believe the metadata.
    if meta.get("maxzoom") is None:
        failures.append("meta.maxzoom is missing (the recipe stamps it beside region and built_at)")
    elif int(meta["maxzoom"]) != header["max_zoom"]:
        failures.append(
            f"meta.maxzoom {meta['maxzoom']} disagrees with the header's max_zoom {header['max_zoom']}"
        )

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
            # A stamp written without an offset is UTC here: the recipe writes `date -u`, and comparing a
            # naive datetime against an aware one raises instead of refusing, which is not a refusal.
            if built.tzinfo is None:
                built = built.replace(tzinfo=timezone.utc)
            if built < reference - timedelta(days=max_age_days):
                failures.append(f"meta.built_at {stamp} is older than {max_age_days} days (P-DATA-03)")
            elif built > reference + max_future_skew:
                failures.append(
                    f"meta.built_at {stamp} is in the future by more than the {max_future_skew} skew "
                    "tolerance: an age limb that only looks backwards passes a stamp from 2099"
                )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refuse a PMTiles that misses its region or its budget.")
    parser.add_argument("archive", type=Path)
    parser.add_argument("--region-json", type=Path, required=True,
                        help="the region file the bbox is READ from, never typed")
    parser.add_argument("--budget-bytes", type=int, default=BUDGET_BYTES)
    parser.add_argument("--max-age-days", type=int, default=MAX_AGE_DAYS)
    parser.add_argument("--min-maxzoom", type=int, default=MIN_MAXZOOM,
                        help=f"refuse an archive coarser than this max zoom (default {MIN_MAXZOOM})")
    args = parser.parse_args(argv)

    region = json.loads(args.region_json.read_text(encoding="utf-8"))
    failures = check(args.archive, bbox_from_region(args.region_json), region=region["id"],
                     budget=args.budget_bytes, max_age_days=args.max_age_days,
                     min_maxzoom=args.min_maxzoom)
    if failures:
        print(f"PMTILES REFUSED: {args.archive}")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    header = parse_header(args.archive)
    print("PMTILES OK: {} region={} bytes={} zoom={}-{} tiles={} bounds=({:.6f},{:.6f},{:.6f},{:.6f})".format(
        args.archive.name, region["id"], args.archive.stat().st_size,
        header["min_zoom"], header["max_zoom"], header["tile_entries_count"],
        header["min_lon"], header["min_lat"], header["max_lon"], header["max_lat"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The tiles OTA manifest: its shape, the one decision over it, and the writer that builds it beside an archive (T-0345).

    python services/tiles/tiles_manifest.py --archive <la.pmtiles> --region-json <region.json> --min-app-build N [--out P]

The corpus manifest is {version, schema_version, min_app_build, sha256, bytes} (Sources/PlaceStore/CorpusManifest.swift).
A basemap has no schema, and has three facts a phone and this checkout can disagree about instead: which region it
draws, which file name BasemapResolver reads it from, and when it was built. So the tiles manifest is exactly FIELDS.

`problems()` is the only decision. The writer refuses to write a manifest it returns anything for, and
ops/lib/sane_prod.py (ops/sane --prod, exit 8) runs it over the PUBLISHED manifest against this checkout. Its
thresholds are check_pmtiles.py's, imported - one number per fact - except MAX_MAXZOOM, below.

The writer reads region, built_at and maxzoom out of the archive's OWN metadata (what check_pmtiles decides) and
measures bytes and sha256 off the bytes on disk, so the manifest cannot claim a provenance the file lacks. That is
the difference from tile_meta.py's sidecar, which copies them from its arguments and is not this shape.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from check_pmtiles import BUDGET_BYTES, MAX_AGE_DAYS, MAX_FUTURE_SKEW, MIN_BYTES, MIN_MAXZOOM, read_metadata
from tile_meta import sha256_of

FIELDS = ("version", "region", "file", "built_at", "maxzoom", "min_app_build", "sha256", "bytes")
# The Protomaps planet build's own maxzoom: an extract cannot be finer than the build it was cut from.
MAX_MAXZOOM = 15
STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
STAMP_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


def is_int(v: object) -> bool:
    """An int that is not a bool: json.loads gives True for `true`, and True == 1."""
    return type(v) is int


def parse_stamp(v: object) -> datetime | None:
    if not isinstance(v, str) or not STAMP_RE.fullmatch(v):
        return None
    try:
        return datetime.strptime(v, STAMP_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def problems(m: object, *, region: str, file: str, now: datetime) -> list[str]:
    """Every way `m` is not a tiles manifest for `region`'s `file` at `now`. Empty list = acceptable."""
    if not isinstance(m, dict):
        return ["not a JSON object"]
    missing = sorted(set(FIELDS) - set(m))
    extra = sorted(set(m) - set(FIELDS))
    if missing or extra:
        return [f"fields: missing {missing}, extra {extra}"]
    out = []
    if not isinstance(m["version"], str) or not m["version"]:
        out.append(f"version is {m['version']!r}, not a non-empty string")
    if not isinstance(m["region"], str) or m["region"] != region:
        out.append(f"region is {m['region']!r}, this checkout's region is {region!r}")
    if not isinstance(m["file"], str) or m["file"] != file:
        out.append(f"file is {m['file']!r}, BasemapResolver reads {file!r}")
    built = parse_stamp(m["built_at"])
    if built is None:
        out.append(f"built_at is {m['built_at']!r}, not a YYYY-MM-DDTHH:MM:SSZ timestamp")
    elif built < now - timedelta(days=MAX_AGE_DAYS):
        out.append(f"built_at {m['built_at']} is older than {MAX_AGE_DAYS} days (P-DATA-03)")
    elif built > now + MAX_FUTURE_SKEW:
        out.append(f"built_at {m['built_at']} is ahead of now by more than {MAX_FUTURE_SKEW}")
    if not is_int(m["maxzoom"]) or not MIN_MAXZOOM <= m["maxzoom"] <= MAX_MAXZOOM:
        out.append(f"maxzoom is {m['maxzoom']!r}, not an int in [{MIN_MAXZOOM}, {MAX_MAXZOOM}]")
    if not is_int(m["min_app_build"]) or m["min_app_build"] < 1:
        out.append(f"min_app_build is {m['min_app_build']!r}, not an int >= 1")
    if not isinstance(m["sha256"], str) or not SHA256_RE.fullmatch(m["sha256"]):
        out.append("sha256 is not 64 lowercase hex digits")
    if not is_int(m["bytes"]) or not MIN_BYTES <= m["bytes"] <= BUDGET_BYTES:
        out.append(f"bytes is {m['bytes']!r}, not an int in [{MIN_BYTES}, {BUDGET_BYTES}]")
    return out


def build(archive: Path, *, min_app_build: int) -> dict:
    """The manifest for `archive`, every field read off the archive itself except min_app_build."""
    meta = read_metadata(archive)
    built = parse_stamp(meta.get("built_at"))
    return {
        "version": built.strftime("%Y%m%dT%H%M%SZ") if built else "",
        "region": meta.get("region"),
        "file": archive.name,
        "built_at": meta.get("built_at"),
        "maxzoom": meta.get("maxzoom"),
        "min_app_build": min_app_build,
        "sha256": sha256_of(archive),
        "bytes": archive.stat().st_size,
    }


def main(argv: list[str] | None = None, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the tiles OTA manifest beside a built archive.")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--region-json", type=Path, required=True,
                        help="the region file the expected region is READ from, never typed")
    parser.add_argument("--min-app-build", type=int, required=True)
    parser.add_argument("--out", type=Path, help="default: <archive>.manifest.json")
    args = parser.parse_args(argv)
    if not args.archive.is_file():
        print(f"TILES MANIFEST REFUSED: no archive at {args.archive}")
        return 1
    region = json.loads(args.region_json.read_text(encoding="utf-8"))["id"]
    try:
        manifest = build(args.archive, min_app_build=args.min_app_build)
    except (ValueError, OSError) as exc:
        print(f"TILES MANIFEST REFUSED: {args.archive} unreadable: {exc}")
        return 1
    found = problems(manifest, region=region, file=f"{region}.pmtiles", now=now or datetime.now(timezone.utc))
    if found:
        print(f"TILES MANIFEST REFUSED: {args.archive}")
        for problem in found:
            print(f"  - {problem}")
        return 1
    out = args.out or args.archive.with_name(args.archive.name + ".manifest.json")
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"TILES MANIFEST OK: {out} region={manifest['region']} version={manifest['version']} bytes={manifest['bytes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

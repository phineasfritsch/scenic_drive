"""ops/sane --prod's two read-only verdicts over answers ops/sane has already fetched (T-0344).

    <health JSON>   | python ops/lib/sane_prod.py quota
    <manifest JSON> | python ops/lib/sane_prod.py manifest services/etl/etl/schema.py
    <tiles JSON>    | python ops/lib/sane_prod.py tiles <region.json> <BasemapResolver.swift>

Prints ONE line and exits 0 (ok) or 1 (FAIL). ops/sane maps 1 to exit 6 (quota) or 8 (manifest, tiles). Anything this
script cannot read is a FAIL that says "cannot tell" - an unreadable answer is never ok.

quota     reads the deployed Worker's /__health fields kill_switch, upstream_month, upstream_calls and
          upstream_trip_at (services/api/src/index.ts). FAIL when the kill switch is set, when the month's
          upstream calls have reached the trip point, or when they are within 10% of it: calls*10 >= trip_at*9.
manifest  the corpus OTA manifest, field by field as Sources/PlaceStore/CorpusManifest.swift parses it, with
          schema_version compared to this checkout's services/etl/etl/schema.py SCHEMA_VERSION.
tiles     the tiles OTA manifest (T-0345), decided by services/tiles/tiles_manifest.py's problems() - the same
          function its writer runs - with region read from region.json's `id` and the file name from the ONE
          whole `applicationSupportPath = "tiles/<file>"` line in BasemapResolver.swift, at the host's clock.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

NEAR_NUMERATOR = 9
NEAR_DENOMINATOR = 10
QUOTA_FIELDS = ("kill_switch", "upstream_month", "upstream_calls", "upstream_trip_at")
MANIFEST_FIELDS = ("version", "schema_version", "min_app_build", "sha256", "bytes")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
MONTH_RE = re.compile(r"[0-9]{4}-[0-9]{2}")
SCHEMA_LINE_RE = re.compile(r"SCHEMA_VERSION\s*=\s*([0-9]+)\s*")
RESOLVER_LINE_RE = re.compile(r'\s*public static let applicationSupportPath = "tiles/([^"/]+)"\s*')
TILES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "tiles")


def is_int(v: object) -> bool:
    """An int that is not a bool: json.loads gives True for `true`, and True == 1."""
    return type(v) is int


def quota(text: str) -> tuple[bool, str]:
    try:
        h = json.loads(text)
    except ValueError:
        return False, "cannot tell: /__health is not JSON"
    if not isinstance(h, dict):
        return False, "cannot tell: /__health is not a JSON object"
    kill, month, calls, trip = (h.get(k) for k in QUOTA_FIELDS)
    if type(kill) is not bool:
        return False, f"cannot tell: kill_switch is {kill!r}, not a boolean"
    if not isinstance(month, str) or not MONTH_RE.fullmatch(month):
        return False, f"cannot tell: upstream_month is {month!r}"
    if not is_int(trip) or trip < 1:
        return False, f"cannot tell: upstream_trip_at is {trip!r}"
    if not is_int(calls) or calls < 0:
        return False, f"cannot tell: upstream_calls is {calls!r} (QUOTA unbound or unreadable)"
    if kill:
        return False, "kill switch is SET (env KILL or the KV KILL_SWITCH key): planning is paused"
    if calls >= trip:
        return False, f"TRIPPED: {calls} upstream calls in {month} >= trip point {trip}: planning is paused"
    if calls * NEAR_DENOMINATOR >= trip * NEAR_NUMERATOR:
        return False, f"NEAR TRIP: {calls} upstream calls in {month} is within 10% of the trip point {trip}"
    return True, f"{calls} of {trip} upstream calls in {month}, kill switch off"


def checkout_schema_version(path: str) -> int | None:
    try:
        with open(path, encoding="utf-8") as f:
            found = [m.group(1) for m in (SCHEMA_LINE_RE.fullmatch(line.rstrip("\r\n")) for line in f) if m]
    except OSError:
        return None
    return int(found[0]) if len(found) == 1 else None


def manifest(text: str, schema_path: str) -> tuple[bool, str]:
    want = checkout_schema_version(schema_path)
    if want is None:
        return False, f"cannot tell: {schema_path} does not hold exactly one SCHEMA_VERSION = <int> line"
    try:
        m = json.loads(text)
    except ValueError:
        return False, "corpus manifest is not JSON"
    if not isinstance(m, dict):
        return False, "corpus manifest is not a JSON object"
    missing = sorted(set(MANIFEST_FIELDS) - set(m))
    extra = sorted(set(m) - set(MANIFEST_FIELDS))
    if missing or extra:
        return False, f"corpus manifest fields: missing {missing}, extra {extra}"
    if not isinstance(m["version"], str) or not m["version"]:
        return False, f"corpus manifest version is {m['version']!r}, not a non-empty string"
    if not is_int(m["schema_version"]):
        return False, f"corpus manifest schema_version is {m['schema_version']!r}, not an int"
    if m["schema_version"] != want:
        return False, f"corpus manifest schema_version {m['schema_version']} != this checkout's SCHEMA_VERSION {want}"
    if not is_int(m["min_app_build"]) or m["min_app_build"] < 1:
        return False, f"corpus manifest min_app_build is {m['min_app_build']!r}, not an int >= 1"
    if not isinstance(m["sha256"], str) or not SHA256_RE.fullmatch(m["sha256"]):
        return False, "corpus manifest sha256 is not 64 lowercase hex digits"
    if not is_int(m["bytes"]) or m["bytes"] < 1:
        return False, f"corpus manifest bytes is {m['bytes']!r}, not an int >= 1"
    return True, f"corpus {m['version']} schema_version {want} == checkout, {m['bytes']} bytes"


def checkout_tiles_file(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            found = [m.group(1) for m in (RESOLVER_LINE_RE.fullmatch(line.rstrip("\r\n")) for line in f) if m]
    except OSError:
        return None
    return found[0] if len(found) == 1 else None


def checkout_region(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            rid = json.load(f).get("id")
    except (OSError, ValueError, AttributeError):
        return None
    return rid if isinstance(rid, str) and rid else None


def tiles(text: str, region_path: str, resolver_path: str, now: datetime | None = None) -> tuple[bool, str]:
    region, file = checkout_region(region_path), checkout_tiles_file(resolver_path)
    if region is None:
        return False, f"cannot tell: {region_path} has no string id"
    if file is None:
        return False, f"cannot tell: {resolver_path} does not hold exactly one applicationSupportPath line"
    try:
        sys.path.insert(0, TILES_DIR)
        sys.dont_write_bytecode = True
        import tiles_manifest
    except ImportError as exc:
        return False, f"cannot tell: services/tiles/tiles_manifest.py does not import ({exc})"
    try:
        m = json.loads(text)
    except ValueError:
        return False, "tiles manifest is not JSON"
    found = tiles_manifest.problems(m, region=region, file=file, now=now or datetime.now(timezone.utc))
    if found:
        return False, "tiles manifest: " + "; ".join(found)
    return True, f"tiles {m['version']} region {region} file {file} == checkout, built_at {m['built_at']}, {m['bytes']} bytes"


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(newline="\n")
    text = sys.stdin.read()
    if argv[1:] == ["quota"]:
        good, line = quota(text)
    elif len(argv) == 3 and argv[1] == "manifest":
        good, line = manifest(text, argv[2])
    elif len(argv) == 4 and argv[1] == "tiles":
        good, line = tiles(text, argv[2], argv[3])
    else:
        print("usage: sane_prod.py quota | sane_prod.py manifest <schema.py> | sane_prod.py tiles <region.json> <resolver.swift>")
        return 2
    print(line)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

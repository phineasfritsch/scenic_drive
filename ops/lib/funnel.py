#!/usr/bin/env python3
"""ops/funnel (T-0284): plan -> preview -> drive -> answer, prettier share and W1/W4 return, read from the
Workers Analytics Engine dataset scenic_telemetry that T-0279's POST /telemetry writes.

    ops/funnel --fixture <file>   a recorded AE SQL API response to SQL below
    ops/funnel --live             POST SQL to the AE SQL API; ACCOUNT_ID and AE_READ_TOKEN from the environment

Rulings live in queue/*/T-0284-ops-funnel.md. The reader is a WHITELIST over the response (R2); it never selects
or holds the H3 cell (R3); credentials come from the environment only and are never printed (R6).
Exits: 0 printed, 2 usage, 3 credentials absent, 4 response refused, 5 HTTP failed (R8).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import funnel_math  # noqa: E402

EXIT_OK, EXIT_USAGE, EXIT_CREDENTIALS_ABSENT, EXIT_RESPONSE_REFUSED, EXIT_HTTP_FAILED = 0, 2, 3, 4, 5

SQL = ("SELECT timestamp, index1, blob1, blob2, double1, double2, _sample_interval FROM scenic_telemetry "
       "WHERE timestamp > NOW() - INTERVAL '28' DAY ORDER BY timestamp FORMAT JSON")
COLUMNS = ("timestamp", "index1", "blob1", "blob2", "double1", "double2", "_sample_interval")
ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account}/analytics_engine/sql"
CREDENTIALS = ("ACCOUNT_ID", "AE_READ_TOKEN")
TOP_REQUIRED = {"meta", "data", "rows"}
TOP_OPTIONAL = {"rows_before_limit_at_least", "statistics"}
TIMESTAMP = re.compile(r"\A\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\Z")

# T-0279 R3: the fifteen wire names, and the labels the funnel reads. Every other name is "other events".
WIRE_NAMES = frozenset({
    "plan_requested", "plan_result", "preview_shown", "handoff_tapped", "drive_started", "drive_completed",
    "drive_abandoned", "post_drive_answer", "surprise_shown", "surprise_not_this", "surprise_take_me_there",
    "surprise_arrived", "corpus_activated", "paywall_shown", "paywall_converted"})
STEP_LABELS = {
    "plan_requested": frozenset({"scenic", "loop", "surprise", "road_trip"}),
    "preview_shown": frozenset({""}),
    "drive_started": frozenset({""}),
    "post_drive_answer": frozenset(funnel_math.ANSWERS),
}


class Refused(Exception):
    """The response is not the whitelisted shape; the message names the first fault."""


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def parse_response(body: bytes) -> list[tuple[str, str, str, int]]:
    """Validated (timestamp, event name, label, weight) rows. Anything off the whitelist raises Refused."""
    try:
        top = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise Refused(f"the body is not JSON ({exc.__class__.__name__})") from None
    if not isinstance(top, dict) or not TOP_REQUIRED <= set(top) or not set(top) <= TOP_REQUIRED | TOP_OPTIONAL:
        raise Refused(f"top-level keys must be {sorted(TOP_REQUIRED)} plus optional {sorted(TOP_OPTIONAL)}")
    meta, data = top["meta"], top["data"]
    if not isinstance(meta, list) or [m.get("name") if isinstance(m, dict) else None for m in meta] != list(COLUMNS):
        raise Refused(f"meta columns must be exactly {list(COLUMNS)} in that order")
    if not isinstance(data, list):
        raise Refused("data must be a list of rows")
    if top["rows"] != len(data) or isinstance(top["rows"], bool):
        raise Refused(f"rows says {top['rows']!r} but data holds {len(data)}")
    return [_row(i, r) for i, r in enumerate(data)]


def _row(i: int, r) -> tuple[str, str, str, int]:
    if not isinstance(r, dict) or set(r) != set(COLUMNS):
        raise Refused(f"data[{i}] must have exactly the keys {list(COLUMNS)}")
    ts, index1, name, label = r["timestamp"], r["index1"], r["blob1"], r["blob2"]
    if not isinstance(ts, str) or not TIMESTAMP.match(ts):
        raise Refused(f"data[{i}].timestamp must be 'YYYY-MM-DD HH:MM:SS'")
    if not all(isinstance(v, str) for v in (index1, name, label)):
        raise Refused(f"data[{i}] index1, blob1 and blob2 must be strings")
    if name not in WIRE_NAMES:
        raise Refused(f"data[{i}].blob1 is not one of T-0279's fifteen event names")
    if index1 != name:
        raise Refused(f"data[{i}].index1 must equal blob1 (T-0279 R2)")
    if name in STEP_LABELS and label not in STEP_LABELS[name]:
        raise Refused(f"data[{i}].blob2 is not a label {name} carries")
    if not (_is_number(r["double1"]) and _is_number(r["double2"])):
        raise Refused(f"data[{i}] double1 and double2 must be finite numbers")
    weight = r["_sample_interval"]
    if not isinstance(weight, int) or isinstance(weight, bool) or weight < 1:
        raise Refused(f"data[{i}]._sample_interval must be a whole number >= 1")
    return ts, name, label, weight


def urllib_post(url: str, headers: dict, data: bytes) -> tuple[int, bytes]:
    """The one real HTTP call; tests pass a stub in its place."""
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except urllib.error.URLError:
        return 0, b""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ops/funnel", add_help=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture", metavar="FILE", help="a recorded AE SQL API response to the fixed SQL")
    source.add_argument("--live", action="store_true", help="query AE; ACCOUNT_ID and AE_READ_TOKEN from the env")
    return parser


def run(argv, env, http, out, err) -> int:
    """The shipping entry point: main() calls exactly this."""
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_USAGE
    if args.live:
        missing = [name for name in CREDENTIALS if not env.get(name)]
        if missing:
            err.write(f"CREDENTIALS_ABSENT: {', '.join(missing)} not set in the environment\n")
            return EXIT_CREDENTIALS_ABSENT
        status, body = http(ENDPOINT.format(account=env["ACCOUNT_ID"]),
                            {"Authorization": "Bearer " + env["AE_READ_TOKEN"]}, SQL.encode("utf-8"))
        if status != 200:
            err.write(f"HTTP_FAILED: status {status}\n")
            return EXIT_HTTP_FAILED
    else:
        try:
            body = pathlib.Path(args.fixture).read_bytes()
        except OSError as exc:
            err.write(f"usage: cannot read the fixture ({exc.__class__.__name__})\n")
            return EXIT_USAGE
    try:
        rows = parse_response(body)
    except Refused as exc:
        err.write(f"RESPONSE_REFUSED: {exc}\n")
        return EXIT_RESPONSE_REFUSED
    out.write("".join(line + "\n" for line in funnel_math.render(funnel_math.tally(rows))))
    return EXIT_OK


def main() -> int:
    return run(sys.argv[1:], os.environ, urllib_post, sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(main())

"""check-sane-prod: ops/sane --prod's exits 6 (quota / kill switch) and 8 (corpus + tiles manifests), driven through the
SHIPPED ops/sane against a LOCAL fake Worker on 127.0.0.1 - never production, never a deploy (T-0344).

    bash ops/lib/check-sane-prod [--sane PATH] [--only name,name]

Each case sets what the fake answers on /__health, /__version, /corpus/manifest.json and /tiles/manifest.json, runs
`SANE_SCOPE=prod API_URL=<fake> CORPUS_MANIFEST_URL=<fake>/... TILES_MANIFEST_URL=<fake>/... bash <sane> --prod`
and asserts:
the exact exit code; the status of every row the case names (a None status: the row must not be printed); no
FAIL row the case does not name; that the fake saw only GET requests; and that `git status --porcelain` and HEAD
are identical before and after (ops/sane never mutates). Exit 0 every case passed; 1 a case failed; 2 cannot tell.
The fake and the row parser live in sane_prod_fake.py; the tiles rows (T-0345) in sane_prod_tiles_cases.py.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
from http.server import ThreadingHTTPServer

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sane_prod_fake import DEL, SEEN, STATE, Fake, edited, rows, snapshot, wire  # noqa: E402
from sane_prod_tiles_cases import TILES_PATH, bound_problems, good, tiles_cases, tiles_meta_problems  # noqa: E402

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
MANIFEST_PATH = "/corpus/manifest.json"


def schema_version() -> int:
    with open(os.path.join(ROOT, "services/etl/etl/schema.py"), encoding="utf-8") as f:
        found = [int(m.group(1)) for m in (re.fullmatch(r"SCHEMA_VERSION = ([0-9]+)", l.rstrip("\r\n")) for l in f) if m]
    if len(found) != 1:
        print(f"SANE-PROD refuse   services/etl/etl/schema.py holds {len(found)} SCHEMA_VERSION lines, not 1")
        sys.exit(2)
    return found[0]


SV = schema_version()
HEALTH = {"ok": True, "db": "up", "git_sha": HEAD, "kill_switch": False, "upstream_month": "2026-10",
          "upstream_calls": 0, "upstream_trip_at": 225000}
MANIFEST = {"version": "20261006T000000Z", "schema_version": SV, "min_app_build": 1, "sha256": "ab" * 32,
            "bytes": 41_000_000}
def h(**kw: object) -> dict:
    return edited(HEALTH, kw)


def m(**kw: object) -> dict:
    return edited(MANIFEST, kw)


OK_ROWS = {"backend": "ok", "version": "ok", "quota": "ok", "manifest": "ok", "tiles": "ok"}
Q6 = {**OK_ROWS, "quota": "FAIL"}
M8 = {**OK_ROWS, "manifest": "FAIL"}

# (name, health (status, body), manifest (status, body) or None for 404 or "unset" for no URL, exit, rows)
CASES: list[tuple[str, tuple[int, object], object, int, dict]] = [
    ("q-green", (200, h()), (200, m()), 0, OK_ROWS),
    ("q-kill", (200, h(kill_switch=True)), (200, m()), 6, Q6),
    ("q-tripped", (200, h(upstream_calls=225000)), (200, m()), 6, Q6),
    ("q-over-trip", (200, h(upstream_calls=225001)), (200, m()), 6, Q6),
    ("q-near-bound", (200, h(upstream_calls=202500)), (200, m()), 6, Q6),
    ("q-below-near", (200, h(upstream_calls=202499)), (200, m()), 0, OK_ROWS),
    ("q-near-bound-small-trip", (200, h(upstream_trip_at=1000, upstream_calls=900)), (200, m()), 6, Q6),
    ("q-below-near-small-trip", (200, h(upstream_trip_at=1000, upstream_calls=899)), (200, m()), 0, OK_ROWS),
    ("q-calls-null", (200, h(upstream_calls=None)), (200, m()), 6, Q6),
    ("q-calls-absent", (200, h(upstream_calls=DEL)), (200, m()), 6, Q6),
    ("q-calls-bool", (200, h(upstream_calls=True)), (200, m()), 6, Q6),
    ("q-calls-negative", (200, h(upstream_calls=-1)), (200, m()), 6, Q6),
    ("q-calls-float", (200, h(upstream_calls=10.5)), (200, m()), 6, Q6),
    ("q-kill-string", (200, h(kill_switch="false")), (200, m()), 6, Q6),
    ("q-kill-absent", (200, h(kill_switch=DEL)), (200, m()), 6, Q6),
    ("q-kill-null", (200, h(kill_switch=None)), (200, m()), 6, Q6),
    ("q-kill-zero", (200, h(kill_switch=0)), (200, m()), 6, Q6),
    ("q-kill-empty-string", (200, h(kill_switch="")), (200, m()), 6, Q6),
    ("q-trip-zero", (200, h(upstream_trip_at=0)), (200, m()), 6, Q6),
    ("q-trip-absent", (200, h(upstream_trip_at=DEL)), (200, m()), 6, Q6),
    ("q-month-absent", (200, h(upstream_month=DEL)), (200, m()), 6, Q6),
    ("m-green", (200, h()), (200, m()), 0, OK_ROWS),
    ("m-not-json", (200, h()), (200, b"<html>not json</html>"), 8, M8),
    ("m-not-object", (200, h()), (200, [m()]), 8, M8),
    ("m-missing-key", (200, h()), (200, m(bytes=DEL)), 8, M8),
    ("m-extra-key", (200, h()), (200, m(url="https://example.invalid/corpus.sqlite")), 8, M8),
    ("m-schema-other", (200, h()), (200, m(schema_version=SV + 1)), 8, M8),
    ("m-schema-older", (200, h()), (200, m(schema_version=SV - 1)), 8, M8),
    ("m-schema-string", (200, h()), (200, m(schema_version=str(SV))), 8, M8),
    ("m-version-empty", (200, h()), (200, m(version="")), 8, M8),
    ("m-version-int", (200, h()), (200, m(version=20261006)), 8, M8),
    ("m-sha-upper", (200, h()), (200, m(sha256="AB" * 32)), 8, M8),
    ("m-sha-63", (200, h()), (200, m(sha256=("ab" * 32)[:63])), 8, M8),
    ("m-bytes-zero", (200, h()), (200, m(bytes=0)), 8, M8),
    ("m-bytes-float", (200, h()), (200, m(bytes=10.0)), 8, M8),
    ("m-min-build-bool", (200, h()), (200, m(min_app_build=True)), 8, M8),
    ("m-min-build-zero", (200, h()), (200, m(min_app_build=0)), 8, M8),
    ("m-404", (200, h()), None, 8, M8),
    ("m-unset", (200, h()), "unset", 0, {**OK_ROWS, "manifest": "skip"}),
    ("p-6-over-8", (200, h(kill_switch=True)), (200, m(schema_version=SV + 1)), 6,
     {**OK_ROWS, "quota": "FAIL", "manifest": "FAIL"}),
    ("p-7-over-6-and-8", (503, h(ok=False, db="down", kill_switch=True)), (200, m(schema_version=SV + 1)), 7,
     {"backend": "FAIL", "version": None, "quota": None, "manifest": "FAIL"}),
]

# T-0344 R9/R10: GENERATED rows x-<field>-<variant>, value and exit functions of the kind; REQUIRED rows per kind.
QUOTA_KINDS = {"kill_switch": "bool", "upstream_month": "month", "upstream_calls": "int0", "upstream_trip_at": "int1"}
MANIFEST_KINDS = {"version": "str", "schema_version": "intsv", "min_app_build": "int1", "sha256": "sha", "bytes": "int1"}
UNIVERSAL = ("absent", "null", "true", "false", "string", "empty-string", "list", "object", "number")
INT_EXTRA = ("zero", "negative")
REGEX_EXTRA = ("over-long", "under-long", "garbage-suffix")
REQUIRED = {"bool": UNIVERSAL, "str": UNIVERSAL, "int0": UNIVERSAL + INT_EXTRA, "int1": UNIVERSAL + INT_EXTRA,
            "intsv": UNIVERSAL + INT_EXTRA, "month": UNIVERSAL + REGEX_EXTRA, "sha": UNIVERSAL + REGEX_EXTRA}
# (field, variant) pairs whose value is VALID for the field: green, exit 0. Every other generated row is the side's FAIL.
GREEN = {("kill_switch", "false"), ("upstream_calls", "zero"), ("version", "string")}


def variants(field: str, kind: str) -> dict[str, object]:
    good = {**HEALTH, **MANIFEST}[field]
    out: dict[str, object] = {"absent": DEL, "null": None, "true": True, "false": False, "empty-string": "",
                              "list": [good], "object": {"value": good}}
    if kind in ("int0", "int1", "intsv"):
        out.update({"string": str(good), "number": float(good), "zero": 0, "negative": -1})
    elif kind in ("month", "sha"):
        out.update({"string": "october" if kind == "month" else "g" * 64, "number": 202610,
                    "over-long": good + good[-1], "under-long": good[:-1], "garbage-suffix": good + "x"})
    else:
        out.update({"string": "x" if kind == "str" else "false", "number": 0})
    return out


def generated_cases() -> list[tuple]:
    out = []
    for side, kinds, rc, fail_rows in (("q", QUOTA_KINDS, 6, Q6), ("m", MANIFEST_KINDS, 8, M8)):
        for field, kind in kinds.items():
            for variant, value in variants(field, kind).items():
                green = (field, variant) in GREEN
                health = h(**{field: value}) if side == "q" else h()
                manifest = m(**{field: value}) if side == "m" else m()
                out.append((f"x-{field}-{variant}", (200, health), (200, manifest), 0 if green else rc,
                            OK_ROWS if green else fail_rows))
    return out


CASES += generated_cases()
CASES += tiles_cases(h(), m(), OK_ROWS, h)


def meta_problems() -> list[str]:
    sys.dont_write_bytecode = True
    sys.path.insert(0, os.path.join(ROOT, "ops/lib"))
    import sane_prod
    sys.path.insert(0, sane_prod.TILES_DIR)
    names = [c[0] for c in CASES]
    out = []
    shipped_m, shipped_q = getattr(sane_prod, "MANIFEST_FIELDS", ()), getattr(sane_prod, "QUOTA_FIELDS", ())
    if set(MANIFEST_KINDS) != set(shipped_m) or set(MANIFEST_KINDS) != set(MANIFEST):
        out.append(f"manifest fields {sorted(MANIFEST_KINDS)} != shipped MANIFEST_FIELDS {sorted(shipped_m)}")
    if set(QUOTA_KINDS) != set(shipped_q):
        out.append(f"quota fields {sorted(QUOTA_KINDS)} != shipped QUOTA_FIELDS {sorted(shipped_q)}")
    for field, kind in {**QUOTA_KINDS, **MANIFEST_KINDS}.items():
        missing = [v for v in REQUIRED[kind] if f"x-{field}-{v}" not in names]
        if missing:
            out.append(f"field {field} has no row for {missing}")
    import tiles_manifest  # sane_prod put services/tiles on sys.path
    out += tiles_meta_problems(names, tiles_manifest)
    if len(set(names)) != len(names):
        out.append("duplicate case names")
    return out


def run_case(sane: str, base: str, case: tuple) -> list[str]:
    name, health, manifest, want_rc, want_rows = case[:5]
    tiles = case[5] if len(case) > 5 else (200, good)
    STATE.clear()
    SEEN.clear()
    STATE["/__health"] = (health[0], wire(health[1]))
    STATE["/__version"] = (200, wire({"git_sha": HEAD, "built_at": "2026-10-09T00:00:00Z", "schema_version": SV}))
    if isinstance(manifest, tuple):
        STATE[MANIFEST_PATH] = (manifest[0], wire(manifest[1]))
    if isinstance(tiles, tuple):
        STATE[TILES_PATH] = (tiles[0], wire(tiles[1]))
    env = {k: v for k, v in os.environ.items() if k not in ("CORPUS_MANIFEST_URL", "TILES_MANIFEST_URL", "API_URL")}
    env.update({"SANE_SCOPE": "prod", "API_URL": base})
    if manifest != "unset":
        env["CORPUS_MANIFEST_URL"] = base + MANIFEST_PATH
    if tiles != "unset":
        env["TILES_MANIFEST_URL"] = base + TILES_PATH
    before = snapshot(ROOT)
    p = subprocess.run(["bash", sane, "--prod"], capture_output=True, text=True, cwd=ROOT, env=env)
    after = snapshot(ROOT)
    got = rows(p.stdout)
    problems = []
    if p.returncode != want_rc:
        problems.append(f"exit {p.returncode}, want {want_rc}")
    for row, status in want_rows.items():
        have = got.get(row)
        if status is None and have is not None:
            problems.append(f"row {row} printed {have}, want none")
        elif status is not None and have != [status]:
            problems.append(f"row {row} {have}, want [{status}]")
    stray = sorted(r for r, st in got.items() if "FAIL" in st and want_rows.get(r) != "FAIL")
    if stray:
        problems.append(f"unexpected FAIL rows {stray}")
    if any(method != "GET" for method, _ in SEEN):
        problems.append(f"non-GET requests {SEEN}")
    if before != after:
        problems.append("git status or HEAD changed across the run")
    if problems:
        problems.append("ops/sane printed: " + " | ".join(l for l in p.stdout.splitlines() if l.strip()))
    return problems


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(newline="\n")
    sane, only = "ops/sane", None
    args = list(argv[1:])
    while args:
        a = args.pop(0)
        if a == "--sane" and args:
            sane = args.pop(0)
        elif a == "--only" and args:
            only = set(args.pop(0).split(","))
        else:
            print(f"SANE-PROD refuse   unknown argument {a}")
            return 2
    for url_file in ("ops/corpus-manifest-url", "ops/tiles-manifest-url"):
        if os.path.exists(os.path.join(ROOT, url_file)):
            print(f"SANE-PROD refuse   {url_file} exists, so the unset cases cannot be tested")
            return 2
    meta = meta_problems()
    if meta:
        print("SANE-PROD refuse   meta: " + "; ".join(meta))
        return 2
    import sane_prod
    ran, bound_failed = bound_problems(ROOT, sane_prod, only)
    for line in bound_failed:
        print(f"SANE-PROD FAIL     {line}")
    cases = [c for c in CASES if only is None or c[0] in only]
    if not cases and not ran:
        print("SANE-PROD refuse   no case selected - the run would check nothing")
        return 2
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    failed = len(bound_failed)
    try:
        for case in cases:
            problems = run_case(sane, base, case)
            if problems:
                failed += 1
                print(f"SANE-PROD FAIL     {case[0]}: " + "; ".join(problems))
            else:
                print(f"SANE-PROD pass     {case[0]} exit={case[3]}")
    finally:
        server.shutdown()
    if failed:
        print(f"SANE-PROD FAIL     {failed} of {len(cases) + ran} cases failed (sane={sane})")
        return 1
    n = len(cases) + ran
    print(f"SANE-PROD ok       {n}/{n} cases passed ({ran} b- rows at a fixed clock; sane={sane}, fake={base})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

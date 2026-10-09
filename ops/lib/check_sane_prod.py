"""check-sane-prod: ops/sane --prod's exits 6 (quota / kill switch) and 8 (corpus manifest), driven through the
SHIPPED ops/sane against a LOCAL fake Worker on 127.0.0.1 - never production, never a deploy (T-0344).

    bash ops/lib/check-sane-prod [--sane PATH] [--only name,name]

Each case sets what the fake answers on /__health, /__version and /corpus/manifest.json, runs
`SANE_SCOPE=prod API_URL=<fake> CORPUS_MANIFEST_URL=<fake>/corpus/manifest.json bash <sane> --prod`, and asserts:
the exact exit code; the status of every row the case names (a None status: the row must not be printed); no
FAIL row the case does not name; that the fake saw only GET requests; and that `git status --porcelain` and HEAD
are identical before and after (ops/sane never mutates). Exit 0 every case passed; 1 a case failed; 2 cannot tell.
"""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
HEAD = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
MANIFEST_PATH = "/corpus/manifest.json"

STATE: dict[str, tuple[int, bytes]] = {}
SEEN: list[tuple[str, str]] = []


class Fake(BaseHTTPRequestHandler):
    def _answer(self) -> None:
        SEEN.append((self.command, self.path))
        status, body = STATE.get(self.path, (404, b'{"error":"not found"}'))
        if self.command != "GET":
            status, body = 405, b'{"error":"GET only"}'
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _answer

    def log_message(self, *args: object) -> None:
        pass


def wire(v: object) -> bytes:
    """JSON as the Worker's JSON.stringify writes it - no spaces, which ops/sane's `"ok":true` grep depends on."""
    return v if isinstance(v, bytes) else json.dumps(v, separators=(",", ":")).encode()


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
DEL = object()


def h(**kw: object) -> dict:
    out = copy.deepcopy(HEALTH)
    for k, v in kw.items():
        if v is DEL:
            out.pop(k)
        else:
            out[k] = v
    return out


def m(**kw: object) -> dict:
    out = copy.deepcopy(MANIFEST)
    for k, v in kw.items():
        if v is DEL:
            out.pop(k)
        else:
            out[k] = v
    return out


OK_ROWS = {"backend": "ok", "version": "ok", "quota": "ok", "manifest": "ok"}
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
    ("q-trip-zero", (200, h(upstream_trip_at=0)), (200, m()), 6, Q6),
    ("q-trip-absent", (200, h(upstream_trip_at=DEL)), (200, m()), 6, Q6),
    ("q-month-absent", (200, h(upstream_month=DEL)), (200, m()), 6, Q6),
    ("m-green", (200, h()), (200, m()), 0, OK_ROWS),
    ("m-not-json", (200, h()), (200, b"<html>not json</html>"), 8, M8),
    ("m-not-object", (200, h()), (200, [m()]), 8, M8),
    ("m-missing-key", (200, h()), (200, m(bytes=DEL)), 8, M8),
    ("m-extra-key", (200, h()), (200, m(url="https://example.invalid/corpus.sqlite")), 8, M8),
    ("m-schema-other", (200, h()), (200, m(schema_version=SV + 1)), 8, M8),
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


def snapshot() -> str:
    st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True,
                        cwd=ROOT).stdout
    return st + subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout


def rows(out: str) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for line in out.splitlines():
        parts = line.rstrip("\r").split()
        if len(parts) >= 2 and not line.startswith(" ") and parts[0] != "SANE" and parts[1] in ("ok", "FAIL", "skip"):
            seen.setdefault(parts[0], []).append(parts[1])
    return seen


def run_case(sane: str, base: str, case: tuple) -> list[str]:
    name, health, manifest, want_rc, want_rows = case
    STATE.clear()
    SEEN.clear()
    STATE["/__health"] = (health[0], wire(health[1]))
    STATE["/__version"] = (200, wire({"git_sha": HEAD, "built_at": "2026-10-09T00:00:00Z", "schema_version": SV}))
    if isinstance(manifest, tuple):
        STATE[MANIFEST_PATH] = (manifest[0], wire(manifest[1]))
    env = {k: v for k, v in os.environ.items() if k not in ("CORPUS_MANIFEST_URL", "API_URL")}
    env.update({"SANE_SCOPE": "prod", "API_URL": base})
    if manifest != "unset":
        env["CORPUS_MANIFEST_URL"] = base + MANIFEST_PATH
    before = snapshot()
    p = subprocess.run(["bash", sane, "--prod"], capture_output=True, text=True, cwd=ROOT, env=env)
    after = snapshot()
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
    if os.path.exists(os.path.join(ROOT, "ops/corpus-manifest-url")):
        print("SANE-PROD refuse   ops/corpus-manifest-url exists, so the m-unset case cannot be tested")
        return 2
    cases = [c for c in CASES if only is None or c[0] in only]
    if not cases:
        print("SANE-PROD refuse   no case selected - the run would check nothing")
        return 2
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    failed = 0
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
        print(f"SANE-PROD FAIL     {failed} of {len(cases)} cases failed (sane={sane})")
        return 1
    print(f"SANE-PROD ok       {len(cases)}/{len(cases)} cases passed (sane={sane}, fake={base})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

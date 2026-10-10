"""check-sane-prod's local fake Worker and its reading of ops/sane's output (split out of check_sane_prod.py, T-0345).

The fake answers GET on whatever paths STATE holds, 404 on the rest, 405 on any other method, and records every
request in SEEN. It binds 127.0.0.1 only: never production, never a deploy.
"""
from __future__ import annotations

import copy
import json
import subprocess
from http.server import BaseHTTPRequestHandler

STATE: dict[str, tuple[int, bytes]] = {}
SEEN: list[tuple[str, str]] = []
DEL = object()


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
    """JSON as the Worker's JSON.stringify writes it - no spaces, which ops/sane's `"ok":true` grep depends on.
    A callable is called first: a body that depends on the clock is built when its case RUNS, not at import."""
    v = v() if callable(v) else v
    return v if isinstance(v, bytes) else json.dumps(v, separators=(",", ":")).encode()


def edited(base: dict, kw: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in kw.items():
        v = v() if callable(v) else v
        if v is DEL:
            out.pop(k)
        else:
            out[k] = v
    return out


def snapshot(root: str) -> str:
    st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True,
                        cwd=root).stdout
    return st + subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=root).stdout


def rows(out: str) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for line in out.splitlines():
        parts = line.rstrip("\r").split()
        if len(parts) >= 2 and not line.startswith(" ") and parts[0] != "SANE" and parts[1] in ("ok", "FAIL", "skip"):
            seen.setdefault(parts[0], []).append(parts[1])
    return seen

"""ops/sane --prod's version row (T-0402): does a change between the live Worker's commit and HEAD need a deploy?

    python ops/lib/sane_version.py LIVE HEAD        (cwd: inside the checkout ops/sane is asking about)

Prints ONE line - the row's message - and exits 0 (live == Worker inputs at HEAD), 1 (deploy pending) or 2 (cannot
tell; ops/sane counts it as pending too). Every path that changed between LIVE and HEAD is put in exactly one class:

  imported      a path a relative import in services/api/src (at HEAD) names - esbuild inlines it whatever directory
                it sits in (src/servedRegion.ts imports services/etl/regions/*/region.json). Outranks every list.
  bundle        WORKER_BUNDLE: what ops/deploy's `wrangler deploy` builds and configures the Worker from.
  not bundled   WORKER_NOT_BUNDLE: read only by `vitest run`. Ignored.
  unclassified  anything else under services/api - a new directory, a new top-level file. COUNTED: a path nobody
                has classified is pending, never ok (fail closed). Put it in one of the two lists.
  outside       anything else outside services/api and ops/deploy. Not a Worker input; not counted.
"""
from __future__ import annotations

import posixpath
import re
import subprocess
import sys

API = "services/api/"
SRC = "services/api/src/"
WORKER_BUNDLE = (
    "services/api/src/",
    "services/api/wrangler.jsonc",
    "services/api/package.json",
    "services/api/package-lock.json",
    "services/api/tsconfig.json",
    "services/api/migrations/",
    "ops/deploy",
)
WORKER_NOT_BUNDLE = (
    "services/api/test/",
    "services/api/vitest.config.ts",
)
# A relative module specifier after `from`, `import` or `import(` - static, side-effect and dynamic imports alike.
IMPORT = re.compile(r"""(?:\bfrom|\bimport)\s*\(?\s*["'](\.{1,2}/[^"']+)["']""")
GREP = r"""(from|import)[[:space:]]*\(?[[:space:]]*["']\.\.?/"""


class CannotTell(Exception):
    pass


def git(*args: str) -> bytes:
    p = subprocess.run(["git", *args], capture_output=True)
    if p.returncode != 0:
        raise CannotTell(f"git {' '.join(args)} exited {p.returncode}: {p.stderr.decode('utf-8', 'replace').strip()}")
    return p.stdout


def imports(head: str) -> set[str]:
    """Every repo path a relative import in services/api/src at HEAD names, as written (no extension added).

    classify() matches these by prefix, so `./geo` covers geo.ts and a directory import covers its index.ts (fail
    closed: a sibling such as geography.ts counts too). Read: static, side-effect, dynamic, `export ... from`, and a
    multi-line import whose specifier shares a line with `from`. Declared limit: a specifier on a later line than its
    `from` / `import(` keyword, and require()."""
    p = subprocess.run(["git", "grep", "-z", "-I", "-E", GREP, head, "--", SRC], capture_output=True)
    if p.returncode not in (0, 1):  # 1 = no match, which is an answer
        raise CannotTell(f"git grep over {SRC} at {head} exited {p.returncode}")
    out: set[str] = set()
    for record in p.stdout.decode("utf-8", "replace").splitlines():
        name, _, text = record.partition("\0")
        path = name[len(head) + 1:] if name.startswith(head + ":") else name
        for spec in IMPORT.findall(text):
            out.add(posixpath.normpath(posixpath.join(posixpath.dirname(path), spec)))
    return out


def listed(path: str, entries: tuple[str, ...]) -> bool:
    return any(path.startswith(e) if e.endswith("/") else path == e for e in entries)


def classify(path: str, imported: set[str]) -> str:
    if any(path == t or path.startswith(t) for t in imported):
        return "imported"
    if listed(path, WORKER_BUNDLE):
        return "bundle"
    if listed(path, WORKER_NOT_BUNDLE):
        return "not"
    if path.startswith(API):
        return "unclassified"
    return "outside"


def decide(live: str, head: str) -> tuple[int, str]:
    short_live = git("rev-parse", "--short", live).decode().strip()
    short_head = git("rev-parse", "--short", head).decode().strip()
    imported = imports(head)
    changed = [p for p in git("diff", "-z", "--no-renames", "--name-only", live, head).decode("utf-8").split("\0") if p]
    counted, n = [], {"imported": 0, "bundle": 0, "not": 0, "unclassified": 0, "outside": 0}
    for path in changed:
        kind = classify(path, imported)
        n[kind] += 1
        if kind in ("imported", "bundle", "unclassified"):
            counted.append(path)
    if not counted:
        return 0, f"live {short_live} == Worker inputs at HEAD {short_head} ({n['not']} not-bundled path(s) changed)"
    return 1, (f"Worker inputs changed since live {short_live} -> deploy pending: {' '.join(counted[:3])} "
               f"({n['bundle'] + n['imported']} bundle, {n['unclassified']} unclassified, {n['not']} not bundled)")


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(newline="\n")
    if len(argv) != 3:
        print("usage: sane_version.py LIVE HEAD")
        return 2
    try:
        rc, line = decide(argv[1], argv[2])
    except (CannotTell, UnicodeDecodeError) as e:
        print(f"cannot tell whether a deploy is pending: {e}")
        return 2
    print(line)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""check-sane-corpus: ops/sane exit 4's corpus invariants (T-0372, pin P-OPS-09), driven through the SHIPPED ops/sane.

    bash ops/lib/check-sane-corpus [--sane PATH] [--only name,name]

Each s- row builds a fixture corpus.sqlite in a temp directory (sane_corpus_cases.build, through the shipping
schema.apply_schema), runs `SANE_SCOPE=prod SANE_CORPUS=<fixture> bash <sane>` - no --prod, so the corpus block is
the only check that runs - and asserts the exact exit, the status of every corpus row, no FAIL row the case does not
name, the fixture's bytes unchanged and `git status` plus HEAD unchanged (ops/sane never mutates).
The d- rows run the shipping `ops/lib/sane_corpus.py` with no argument against a fake $SCENIC_REGION_WORK store,
which is how ops/sane finds a corpus when SANE_CORPUS is unset; p-prod-scope runs ops/sane with neither.
Exit 0 every row passed; 1 a row failed; 2 cannot tell.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sane_corpus  # noqa: E402  (puts services/etl on sys.path)
from etl import schema, surfacecoverage  # noqa: E402
from sane_corpus_cases import FLOOR_LA, build, cases, meta_problems, want  # noqa: E402
from sane_prod_fake import snapshot  # noqa: E402

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
CLEARED = ("SANE_CORPUS", "SCENIC_REGION_WORK", "API_URL", "CORPUS_MANIFEST_URL", "TILES_MANIFEST_URL", "SANE_SCOPE")


def rows(out: str) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) >= 2 and parts[0] != "SANE" and parts[1] in ("ok", "FAIL", "skip"):
            seen.setdefault(parts[0], []).append(parts[1])
    return seen


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "absent"


def base_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in CLEARED}


def compare(got: dict, want_rows: dict) -> list[str]:
    problems = []
    for row, status in want_rows.items():
        if got.get(row) != [status]:
            problems.append(f"row {row} {got.get(row)}, want [{status}]")
    stray = sorted(r for r, st in got.items() if "FAIL" in st and want_rows.get(r) != "FAIL")
    if stray:
        problems.append(f"unexpected FAIL rows {stray}")
    return problems


def run_s(sane: str, tmp: pathlib.Path, case: tuple) -> list[str]:
    name, fx, want_rc, want_rows = case
    path = tmp / f"{name}.sqlite"
    build(path, fx, schema, surfacecoverage)
    before, fixture = snapshot(ROOT), digest(path)
    env = {**base_env(), "SANE_SCOPE": "prod", "SANE_CORPUS": str(path)}
    p = subprocess.run(["bash", sane], capture_output=True, text=True, cwd=ROOT, env=env)
    problems = [] if p.returncode == want_rc else [f"exit {p.returncode}, want {want_rc}"]
    problems += compare(rows(p.stdout), want_rows)
    if digest(path) != fixture:
        problems.append("the fixture corpus changed across the run")
    if snapshot(ROOT) != before:
        problems.append("git status or HEAD changed across the run")
    if problems:
        problems.append("ops/sane printed: " + " | ".join(l for l in p.stdout.splitlines() if l.strip()))
    return problems


def d_rows() -> list[tuple]:
    """(name, store files {name: fixture}, SANE_CORPUS fixture or None, exit, rows) - discovery without SANE_CORPUS."""
    clean = want(None)
    return [
        ("d-unset", None, None, 0, {"corpus-db": "skip"}),
        ("d-store-empty", {}, None, 0, {"corpus-db": "skip"}),
        ("d-store-clean", {"la-corpus.sqlite": {}}, None, 0, clean),
        ("d-store-below-floor", {"la-corpus.sqlite": {"viewpoints": FLOOR_LA - 1}}, None, 4,
         want("corpus-viewpoints")),
        ("d-store-wrong-name", {"corpus.sqlite": {"viewpoints": 0}, "sfbay.sqlite": {"viewpoints": 0}}, None, 0,
         {"corpus-db": "skip"}),
        ("d-named-beats-store", {"la-corpus.sqlite": {}}, {"viewpoints": 0}, 4, want("corpus-viewpoints")),
    ]


def run_d(tmp: pathlib.Path, case: tuple) -> list[str]:
    name, store, named, want_rc, want_rows = case
    env = base_env()
    if store is not None:
        sdir = tmp / name
        sdir.mkdir()
        for fname, fx in store.items():
            build(sdir / fname, fx, schema, surfacecoverage)
        env["SCENIC_REGION_WORK"] = str(sdir)
    if named is not None:
        build(tmp / f"{name}-named.sqlite", named, schema, surfacecoverage)
        env["SANE_CORPUS"] = str(tmp / f"{name}-named.sqlite")
    p = subprocess.run([sys.executable, os.path.join(ROOT, "ops/lib/sane_corpus.py")], capture_output=True,
                       text=True, cwd=ROOT, env=env)
    got: dict[str, list[str]] = {}
    for line in p.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            got.setdefault(parts[1], []).append(parts[0])
    problems = [] if p.returncode == want_rc else [f"exit {p.returncode}, want {want_rc}"]
    problems += compare(got, want_rows)
    return problems + ([f"sane_corpus.py printed: {p.stdout!r} {p.stderr!r}"] if problems else [])


P_ROWS = (  # (name, env added, exit, rows): ops/sane's own arms around sane_corpus.py, the clean fixture named
    ("p-prod-scope", {}, 0, {"corpus-db": "skip"}),
    ("p-python-false", {"PYTHON": "false"}, 4, {"corpus-db": "FAIL"}),
    ("p-python-echo", {"PYTHON": "echo"}, 4, {"corpus-db": "FAIL"}),
)


def run_p(sane: str, tmp: pathlib.Path, case: tuple) -> list[str]:
    name, added, want_rc, want_rows = case
    env = {**base_env(), "SANE_SCOPE": "prod", **added}
    if added:
        build(tmp / f"{name}.sqlite", {}, schema, surfacecoverage)
        env["SANE_CORPUS"] = str(tmp / f"{name}.sqlite")
    p = subprocess.run(["bash", sane], capture_output=True, text=True, cwd=ROOT, env=env)
    got = rows(p.stdout)
    problems = [] if p.returncode == want_rc else [f"exit {p.returncode}, want {want_rc}"]
    extra = sorted(r for r in got if r.startswith("corpus-") and r != "corpus-db")
    problems += compare(got, want_rows) + ([f"corpus rows {extra} printed"] if extra else [])
    return problems + ([f"ops/sane printed: {p.stdout!r}"] if problems else [])


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
            print(f"SANE-CORPUS refuse   unknown argument {a}")
            return 2
    s_cases, d_cases = cases(schema.SCHEMA_VERSION), d_rows()
    names = [c[0] for c in s_cases] + [c[0] for c in d_cases] + [c[0] for c in P_ROWS]
    meta = meta_problems(names, sane_corpus)
    if meta:
        print("SANE-CORPUS refuse   meta: " + "; ".join(meta))
        return 2
    picked = [n for n in names if only is None or n in only]
    if not picked:
        print("SANE-CORPUS refuse   no case selected - the run would check nothing")
        return 2
    failed = 0
    with tempfile.TemporaryDirectory(prefix="sane-corpus-") as tmpdir:
        tmp = pathlib.Path(tmpdir)
        for kind, case in [("s", c) for c in s_cases] + [("d", c) for c in d_cases] + [("p", c) for c in P_ROWS]:
            if case[0] not in picked:
                continue
            problems = run_s(sane, tmp, case) if kind == "s" else run_d(tmp, case) if kind == "d" else run_p(sane, tmp, case)
            if problems:
                failed += 1
                print(f"SANE-CORPUS FAIL     {case[0]}: " + "; ".join(problems))
            else:
                print(f"SANE-CORPUS pass     {case[0]}")
    if failed:
        print(f"SANE-CORPUS FAIL     {failed} of {len(picked)} cases failed (sane={sane})")
        return 1
    print(f"SANE-CORPUS ok       {len(picked)}/{len(picked)} cases passed (sane={sane})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

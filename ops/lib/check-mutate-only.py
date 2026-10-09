"""T-0347 (P-PROC-06): every mutation driver refuses an `--only` that names nothing or does not parse, with exit 64.

    python ops/lib/check-mutate-only.py

A typo'd selection used to have three outcomes, none of them a usage refusal: exit 2 (the same status as a red
baseline or a dirty tree), the WHOLE population run because the driver ignored that spelling of the flag, or a
run over ZERO mutations. Each reads as something other than "you typed it wrong" when only the status is read.

The population is the DRIVERS whitelist of ops/lib/mutate_population_table.py (the same list P-PROC-06 already
holds every runnable ops/mutate/*.py to) plus every services/api/test/mutate/*Mutants.mjs, each with a literal
floor so a table emptied by a bad merge is a refusal and not `0 of 0`. Every driver is run, as the shipping
command line, with `--only 999999` (names no entry) and `--only 1-2x` (does not parse as an id or a range), and
must exit EXIT_ONLY_REFUSED (64) with a `REFUSING TO RUN: ` line. 64 and not "non-zero": 2 is non-zero and is what
a driver that reached its baseline gate returns, so "non-zero" would pass a driver that never looked at --only.
The parsers themselves (ops/mutate/mutate_only.py, services/api/test/mutate/onlyIds.mjs) are also exercised in
process for the selections that must NOT refuse, so a parser that refuses everything is not green.
The tree's `git status` is compared before and after: a driver that ignored the flag and began mutating is named.
Exit 0 all refused; 1 a driver did not refuse as required; 2 this check could not run (floor, git, a parser control).
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ops/lib"))
sys.path.insert(0, str(ROOT / "ops/mutate"))

from mutate_population_table import DRIVERS  # noqa: E402
import mutate_only  # noqa: E402

EXIT_ONLY_REFUSED = 64
PY_FLOOR = 38
MJS_FLOOR = 17
PROBES = (["--only", "999999"], ["--only", "1-2x"])
TIMEOUT_S = 120


def status() -> str:
    p = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True,
                       text=True)
    if p.returncode != 0:
        raise SystemExit("check-mutate-only: git status failed (exit %d): REFUSING" % p.returncode)
    return p.stdout


def parser_controls() -> list:
    """Selections that must NOT refuse, and the exact selections they make."""
    bad = []
    py = [(["--only", "1,E1"], ["1", "2", "E1"], {"1", "E1"}), (["--only=2", "--only", "1"], ["1", "2"], {"1", "2"}),
          ([], ["1"], None), (["--prove-vacuity"], ["1"], None)]
    for argv, keys, want in py:
        got = mutate_only.select_only(argv, keys)
        if got != want:
            bad.append("mutate_only.select_only(%r, %r) = %r, expected %r" % (argv, keys, got, want))
    got = mutate_only.select_only(["--only", "a, b"], ["xa, by"], substring=True, split=False)
    if got != {"xa, by"}:
        bad.append("mutate_only whole-value fragment selection = %r" % (got,))
    js = ("import { onlyIds } from %s; console.log(JSON.stringify([onlyIds(['--only', 'a,b'], ['a', 'b', 'c']), "
          "onlyIds(['--only=c'], ['a', 'c']), onlyIds([], ['a'])]));"
          % json.dumps((ROOT / "services/api/test/mutate/onlyIds.mjs").as_uri()))
    p = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True)
    want = [["a", "b"], ["c"], None]
    if p.returncode != 0 or json.loads(p.stdout or "null") != want:
        bad.append("onlyIds controls: exit %d, %r, expected %r" % (p.returncode, p.stdout.strip(), want))
    return bad


def drivers() -> list:
    py = [["python", ROOT / "ops/mutate" / d] for d in sorted(DRIVERS)]
    mjs = [["node", f] for f in sorted((ROOT / "services/api/test/mutate").glob("*Mutants.mjs"))]
    if len(py) < PY_FLOOR or len(mjs) < MJS_FLOOR:
        raise SystemExit("check-mutate-only: %d Python drivers (floor %d), %d mjs drivers (floor %d): REFUSING"
                         % (len(py), PY_FLOOR, len(mjs), MJS_FLOOR))
    return [([sys.executable if k == "python" else k, str(f)], f.relative_to(ROOT).as_posix()) for k, f in py + mjs]


def main() -> int:
    bad = parser_controls()
    if bad:
        for b in bad:
            print("PARSER CONTROL FAILED: %s" % b)
        return 2
    runs = drivers()
    before = status()
    failed = []
    for cmd, name in runs:
        for probe in PROBES:
            try:
                p = subprocess.run(cmd + probe, cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT_S)
                code, out = p.returncode, p.stdout + p.stderr
            except subprocess.TimeoutExpired:
                code, out = None, "(still running after %ds: it ignored the flag and started a run)" % TIMEOUT_S
            lines = [l for l in out.replace("\r", "").split("\n") if l.strip()]
            ok = code == EXIT_ONLY_REFUSED and any(l.startswith("REFUSING TO RUN: ") for l in lines)
            if not ok:
                failed.append("%s %s: exit %s (need %d) - %s" % (name, " ".join(probe), code, EXIT_ONLY_REFUSED,
                                                                 lines[-1][:120] if lines else "(no output)"))
    after = status()
    for f in failed:
        print("NOT REFUSED: %s" % f)
    if after != before:
        print("TREE CHANGED during the run - a driver mutated files:\n%s" % after)
        return 1
    print("MUTATE-ONLY %s: %d of %d driver runs refused with exit %d (%d drivers x %d probes)"
          % ("OK" if not failed else "FAILED", 2 * len(runs) - len(failed), 2 * len(runs), EXIT_ONLY_REFUSED,
             len(runs), len(PROBES)))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

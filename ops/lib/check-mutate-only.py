"""T-0347 (P-PROC-06): every mutation driver refuses an `--only` that names nothing or does not parse, with exit 64.

    python ops/lib/check-mutate-only.py

A typo'd selection used to have three outcomes, none of them a usage refusal: exit 2 (the same status as a red
baseline or a dirty tree), the WHOLE population run because the driver ignored that spelling of the flag, or a
run over ZERO mutations. Each reads as something other than "you typed it wrong" when only the status is read.

The population is the DRIVERS whitelist of ops/lib/mutate_population_table.py (the same list P-PROC-06 already
holds every runnable ops/mutate/*.py to) plus every services/api/test/mutate/*Mutants.mjs, each with a literal
floor so a table emptied by a bad merge is a refusal and not `0 of 0`. Every driver is run, as the shipping
command line, with `--only 999999` (names no entry), `--only 1-2x` (does not parse as an id or a range) and
well-formed RANGES of the driver's own ids, and must exit EXIT_ONLY_REFUSED (64) with a `REFUSING TO RUN: ` line.
The ids come from the driver: the `999999` refusal prints the population it was handed as one `ONLY IDS: <json>`
line. The ids split into two classes (T-0353). All-digit ids give the two smallest `A-B`, else the first
`N-(N+1)` no id contains (also the only probe of a driver with no `--only`, whose refusal lists no ids). Any
non-digit ids (mjs mutation names, substring-keyed names, plansheet-style E-ids) give `<x0>-<x1>` from the first
consecutive listed pair no id equals or contains, or `<x>-<x>` for a lone one: a range expansion anywhere in a
parser would select real entries with it. A non-digit population no pair can probe fails, and fewer name-range
probes than NAME_RANGE_FLOOR (38, measured 2026-10-09) fails. A "names no entry" refusal with no `ONLY IDS` line
fails.
64 and not "non-zero": 2 is non-zero and is what a driver that reached its baseline gate returns, so "non-zero"
would pass a driver that never looked at --only.
The parsers themselves (ops/mutate/mutate_only.py, services/api/test/mutate/onlyIds.mjs) are also exercised in
process for the selections that must NOT refuse, so a parser that refuses everything is not green.
The tree's `git status` (untracked files included) is compared before and after: a driver that ignored the flag
and began mutating is named. A probe killed at the timeout is reported with the files it left changed; they are
NOT restored here.
Exit 0 all refused; 1 a driver did not refuse as required; 2 this check could not run (floor, git, a parser control,
fewer name-range probes than NAME_RANGE_FLOOR).
"""
from __future__ import annotations

import json
import pathlib
import re
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
NAMES_NOTHING = ["--only", "999999"]
PROBES = (NAMES_NOTHING, ["--only", "1-2x"])
NAME_RANGE_FLOOR = 38
NO_ONLY = "this driver has no --only"
TIMEOUT_S = 120


def status() -> str:
    p = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, capture_output=True,
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


def free(token: str, ids: list) -> bool:
    """No id equals or contains the token, so even a substring driver selects nothing with it."""
    return not any(token in i for i in ids)


def name_range(ids: list) -> str | None:
    """`<x0>-<x1>` over the driver's non-digit ids (names, E-ids), trying consecutive listed pairs until one no id
    contains; one such id gives `<x>-<x>`. None when the driver lists no non-digit id. An `A-B` expansion whose
    halves are both known ids selects entries with it; a correct parser refuses it as one unknown id."""
    names = [i for i in ids if not re.fullmatch(r"[0-9]+", i)]
    pairs = list(zip(names, names[1:])) or [(n, n) for n in names[:1]]
    for a, b in pairs:
        if free("%s-%s" % (a, b), ids):
            return "%s-%s" % (a, b)
    return None if not names else ""


def range_tokens(ids: list) -> list:
    """Well-formed ranges over the driver's real ids, as (kind, token). The digit class gives its two smallest
    `A-B`; a driver without one gets the first N-(N+1) no id contains; a driver with any non-digit id also gets
    name_range(). A non-digit population no pair can probe is ("name", "") - a failure, never a skip."""
    digits = sorted((i for i in ids if re.fullmatch(r"[0-9]+", i)), key=int)
    out = []
    if len(digits) >= 2 and free("%s-%s" % (digits[0], digits[1]), ids):
        out.append(("digit", "%s-%s" % (digits[0], digits[1])))
    else:
        n = 1
        while not free("%d-%d" % (n, n + 1), ids):
            n += 1
        out.append(("n", "%d-%d" % (n, n + 1)))
    name = name_range(ids)
    if name is not None:
        out.append(("name", name))
    return out


def probe_once(cmd: list, name: str, probe: list, before: str) -> tuple:
    try:
        p = subprocess.run(cmd + probe, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT_S)
        code, out = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        moved = sorted(set(status().splitlines()) ^ set(before.splitlines()))
        print("KILLED: %s %s still running after %ds - NOT restored; the tree now differs in: %s"
              % (name, " ".join(probe), TIMEOUT_S, "; ".join(moved) or "(no file)"))
        code, out = None, "(killed at %ds: it ignored the flag and started a run)" % TIMEOUT_S
    return code, [l for l in out.replace("\r", "").split("\n") if l.strip()]


def refused(cmd: list, name: str, probe: list, before: str) -> tuple:
    """(exited EXIT_ONLY_REFUSED with a REFUSING TO RUN line, exit code, output lines)."""
    code, lines = probe_once(cmd, name, probe, before)
    return code == EXIT_ONLY_REFUSED and any(l.startswith("REFUSING TO RUN: ") for l in lines), code, lines


def verdict(name: str, probe: list, code, lines: list) -> str:
    return "%s %s: exit %s (need %d) - %s" % (name, " ".join(probe), code, EXIT_ONLY_REFUSED,
                                              lines[-1][:120] if lines else "(no output)")


def main() -> int:
    bad = parser_controls()
    if bad:
        for b in bad:
            print("PARSER CONTROL FAILED: %s" % b)
        return 2
    runs = drivers()
    before = status()
    failed, kinds = [], {"digit": 0, "name": 0, "n": 0}
    for cmd, name in runs:
        ids = []
        for probe in PROBES:
            ok, code, lines = refused(cmd, name, probe, before)
            if probe == NAMES_NOTHING:
                listed = [l[len(mutate_only.IDS_LINE):] for l in lines if l.startswith(mutate_only.IDS_LINE + " ")]
                ids = json.loads(listed[0]) if listed else []
                if not listed and not any(NO_ONLY in l for l in lines):
                    ok, lines = False, lines + ["the refusal lists no %s line" % mutate_only.IDS_LINE]
            if not ok:
                failed.append(verdict(name, probe, code, lines))
        for kind, token in range_tokens(ids):
            kinds[kind] += 1
            if not token:
                failed.append("%s %s range: none of its consecutive id pairs forms a token free of every id"
                              % (name, kind))
                continue
            ok, code, lines = refused(cmd, name, ["--only", token], before)
            if not ok:
                failed.append(verdict(name, ["--only", token], code, lines))
    after = status()
    for f in failed:
        print("NOT REFUSED: %s" % f)
    short = kinds["name"] < NAME_RANGE_FLOOR
    if short:
        print("NAME-RANGE PROBES %d below floor %d: a driver's non-digit ids (names, E-ids) went unprobed"
              % (kinds["name"], NAME_RANGE_FLOOR))
    if after != before:
        print("TREE CHANGED during the run - a driver mutated files:\n%s" % after)
        return 1
    ranges = sum(kinds.values())
    total = len(PROBES) * len(runs) + ranges
    print("MUTATE-ONLY %s: %d of %d driver runs refused with exit %d (%d drivers, %d range probes: %d digit, "
          "%d name, %d N-(N+1))" % ("OK" if not failed and not short else "FAILED", total - len(failed), total,
                                   EXIT_ONLY_REFUSED, len(runs), ranges, kinds["digit"], kinds["name"], kinds["n"]))
    return 1 if failed else 2 if short else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Mutation harness AND population for etl/extractadapter.py and etl/accessrule.py (T-0217, ruling R6).

WHY THESE TWO HAVE ONE. `accessrule.access_refused` decides the corpus's `access_ok` column - the column
the hazard strip and the device router read - and `extractadapter` decides the class, the direction and the
surface tag of every way that reaches `corpus.build`. They are numbers about roads, and CLAUDE.md's
Verification section and P-PROC-06 both say a module like that ships a population with a literal floor in
the same PR. T-0206's measurement adapter had none, and its access list refused 139 ways of the canyon
window that ScenicKit routes while letting through the 22 it refuses. Mutations 26 and 27 - the node
order of a `oneway=-1` row, and the short-way guard - are this PR's pre-review mutant pass's two survivors,
promoted here with the two checks that catch them (task Log, S1 and S2).

THE CONTRACT is ops/mutate/surfacecoverage.py's and ops/mutate/scenic_tags.py's, kept identically:

  * each entry is `(name, file, old, new)`; `old` must appear VERBATIM in the pristine file or the run
    reports SKIP and FAILS - a stale anchor is a harness that has gone quietly blind;
  * a catch requires a NAMED TEST to fail; a non-zero exit is Python noticing, not a check noticing;
  * every subject, the test file this suite empties, and THIS FILE are compared to `git show HEAD:` before
    anything runs, and the restore is verified afterwards: a mutation report is a claim about a COMMIT;
  * `MIN_MUTATIONS` EQUALS the shipped population, so deleting any one mutation refuses the run;
  * EQUIVALENT mutants cannot change behaviour, so a catch there is a FAILURE - it means a test has an
    opinion about how the code is written rather than about what it does;
  * `--prove-vacuity` empties the test file and requires EVERY mutation to report MISSED.

`assemble.py` IS MUTATED HERE AND IS NOT DECLARED HERE. One mutation reorders `gate_reason`'s four rules,
because the ORDER is what makes a derived access column wrong (a private dirt road answers
`unpaved_surface`); the module's own population is ops/mutate/scenic_tags.py's and this file does not
claim it.

PYTHON SUBJECTS: every `__pycache__` under services/etl is purged before each run and the run sleeps past
the filesystem's timestamp granularity, because a .pyc whose source mtime matches to the second is reused
and the mutation never lands (the whole-second mtime false green).
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
ETL = ROOT / "services" / "etl"
ADAPTER = ETL / "etl" / "extractadapter.py"
RULE = ETL / "etl" / "accessrule.py"
ASSEMBLE = ETL / "etl" / "assemble.py"
ADAPTER_TESTS = ETL / "tests" / "test_extractadapter.py"
EMPTIED = (ADAPTER_TESTS,)
SUBJECTS = (ADAPTER, RULE, ASSEMBLE)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/extractadapter.py", "services/etl/etl/accessrule.py")
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

# Anchors, verbatim from the subjects. Identifiers and code, never a comment (CLAUDE.md).
CLOSED = 'CLOSED_ACCESS = frozenset({"private", "no", "permit", "destination"})'
PREDICATE = ('    return (tags.get(ACCESS_KEY) in CLOSED_ACCESS\n'
             '            or tags.get(MOTOR_VEHICLE_KEY) == MOTOR_VEHICLE_REFUSED)')
GATE_ORDER = ('    surface = tags.get("surface")\n'
              '    if surface is not None and surface in UNPAVED_SURFACES:\n'
              '        return GATE_UNPAVED_SURFACE\n'
              '    if tags.get("highway") == TRACK_HIGHWAY:\n'
              '        return GATE_TRACK\n'
              '    if access_refused(tags):\n'
              '        return GATE_NO_ACCESS')
CLS_TABLE = ("HIGHWAY_TO_CLS = {highway: cls for cls, values in WAY_CLASSES.items() "
             "for highway in values}")
FORWARD_BRANCH = "    if value in ONEWAY_FORWARD:\n        return FORWARD"
REVERSE_BRANCH = "    if value in ONEWAY_REVERSE:\n        return REVERSE"
IMPLICATION = ("    if tags.get(JUNCTION_KEY) == ROUNDABOUT:\n"
               "        return FORWARD\n"
               "    return TWO_WAY")
ACCESS_COLUMN = "    return ACCESS_BLOCKED if access_refused(tags) else ACCESS_OK"
NAME_PASS = "    name = name_of(tags)\n    if name is not None:\n        row[NAME_KEY] = name"
SURFACE_PASS = "    value = surface_of(tags)\n    if value is not None:\n        row[SURFACE_KEY] = value"
CLASS_SKIP = ('        if tags.get(HIGHWAY_KEY) not in HIGHWAY_TO_CLS:\n'
              '            counts["skipped_class"] += 1\n'
              '            continue')
DUPLICATE = "        if way_id in seen:"
SURFACE_COUNT = ('        counts[SURFACE_COUNTS[surface_state(highway=way["highway"], '
                 'surface=way.get(SURFACE_KEY))]] += 1')
REGION_REFUSAL = ('    raise ValueError("the document names no region and --region was not given: a corpus '
                  'whose region is "\n                     "guessed is a corpus nobody can serve")')
NODES = '           "nodes": [[float(lat), float(lon)] for lat, lon in coords]}'
SHORT_SKIP = ('        if len(coords) < MIN_COORDINATES:\n            counts["skipped_short"] += 1\n'
              '            continue')

MUTATIONS = [
    # --- the access rule: the one predicate both the gate and the corpus column ask -----------------------
    ("widen the closed set to T-0206's throwaway list, refusing roads ScenicKit routes", RULE, CLOSED,
     'CLOSED_ACCESS = frozenset({"private", "no", "permit", "destination", "customers", "delivery", '
     '"military"})'),
    ("drop `destination` from the closed set, so a road closed to through traffic reads open", RULE,
     CLOSED, 'CLOSED_ACCESS = frozenset({"private", "no", "permit"})'),
    ("widen `motor_vehicle` to the closed set, which refuses `motor_vehicle=private` roads", RULE,
     PREDICATE, '    return (tags.get(ACCESS_KEY) in CLOSED_ACCESS\n'
                '            or tags.get(MOTOR_VEHICLE_KEY) in CLOSED_ACCESS)'),
    ("drop the `motor_vehicle` half of the rule - the half PR #102's review found missing", RULE,
     PREDICATE, "    return tags.get(ACCESS_KEY) in CLOSED_ACCESS"),
    ("drop the `access` half of the rule", RULE, PREDICATE,
     "    return tags.get(MOTOR_VEHICLE_KEY) == MOTOR_VEHICLE_REFUSED"),
    ("refuse only when BOTH halves fire, so one tag alone never closes a road", RULE, PREDICATE,
     '    return (tags.get(ACCESS_KEY) in CLOSED_ACCESS\n'
     '            and tags.get(MOTOR_VEHICLE_KEY) == MOTOR_VEHICLE_REFUSED)'),
    ("treat an ABSENT access tag as a refusal - positive evidence dropped", RULE, PREDICATE,
     '    return (tags.get(ACCESS_KEY, "no") in CLOSED_ACCESS\n'
     '            or tags.get(MOTOR_VEHICLE_KEY) == MOTOR_VEHICLE_REFUSED)'),

    # --- the defect the 06:13 panel corrected: the column derived from the first firing rule --------------
    ("derive access_ok from `gate_reason != GATE_NO_ACCESS`, which grants a private dirt road access",
     ADAPTER, ACCESS_COLUMN,
     "    from .assemble import GATE_NO_ACCESS, gate_reason\n"
     "    return ACCESS_OK if gate_reason(tags) != GATE_NO_ACCESS else ACCESS_BLOCKED"),
    ("fold every safety gate into the access column, so a public track reads closed", ADAPTER,
     ACCESS_COLUMN, "    from .assemble import gate_reason\n"
                    "    return ACCESS_BLOCKED if access_refused(tags) or gate_reason(tags) else ACCESS_OK"),
    ("answer the access rule FIRST in gate_reason, which is what makes a derived column look right",
     ASSEMBLE, GATE_ORDER,
     '    if access_refused(tags):\n'
     '        return GATE_NO_ACCESS\n'
     '    surface = tags.get("surface")\n'
     '    if surface is not None and surface in UNPAVED_SURFACES:\n'
     '        return GATE_UNPAVED_SURFACE\n'
     '    if tags.get("highway") == TRACK_HIGHWAY:\n'
     '        return GATE_TRACK'),

    # --- direction --------------------------------------------------------------------------------------
    ("read `oneway=-1` as a forward one-way, sending the router the wrong way down a real road", ADAPTER,
     REVERSE_BRANCH, "    if value in ONEWAY_REVERSE:\n        return FORWARD"),
    ("drop `oneway=-1` to two-way, the direction lost rather than reversed", ADAPTER, REVERSE_BRANCH,
     "    if value in ONEWAY_REVERSE:\n        return TWO_WAY"),
    ("read `oneway=yes` as two-way", ADAPTER, FORWARD_BRANCH,
     "    if value in ONEWAY_FORWARD:\n        return TWO_WAY"),
    ("treat a roundabout with no `oneway` tag as two-way", ADAPTER, IMPLICATION,
     "    if False:\n        return FORWARD\n    return TWO_WAY"),
    ("imply one-way from `junction=circular` too, which OSM does not", ADAPTER, IMPLICATION,
     '    if tags.get(JUNCTION_KEY) in (ROUNDABOUT, "circular"):\n        return FORWARD\n'
     "    return TWO_WAY"),
    ("default an untagged way to one-way instead of two-way", ADAPTER, IMPLICATION,
     "    if tags.get(JUNCTION_KEY) == ROUNDABOUT:\n        return FORWARD\n    return FORWARD"),
    ("reverse the nodes of every `oneway=-1` row while the flag stays -1 - a real road's geometry laid "
     "against its own direction column", ADAPTER, NODES,
     NODES.replace("coords]}", "(coords[::-1] if oneway_flag(tags) == REVERSE else coords)]}")),

    # --- class, skip and refusal -------------------------------------------------------------------------
    ("let a class outside WAY_CLASSES through to a reader that refuses the whole document", ADAPTER,
     CLASS_SKIP, '        if False:\n            counts["skipped_class"] += 1\n            continue'),
    ("skip the out-of-table ways in SILENCE - the count line reads 0 and two roads vanish", ADAPTER,
     CLASS_SKIP, '        if tags.get(HIGHWAY_KEY) not in HIGHWAY_TO_CLS:\n'
                 '            counts["skipped_class"] += 0\n'
                 '            continue'),
    ("build the class table from the first highway value of each class, losing every _link way", ADAPTER,
     CLS_TABLE, "HIGHWAY_TO_CLS = {highway: cls for cls, values in WAY_CLASSES.items() "
                "for highway in values[:1]}"),
    ("drop a repeated way_id in silence, the way the throwaway did - every other rank moves", ADAPTER,
     DUPLICATE, "        if False and way_id in seen:"),
    ("guess a region rather than refusing a document that names none", ADAPTER, REGION_REFUSAL,
     '    return "la"'),
    ("disable the short-way guard, so a one-node way reaches a reader that refuses the whole document",
     ADAPTER, SHORT_SKIP, SHORT_SKIP.replace("if len", "if False and len")),

    # --- what travels to the corpus ----------------------------------------------------------------------
    ("drop the name, so every way reaches the corpus anonymous", ADAPTER, NAME_PASS,
     "    name = name_of(tags)\n    if False:\n        row[NAME_KEY] = name"),
    ("drop the surface tag, which makes every unpaved road paved by omission", ADAPTER, SURFACE_PASS,
     "    value = surface_of(tags)\n    if False:\n        row[SURFACE_KEY] = value"),
    ("emit the three-state surface column instead of the raw tag, which the reader refuses", ADAPTER,
     SURFACE_PASS, "    value = surface_of(tags)\n    if value is not None:\n"
                   "        row[SURFACE_KEY] = surface_state(highway=tags.get(HIGHWAY_KEY), surface=value)"),
    ("count every way as paved, so the count line stops measuring the states it reports", ADAPTER,
     SURFACE_COUNT, '        counts["surface_paved"] += 1'),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE. Each carries its witness in the name.
EQUIVALENT = [
    ("guard the forward set against None - None is in no set of strings, so the branch is the same",
     ADAPTER, FORWARD_BRANCH,
     "    if value is not None and value in ONEWAY_FORWARD:\n        return FORWARD"),
    ("ask membership of a set copy - `x in frozenset(s)` and `x in set(s)` are one relation", RULE,
     PREDICATE, '    return (tags.get(ACCESS_KEY) in set(CLOSED_ACCESS)\n'
                '            or tags.get(MOTOR_VEHICLE_KEY) == MOTOR_VEHICLE_REFUSED)'),
    ("spell dict.get's own default - `d.get(k)` IS `d.get(k, None)`", ADAPTER, SURFACE_COUNT,
     '        counts[SURFACE_COUNTS[surface_state(highway=way["highway"], '
     'surface=way.get(SURFACE_KEY, None))]] += 1'),
]

# Asserted the other way round: each must still go MISSED, and a gap that CLOSES fails the run so it gets
# promoted into MUTATIONS. Empty is a claim, not an omission.
KNOWN_MISSED = []

MIN_MUTATIONS = 27
PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", str(ADAPTER_TESTS)]
# Past the filesystem's timestamp granularity, so a mutation always lands rather than hitting a stale .pyc.
SETTLE_S = 1.1


def repo_path(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def head_bytes(path: pathlib.Path) -> bytes:
    out = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + repo_path(path)], capture_output=True)
    if out.returncode != 0:
        raise SystemExit("not in HEAD: %s - a mutation report is a claim about a commit" % repo_path(path))
    return out.stdout.replace(b"\r\n", b"\n")


def assert_pristine(paths) -> None:
    for path in paths:
        if path.read_bytes().replace(b"\r\n", b"\n") != head_bytes(path):
            raise SystemExit("%s differs from HEAD - refusing to report on a dirty tree" % repo_path(path))


def purge_pycache() -> None:
    for cache in ETL.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run_tests() -> tuple:
    purge_pycache()
    time.sleep(SETTLE_S)
    out = subprocess.run(PYTEST, cwd=str(ETL), capture_output=True, text=True)
    failed = [line.split(" ")[1] for line in (out.stdout or "").splitlines() if line.startswith("FAILED ")]
    return out.returncode, failed


def apply(path: pathlib.Path, old: str, new: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
    return True


def restore(originals: dict) -> None:
    for path, text in originals.items():
        path.write_text(text, encoding="utf-8", newline="\n")


def arm(population: list, subjects: dict, expect_caught: bool, label: str) -> tuple:
    """Run one population. `subjects` is the SUBJECT files only, so --prove-vacuity's emptied test file
    stays emptied for the whole arm rather than being restored after the first mutation."""
    caught = missed = skipped = 0
    for name, path, old, new in population:
        if not apply(path, old, new):
            print("  SKIP        %s (anchor is not in %s)" % (name, repo_path(path)))
            skipped += 1
            continue
        code, failed = run_tests()
        restore(subjects)
        if failed:
            caught += 1
            print("  caught      %s  <- %s" % (name, failed[0]))
        else:
            missed += 1
            print("  %s      %s (exit %d)" % ("MISSED" if expect_caught else "missed", name, code))
    print("%s: %d caught, %d missed, %d skipped, of %d" % (label, caught, missed, skipped, len(population)))
    return caught, missed, skipped


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops/mutate/extractadapter.py", description=__doc__.splitlines()[0])
    parser.add_argument("--prove-vacuity", action="store_true",
                        help="empty the test file and require every mutation to be MISSED")
    args = parser.parse_args(argv)

    if len(MUTATIONS) < MIN_MUTATIONS:
        print("population is %d, floor is %d" % (len(MUTATIONS), MIN_MUTATIONS), file=sys.stderr)
        return 1
    assert_pristine(GUARDED)
    originals = {path: path.read_text(encoding="utf-8") for path in SUBJECTS + EMPTIED}
    subjects = {path: originals[path] for path in SUBJECTS}

    if args.prove_vacuity:
        for path in EMPTIED:
            path.write_text("", encoding="utf-8", newline="\n")
        caught, missed, skipped = arm(MUTATIONS, subjects, False, "VACUITY")
        restore(originals)
        assert_pristine(GUARDED)
        ok = caught == 0 and skipped == 0 and missed == len(MUTATIONS)
        print("VACUITY %s" % ("PROVED" if ok else "FAILED"))
        return 0 if ok else 1

    code, failed = run_tests()
    if code != 0 or failed:
        print("BASELINE is not green: exit %d, %s" % (code, failed), file=sys.stderr)
        return 1
    print("BASELINE exit=0, %d mutations, floor %d" % (len(MUTATIONS), MIN_MUTATIONS))
    caught, missed, skipped = arm(MUTATIONS, subjects, True, "MUTATIONS")
    eq_caught, _eq_missed, eq_skipped = arm(EQUIVALENT, subjects, False, "EQUIVALENT")
    km_caught = km_skipped = 0
    if KNOWN_MISSED:
        km_caught, _km_missed, km_skipped = arm(KNOWN_MISSED, subjects, False, "KNOWN_MISSED")
    assert_pristine(GUARDED)
    ok = (caught == len(MUTATIONS) and skipped == 0 and eq_caught == 0 and eq_skipped == 0
          and km_caught == 0 and km_skipped == 0)
    print("MUTATE %s  caught=%d/%d equivalent_caught=%d" % ("OK" if ok else "FAILED", caught,
                                                            len(MUTATIONS), eq_caught))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

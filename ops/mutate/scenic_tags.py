#!/usr/bin/env python3
"""Mutation harness AND population for the two numeric modules T-0168 adds: tagwriter and scenecheck.

WHY THESE TWO AND NOT THE OTHER TWO (T-0168's log, the closing ruling). `etl/osmxml.py` is a stream copy and
`etl/waydoc.py` is wiring over producers that carry their own numbers; neither computes one. These two do:
`tagwriter.quantise` is the R1 quantisation - round-half-up of the 0..1 score times ten, clamped to the four
bits GraphHopper holds it in - and `scenecheck.counts` is `ops/sane` check 4's two clauses as numbers. A
module that computes a number ships a population (CLAUDE.md, Verification).

THE CONTRACT, the same one ops/mutate/gates_corpus.py and its runner keep:

  * each entry is `(name, file, old, new)`; `old` must appear VERBATIM in the pristine file or the run
    reports SKIP and FAILS - a stale anchor is a harness that has gone quietly blind;
  * a catch requires a NAMED TEST to fail. A non-zero exit is not a catch: a mutation that makes the suite
    error out has been noticed by Python, not by a check;
  * every subject, every test file this suite empties, and THIS FILE are compared to `git show HEAD:` before
    anything runs, and the restore is verified against HEAD afterwards. A mutation report is a claim about a
    COMMIT and is worth nothing about a dirty tree;
  * `MIN_MUTATIONS` EQUALS the shipped population, so deleting any one mutation refuses the run;
  * EQUIVALENT mutants are asserted the other way round - they cannot change behaviour, so a catch there is
    a FAILURE, because it means a test has an opinion about how the code is written rather than what it does;
  * `--prove-vacuity` empties both test files and requires EVERY mutation to report MISSED, which is what
    makes a clean sheet mean something.

PYTHON SUBJECTS NEED TWO THINGS A SWIFT SUBJECT DOES NOT, and both are here because leaving either out
produces a FALSE GREEN: every `__pycache__` under services/etl is purged before each run, and the run sleeps
past the filesystem's timestamp granularity, because a .pyc whose source mtime matches to the second is
reused and the mutation never lands.
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
TAGWRITER = ETL / "etl" / "tagwriter.py"
SCENECHECK = ETL / "etl" / "scenecheck.py"
TAGWRITER_TESTS = ETL / "tests" / "test_tagwriter.py"
SCENECHECK_TESTS = ETL / "tests" / "test_scenecheck.py"
EMPTIED = (TAGWRITER_TESTS, SCENECHECK_TESTS)
SUBJECTS = (TAGWRITER, SCENECHECK)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/tagwriter.py", "services/etl/etl/scenecheck.py")
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

# Anchors reused by more than one mutation, verbatim from the subjects.
QUANTISE = "    scaled = math.floor(number * SCORE_SCALE + 0.5)"
CLAMP = "    return max(SCORE_MIN, min(SCORE_MAX, scaled))"
NOT_A_ROAD = "    if not tags.get(HIGHWAY):\n        counts[\"not_a_road\"] += 1\n        return"
GATE_TAG = "    if row.get(\"gate_reason\"):\n        out[KEY_GATE] = row[\"gate_reason\"]"
NULL_ROW = "        if row.get(\"score\") is None:"
FLAGS_JOIN = "        out[KEY_FLAGS] = FLAG_SEPARATOR.join(flags)"
WRITE_LOOP = ("    with osmxml.Writer(out) as writer:\n"
              "        for elem in osmxml.iter_top_level(source):\n"
              "            if elem.tag == osmxml.WAY:\n"
              "                _tag_way(elem, scored, refused, counts, seen)\n"
              "            writer.write(elem)")
MISSING = "    missing = sorted((set(scored) | set(refused)) - seen)"
NEITHER = "    raise ValueError(\"way %d carries highway=%s and is in neither the scored table nor the "
CHECK_NOT_A_ROAD = "        if not tags.get(HIGHWAY):\n            found[\"not_a_road\"] += 1\n            continue"
CHECK_REFUSED = "        if tags.get(tagwriter.KEY_REFUSED):\n            found[\"refused\"] += 1\n            continue"
CHECK_GATED = "        if value > 0 and is_gated(tags):"
IS_GATED = "    return tags.get(HIGHWAY) in ZERO_CLASSES or gate_reason(tags) is not None"
REFUSES = "    return found[\"null_score\"] > 0 or found[\"gated_scored\"] > 0"
SORT = "    rows.sort(key=lambda r: (-r[\"scenic_score\"], -r[\"scenic_score_unit\"], r[\"way_id\"]))"
MIDDLE = "    return coords[len(coords) // 2]"

MUTATIONS = [
    # --- the quantisation, ruling R1 ----------------------------------------------------------------------
    ("truncate instead of rounding half up", TAGWRITER, QUANTISE,
     "    scaled = math.floor(number * SCORE_SCALE)"),
    ("round half to even, which is what `round` does", TAGWRITER, QUANTISE,
     "    scaled = round(number * SCORE_SCALE)"),
    ("round half DOWN", TAGWRITER, QUANTISE,
     "    scaled = math.ceil(number * SCORE_SCALE - 0.5)"),
    ("scale to 0..100, past the four bits the router holds", TAGWRITER, "SCORE_SCALE = 10",
     "SCORE_SCALE = 100"),
    ("stop at 9, so a perfect road cannot say so", TAGWRITER, "SCORE_MAX = 10", "SCORE_MAX = 9"),
    ("drop the clamp, so a term bug upstream becomes a value the router cannot hold", TAGWRITER, CLAMP,
     "    return scaled"),
    ("write the terms at two decimals instead of four", TAGWRITER, "TERM_PRECISION = 4",
     "TERM_PRECISION = 2"),

    # --- what lands on a way, rulings R1 and R2 ------------------------------------------------------------
    ("stop naming the gate that fired", TAGWRITER, GATE_TAG, "    if False:\n        pass"),
    ("write a refused row as a silent 0 - the exact defect R2 forbids", TAGWRITER, NULL_ROW,
     "        if False:"),
    ("tag a park as if it were a road", TAGWRITER, NOT_A_ROAD, "    if not tags.get(HIGHWAY):\n"
     "        counts[\"not_a_road\"] += 1"),
    ("let the population shrink between two stages", TAGWRITER, MISSING, "    missing = []"),
    ("let a road the table never saw through untagged", TAGWRITER, NEITHER,
     "    return\n    raise ValueError(\"way %d carries highway=%s and is in neither the scored table nor the "),
    ("count a gated way as ungated in the write line", TAGWRITER,
     "        if row.get(\"gate_reason\"):\n            counts[\"gated\"] += 1",
     "        if False:\n            counts[\"gated\"] += 1"),

    # --- the order of the shipped bytes, ruling R3 (P-DATA-01) --------------------------------------------
    # Both are invisible to two writes inside ONE interpreter: one hash seed makes the pair agree with each
    # other and disagree with the next process. The P-DATA-01 test writes its second file in a child.
    ("emit the ways in hash order instead of input order", TAGWRITER, WRITE_LOOP,
     "    held = []\n"
     "    with osmxml.Writer(out) as writer:\n"
     "        for elem in osmxml.iter_top_level(source):\n"
     "            if elem.tag == osmxml.WAY:\n"
     "                _tag_way(elem, scored, refused, counts, seen)\n"
     "                held.append(__import__(\"copy\").deepcopy(elem))\n"
     "                continue\n"
     "            writer.write(elem)\n"
     "        for elem in sorted(held, key=lambda way: hash(way.get(\"id\"))):\n"
     "            writer.write(elem)"),
    ("join the flags out of a set, which has no order", TAGWRITER, FLAGS_JOIN,
     "        out[KEY_FLAGS] = FLAG_SEPARATOR.join(set(flags))"),

    # --- check 4's two clauses --------------------------------------------------------------------------
    ("only object to a gated way scoring above 5", SCENECHECK, CHECK_GATED,
     "        if value > 5 and is_gated(tags):"),
    # The clause is `> 0`. Every gated fixture carried 3 or 7, so `> 1` passed 26 tests: a shipped PBF with
    # a motorway at 1 printed gated_scored=0 and exited 0.
    ("only object to a gated way scoring above 1", SCENECHECK, CHECK_GATED,
     "        if value > 1 and is_gated(tags):"),
    ("forget that motorway and trunk are a clause of their own", SCENECHECK, IS_GATED,
     "    return gate_reason(tags) is not None"),
    ("forget the safety gates, keeping only the zero classes", SCENECHECK, IS_GATED,
     "    return tags.get(HIGHWAY) in ZERO_CLASSES"),
    ("count a refused way as a hole in the scores", SCENECHECK, CHECK_REFUSED,
     "        if False:\n            found[\"refused\"] += 1\n            continue"),
    ("mistake the name tag for the highway tag when deciding what a road is", SCENECHECK,
     CHECK_NOT_A_ROAD,
     "        if not tags.get(NAME):\n            found[\"not_a_road\"] += 1\n            continue"),
    ("refuse on the first clause only", SCENECHECK, REFUSES, "    return found[\"null_score\"] > 0"),
    ("report the failure with a zero exit code", SCENECHECK, "REFUSAL_EXIT = 4", "REFUSAL_EXIT = 0"),
    ("rank the ways from worst to best", SCENECHECK, SORT,
     "    rows.sort(key=lambda r: (r[\"scenic_score\"], r[\"scenic_score_unit\"], r[\"way_id\"]))"),
    ("give the human the way's first node instead of its middle one", SCENECHECK, MIDDLE,
     "    return coords[0]"),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE. Both have a witness in the name.
EQUIVALENT = [
    ("clamp the other way round - min(MAX, max(MIN, x)) is max(MIN, min(MAX, x)) for MIN < MAX", TAGWRITER,
     CLAMP, "    return min(SCORE_MAX, max(SCORE_MIN, scaled))"),
    ("format with `format` instead of the % operator - same digits for every float", TAGWRITER,
     "    return \"%.*f\" % (TERM_PRECISION, float(value))",
     "    return format(float(value), \".%df\" % TERM_PRECISION)"),
]

# Asserted the other way round: each must still go MISSED, and a gap that CLOSES fails the run so it gets
# promoted into MUTATIONS. Empty is a claim, not an omission.
KNOWN_MISSED = []

MIN_MUTATIONS = 25
PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q",
          str(TAGWRITER_TESTS), str(SCENECHECK_TESTS)]
# Past the filesystem's timestamp granularity, so a mutation always lands rather than hitting a stale .pyc.
SETTLE_S = 1.1


def repo_path(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def head_bytes(path: pathlib.Path) -> bytes:
    out = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + repo_path(path)],
                         capture_output=True)
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
    failed = [line.split(" ")[1] for line in (out.stdout or "").splitlines()
              if line.startswith("FAILED ")]
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
    """Run one population. `subjects` is the SUBJECT files only.

    Only the subjects, deliberately: the first version restored every guarded file after each mutation,
    which in `--prove-vacuity` put the emptied test files BACK after the first mutation and reported
    21 of 22 caught with no tests present. The proof caught its own harness, which is the whole reason it
    exists - a vacuity arm that cannot fail proves nothing.
    """
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
    print("%s: %d caught, %d missed, %d skipped, of %d" % (label, caught, missed, skipped,
                                                           len(population)))
    return caught, missed, skipped


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops/mutate/scenic_tags.py", description=__doc__.splitlines()[0])
    parser.add_argument("--prove-vacuity", action="store_true",
                        help="empty both test files and require every mutation to be MISSED")
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

#!/usr/bin/env python3
"""Mutation harness for T-0239's time-versus-fun menu (RouteMenu.swift, MenuRow.swift, MenuArguments.swift).

    python ops/mutate/menu.py
    python ops/mutate/menu.py --prove-vacuity
    python ops/mutate/menu.py --prove-floor

The population is ops/mutate/menu_mutations.py and the runner ops/mutate/menu_run.py; this file is the CLI,
the floors and the proof arms - straightline.py's three-file shape, under CLAUDE.md's 300-line cap.

The three subjects and the harness's own three files are compared with `git show HEAD:` before the first
build, and the subjects again afterwards: a mutation report is a claim about a COMMIT. The two test files are
not guarded, so a red-then-green demonstration can run against a suite with a test removed.

`--prove-vacuity` replaces both test files with empty suites and requires EVERY mutation to report MISSED -
not merely "not caught", which a harness broken in the compile-only direction satisfies. `--prove-floor`
shows the floor refusing on seven arms and staying quiet on the real population; it builds nothing.
"""
from __future__ import annotations

import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# A stale .pyc of the population is a false verdict (see straightline.py): none is written, none is read.
sys.dont_write_bytecode = True
shutil.rmtree(pathlib.Path(__file__).resolve().parent / "__pycache__", ignore_errors=True)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("Sources/ScenicKit/Menu/RouteMenu.swift", "Sources/ScenicKit/Menu/MenuRow.swift",
                   "Sources/ScenicPlanCLI/MenuArguments.swift")

from menu_mutations import (EQUIVALENT, MIN_EQUIVALENT, MIN_MUTATIONS, MIN_TEST_FILES, MUTATED_FILES,
                            MUTATIONS, ROOT, SUBJECTS, TEST_FILES)
from menu_run import FILTER, build, empty_suite, not_at_head, run_all, test

TESTS = [t for t in TEST_FILES if t.exists()]
HARNESS = (pathlib.Path(__file__).resolve(),
           pathlib.Path(__file__).resolve().parent / "menu_mutations.py",
           pathlib.Path(__file__).resolve().parent / "menu_run.py")


def population_floor():
    """The reason to refuse, or None. A harness that examines nothing exits 0 and proves nothing."""
    if len(MUTATIONS) < MIN_MUTATIONS:
        return "MUTATIONS holds %d entries, below the floor of %d" % (len(MUTATIONS), MIN_MUTATIONS)
    if len(EQUIVALENT) < MIN_EQUIVALENT:
        return "EQUIVALENT holds %d entries, below the floor of %d" % (len(EQUIVALENT), MIN_EQUIVALENT)
    if len(TESTS) < MIN_TEST_FILES:
        return "TESTS found %d of the %d test files, below the floor of %d" % (len(TESTS), len(TEST_FILES),
                                                                             MIN_TEST_FILES)
    nameless = [n for n, _p, _o, _w, killers in MUTATIONS if not killers]
    if nameless:
        return ("these entries name no killer: %s. `0 red of 0 named` is the killer check satisfied "
                "vacuously" % ", ".join(nameless))
    edited = {p for _n, p, _o, _w, _k in MUTATIONS}
    unmutated = [s.name for s in SUBJECTS if s not in edited]
    if unmutated:
        return ("no MUTATIONS entry edits %s; the stated subject would be wider than what is measured"
                % ", ".join(unmutated))
    return None


def prove_floor() -> int:
    """`--prove-floor`: the floor REFUSING, one arm at a time, then the control clean. Builds nothing."""
    base = {"MUTATIONS": list(MUTATIONS), "EQUIVALENT": list(EQUIVALENT), "TESTS": list(TESTS),
            "MIN_MUTATIONS": MIN_MUTATIONS}
    killers_gone = [(n, p, o, w, [] if i == 0 else k) for i, (n, p, o, w, k) in enumerate(MUTATIONS)]
    arms = [("MUTATIONS emptied", {"MUTATIONS": []}),
            ("MUTATIONS one short of the floor", {"MUTATIONS": base["MUTATIONS"][:MIN_MUTATIONS - 1]}),
            ("the floor raised to %d" % (MIN_MUTATIONS + 1), {"MIN_MUTATIONS": MIN_MUTATIONS + 1}),
            ("EQUIVALENT one short of the floor", {"EQUIVALENT": base["EQUIVALENT"][:MIN_EQUIVALENT - 1]}),
            ("one entry's killers emptied", {"MUTATIONS": killers_gone}),
            ("MenuArguments.swift unmutated, count padded back",
             {"MUTATIONS": [m for m in MUTATIONS if m[1] != SUBJECTS[2]] + MUTATIONS[:3]}),
            ("a test file missing", {"TESTS": base["TESTS"][:1]})]
    g = globals()
    refused = 0
    try:
        for label, patch in arms:
            g.update(base)
            g.update(patch)
            why = population_floor()
            sys.stdout.write("FLOOR ARM   %-48s %s\n" % (label, why or "NO REFUSAL - THIS ARM FAILED"))
            refused += 1 if why is not None else 0
        g.update(base)
        control = population_floor()
        sys.stdout.write("FLOOR ARM   %-48s %s\n" % ("CONTROL: unpatched", control or "no refusal, as required"))
    finally:
        g.update(base)
    ok = refused == len(arms) and control is None
    sys.stdout.write("FLOOR PROOF %s: %d of %d arms refused and the control did not\n"
                     % ("OK" if ok else "FAILED", refused, len(arms)))
    return 0 if ok else 1


def main(argv) -> int:
    if "--prove-floor" in argv:
        return prove_floor()
    prove = "--prove-vacuity" in argv
    refusal = population_floor()
    if refusal is not None:
        sys.stdout.write("REFUSING TO RUN: %s\n" % refusal)
        return 2
    sys.stdout.write("population  mutations=%d (floor %d)  equivalent=%d (floor %d)  subjects=%s  test "
                     "files=%d  filter=%s\n" % (len(MUTATIONS), MIN_MUTATIONS, len(EQUIVALENT), MIN_EQUIVALENT,
                                                ", ".join(s.name for s in SUBJECTS), len(TESTS), FILTER))
    dirty = not_at_head(list(MUTATED_FILES) + list(HARNESS))
    if dirty:
        sys.stdout.write("REFUSING: not what HEAD says it is: %s\n" % ", ".join(dirty))
        return 2
    pristine = {f: f.read_bytes() for f in MUTATED_FILES}
    pristine_tests = {t: t.read_bytes() for t in TESTS}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-24s md5 %s  == HEAD\n" % (f.name, hashlib.md5(b).hexdigest()))
    sys.stdout.flush()

    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: both test files replaced by empty suites; every mutation "
                             "must report MISSED.\n")
            for t in TESTS:
                t.write_text(empty_suite(t), encoding="utf-8", newline="\n")
        if build() != 0 and build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _txt = test()
        sys.stdout.write("BASELINE    --filter %-40s exit=%d\n" % (FILTER, code))
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2
        r = run_all(pristine, MUTATIONS, True)
        if not prove:
            sys.stdout.write("\nEQUIVALENT - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            for name, _p, _o, _n, witness in EQUIVALENT:
                sys.stdout.write("  witness     %s: %s\n" % (name, witness))
            eq = run_all(pristine, EQUIVALENT, False)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        for t, b in pristine_tests.items():
            t.write_bytes(b)

    still = not_at_head(MUTATED_FILES)
    if still:
        sys.stdout.write("RESTORE FAILED - not back at HEAD: %s\n" % ", ".join(still))
        return 2
    sys.stdout.write("\ncaught by the test that names it: %d of %d   (wrong killer %d, trapped %d, "
                     "compile-only %d, MISSED %d, skipped %d)\n"
                     % (len(r["caught"]), len(MUTATIONS), len(r["wrong_killer"]), len(r["trapped"]),
                        len(r["compile_only"]), len(r["missed"]), len(r["skipped"])))
    if prove:
        ok = len(r["caught"]) == 0 and len(r["missed"]) == len(MUTATIONS)
        sys.stdout.write("VACUITY PROOF %s: with the %d test file(s) emptied, caught=%d (need 0) and "
                         "MISSED=%d of %d\n" % ("OK" if ok else "FAILED", len(TESTS), len(r["caught"]),
                                                len(r["missed"]), len(MUTATIONS)))
        return 0 if ok else 1
    eq_caught = len(eq["caught"]) + len(eq["wrong_killer"])
    eq_ok = len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))
    ok = len(r["caught"]) == len(MUTATIONS) and eq_ok
    sys.stdout.write("MUTATE %s  caught=%d/%d equivalent_caught=%d\n"
                     % ("OK" if ok else "FAILED", len(r["caught"]), len(MUTATIONS), eq_caught))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Mutation harness for LambdaSearch. A catch requires a NAMED TEST to fail, not a non-zero exit.

Tracked in ops/ rather than .artifacts/, because .artifacts/ is gitignored and a task whose `acceptance:`
line names a file nobody else can run has no reproducible red evidence. Each mutation is built first: a
mutation that does not compile is reported `compile-only` and does not count, since a compiler error is a
fact about Swift and not about this suite.

Run `--prove-vacuity` to check the harness itself: it replaces EVERY test file in TEST_FILES with an empty
suite and requires every mutation to report MISSED. A harness that still reports catches with no tests
present is measuring the compiler. Emptying only one of two suites is how this proof was false once; the
wording is plural because the code is.

This file is the protocol. The mutations that must be caught are in budget_mutations.py and, for the ones
that move a threshold by a hair rather than delete a guard, budget_boundaries.py; the two arms that must go
MISSED are in budget_arms.py; what the run does to the working tree is in budget_tree.py; and the three
subject paths they all share are in budget_paths.py - each split off at the 300-line cap, along a boundary
of meaning rather than at a line number. Contract, unchanged from ops/mutate/gates.py and T-0132:
  * the pass condition is `caught == len(MUTATIONS)`; a trap, a compile failure and a stale anchor each FAIL;
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`;
  * the EQUIVALENT and KNOWN_MISSED arms require MISSED specifically, not merely "not caught";
  * the baseline is built twice before it is called broken, like every mutation;
  * an empty population REFUSES rather than reporting a clean sheet over nothing - `--prove-floor`
    demonstrates that refusal, and the one-entry-short refusal too, and costs no build;
  * a subject that does not match `git show HEAD:` REFUSES, because every verdict here is a statement about
    the content of those files - `--prove-dirty` demonstrates it, and costs no build.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

# The population lives next to this file, not on the caller's sys.path: `python ops/mutate/budget.py` from
# the repo root and `./ops/mutate/budget.py` must both find it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from budget_arms import EQUIVALENT, KNOWN_MISSED, MIN_EQUIVALENT
from budget_mutations import MIN_MUTATIONS, MUTATIONS
from budget_paths import ROOT, SUBJECTS

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06). The gate
# reads this tuple as text; the Path objects above are what the run actually mutates.
SUBJECT_MODULES = ("Sources/ScenicKit/Budget/LambdaSearch.swift",
                   "Sources/ScenicKit/Budget/BudgetError.swift",
                   "Sources/ScenicKit/Budget/BudgetOutcome.swift")
from budget_tree import (SENTINEL, SENTINEL_MESSAGE, TEST_FILES, differs_from_head, prove_blind,
                         prove_dirty, unanswerable)

SCRATCH = ".build-mutate-budget"


def empty_suite(path: pathlib.Path) -> str:
    """An empty suite named after the file it replaces - two identically-named structs would not compile, and
    a compile failure would make the vacuity proof pass for the wrong reason."""
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))


FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def build() -> int:
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(pristine, mutations):
    """Returns a verdict per mutation. SKIP is its own bucket, never folded into MISSED: a mutation that did
    not land tells you the harness is stale, which is the opposite of what MISSED means."""
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    for name, path, old, new in mutations:
        text = pristine[path].decode("utf-8")
        if old not in text:
            sys.stdout.write("SKIP        %-62s anchor not found - harness is stale\n" % name)
            out["skipped"].append(name)
            continue
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if path.read_bytes() == pristine[path]:
                sys.stdout.write("SKIP        %-62s mutation did not land\n" % name)
                out["skipped"].append(name)
                continue
            # Built twice before a compile failure is believed: other agents run swift builds on this box
            # concurrently and a transient scratch collision produced a false compile-only verdict once.
            if build() != 0 and build() != 0:
                verdict, code = "compile_only", 1
            else:
                code, txt = test()
                verdict = "caught" if FAIL_LINE.search(txt) else ("trapped" if code != 0 else "missed")
        finally:
            path.write_bytes(pristine[path])
        out[verdict].append(name)
        label = {"caught": "caught", "trapped": "trapped", "compile_only": "compile-only", "missed": "MISSED"}
        note = {"caught": "exit=%d" % code,
                "trapped": "non-zero exit, but NO named test failed - does not count",
                "compile_only": "a fact about Swift, not about these tests - does not count",
                "missed": "exit=0  no test objected"}
        sys.stdout.write("%-12s%-62s %s\n" % (label[verdict], name, note[verdict]))
    return out


def head_line(snapshot) -> str:
    """The sentence this run prints about the HEAD comparison, as a function of what git could answer.

    N-SG2: this used to be `"subjects match git show HEAD: yes (%d files)"` in an else-branch, printed
    whatever happened. `differs_from_head` deliberately treats "git cannot answer" as not-dirty, so with git
    unreachable it returns [] over a mutated subject and that line asserted a comparison that never ran - a
    harness making the exact claim it exists to stop anyone else making. A function rather than a `write`
    inside `main` so the blind case can be DEMONSTRATED without a build; the demo is in the task Log."""
    blind = unanswerable(snapshot)
    line = ("subjects compared with git show HEAD: %d of %d match\n"
            % (len(snapshot) - len(blind), len(snapshot)))
    if blind:
        line += ("  NOT COMPARED: git could not answer for %s, so nothing here is a statement about those\n"
                 "  committed bytes - a mutation left on disk in one of them would not have been seen.\n"
                 % ", ".join(f.name for f in blind))
    return line


def population_ok() -> bool:
    """A FLOOR on the harness's own evidence. `caught == len(MUTATIONS)` is satisfied by an empty list - 0 of
    0, exit 0 - so an emptied or truncated population would report the cleanest sheet this file can print.
    ops/lib/check-exec-bits refuses the same way with MIN_FILES. KNOWN_MISSED is exempt: empty there is the
    honest state, and its own arm is what guards it."""
    bad = []
    if len(MUTATIONS) < MIN_MUTATIONS:
        bad.append("MUTATIONS has %d, floor is %d" % (len(MUTATIONS), MIN_MUTATIONS))
    if len(EQUIVALENT) < MIN_EQUIVALENT:
        bad.append("EQUIVALENT has %d, floor is %d" % (len(EQUIVALENT), MIN_EQUIVALENT))
    for b in bad:
        sys.stdout.write("POPULATION FLOOR: %s. A shrunken list must never read as a clean sheet.\n" % b)
    return not bad


def prove_floor() -> int:
    """`--prove-floor`: demonstrate the floor instead of asserting it. Shipped as a flag rather than left in
    a scratch script for the same reason this harness is tracked at all - a demonstration that only exists in
    a gitignored directory is one nobody else can re-run. Costs no build.

    THREE arms, because two of them are different claims. Emptied proves the floor refuses a gutted
    population; ONE ENTRY SHORT proves it refuses a quiet trim, which is what a floor of 22 against 34
    entries did NOT do while its own comment said it caught "an emptied or truncated" list. The third puts
    the real lists back and requires them to pass, so a floor set above the population cannot hide here."""
    global MUTATIONS, EQUIVALENT
    real = (MUTATIONS, EQUIVALENT)
    try:
        MUTATIONS, EQUIVALENT = [], []
        sys.stdout.write("with the population emptied:\n")
        refused_empty = not population_ok()

        MUTATIONS, EQUIVALENT = real[0][:-1], real[1][:-1]
        sys.stdout.write("with one mutation and one equivalent deleted (%d, %d):\n"
                         % (len(MUTATIONS), len(EQUIVALENT)))
        refused_short = not population_ok()
    finally:
        MUTATIONS, EQUIVALENT = real
    sys.stdout.write("with the real population (%d mutations, %d equivalent):\n"
                     % (len(MUTATIONS), len(EQUIVALENT)))
    restored = population_ok()
    ok = refused_empty and refused_short and restored
    sys.stdout.write("FLOOR PROOF %s: emptied -> refused=%s, one deleted -> refused=%s, real -> accepted=%s\n"
                     "  (without this floor `caught == len(MUTATIONS)` reads 0 of 0 and exits 0; without the\n"
                     "   middle arm the floor can sit far below the list and refuse nothing anybody would do)\n"
                     % ("OK" if ok else "FAILED", refused_empty, refused_short, restored))
    return 0 if ok else 1


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    if "--prove-floor" in argv:
        return prove_floor()
    if "--prove-dirty" in argv:
        return prove_dirty(sys.stdout.write)
    if "--prove-blind" in argv:
        return prove_blind(sys.stdout.write, head_line)
    if not population_ok():
        return 2
    if SENTINEL.exists():
        sys.stdout.write(SENTINEL_MESSAGE % SENTINEL)
        return 2
    pristine = {f: f.read_bytes() for f in SUBJECTS}
    pristine_tests = {f: f.read_bytes() for f in TEST_FILES}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    # The md5s above used to be printed and nothing else - a number for a human to read, which is what the
    # task Log was crediting when it said the subjects "are checked against HEAD". They are now CHECKED: the
    # third review planted a live mutation by hand, ran this harness with no sentinel present, and got
    # `pristine ... md5 d08228d8`, `BASELINE exit=0` and `34 of 34 caught` over a corrupted subject, exit 0.
    # Every verdict below is a statement about the content of these files, so measuring the wrong content
    # makes every line of the report false at once.
    dirty = differs_from_head(pristine)
    if dirty and "--allow-dirty-subject" not in argv:
        sys.stdout.write(
            "REFUSING: %s does not match `git show HEAD:`.\n"
            "  A mutation left on disk - by a killed run of this harness, or by a hand-run red demo that\n"
            "  died before its restore - would be snapshotted as `pristine` and every verdict measured\n"
            "  against it. Check `git diff -- Sources/ScenicKit/Budget/`, restore, and run again.\n"
            "  If the change is yours and deliberate, re-run with --allow-dirty-subject.\n"
            % ", ".join(f.name for f in dirty))
        return 2
    if dirty:
        sys.stdout.write("--allow-dirty-subject: measuring %s as it is on disk, NOT as committed. Every\n"
                         "  verdict below is about that content and not about HEAD.\n"
                         % ", ".join(f.name for f in dirty))
    else:
        sys.stdout.write(head_line(pristine))

    eq = None
    known = None
    SENTINEL.parent.mkdir(parents=True, exist_ok=True)
    SENTINEL.write_text("mutating %s\n" % ", ".join(f.name for f in SUBJECTS), encoding="utf-8")
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: EVERY test file is replaced by an empty suite, so every\n"
                             "mutation must report MISSED - not merely 'not caught'.\n")
            for f in TEST_FILES:
                f.write_text(empty_suite(f), encoding="utf-8", newline="\n")

        # Built TWICE before the baseline is declared broken, for the same reason each mutation is (T-0132).
        # On this Windows checkout a first build into a fresh scratch directory can fail with "unable to
        # create symbolic link ... I/O error (code: 512)" and succeed immediately after. The mutation loop
        # allowed for that and the baseline did not, so a transient failure would abort the whole run with
        # "baseline does not build" and nothing would ever be measured.
        if build() != 0 and build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _ = test()
        sys.stdout.write("BASELINE                                                              exit=%d\n" % code)
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2

        r = run_all(pristine, MUTATIONS)

        if not prove:
            sys.stdout.write("\nKNOWN GAPS - asserted MISSED on purpose; a catch here means the gap closed\n")
            if KNOWN_MISSED:
                known = run_all(pristine, KNOWN_MISSED)
            else:
                sys.stdout.write("  (none - every mutation above is claimed to be caught by a named test)\n")
            sys.stdout.write("\nEQUIVALENT MUTANTS - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            eq = run_all(pristine, EQUIVALENT)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        for f, b in pristine_tests.items():
            f.write_bytes(b)
        SENTINEL.unlink()

    if any(f.read_bytes() != b for f, b in pristine.items()) or any(f.read_bytes() != b for f, b in pristine_tests.items()):
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2

    sys.stdout.write("\nrestored: " + ", ".join(hashlib.md5(f.read_bytes()).hexdigest()[:8] for f in pristine) + "\n")
    sys.stdout.write("caught by a named test: %d of %d   (trapped %d, compile-only %d, MISSED %d, skipped %d)\n"
                     % (len(r["caught"]), len(MUTATIONS), len(r["trapped"]), len(r["compile_only"]),
                        len(r["missed"]), len(r["skipped"])))
    for bucket, why in (("trapped", "detected, but by a crash and not an assertion - DOES NOT COUNT"),
                        ("compile_only", "a compile failure is not a test catch - DOES NOT COUNT"),
                        ("missed", "no test objected"),
                        ("skipped", "anchor missing - the harness is stale")):
        for n in r[bucket]:
            sys.stdout.write("  %s: %s (%s)\n" % (bucket.upper(), n, why))

    if prove:
        ok = len(r["caught"]) == 0 and len(r["missed"]) == len(MUTATIONS)
        sys.stdout.write("VACUITY PROOF %s: with no tests present, caught=%d (need 0) and MISSED=%d of %d\n"
                         "  (requiring MISSED to be complete, not just caught==0, is what stops a harness\n"
                         "   broken in the compile-only direction from proving its own non-vacuity)\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(r["missed"]), len(MUTATIONS)))
        return 0 if ok else 1

    # MISSED specifically, on both arms. `missed + trapped` was the `caught + trapped` shape F6 was filed
    # for, left standing in this one arm: a KNOWN_MISSED mutation that starts CRASHING the runner would keep
    # the arm green instead of prompting a look at why a gap changed shape.
    known_ok = not KNOWN_MISSED or (known is not None and len(known["missed"]) == len(KNOWN_MISSED))
    if not known_ok and known is not None:
        sys.stdout.write("KNOWN-GAP ARM FAILED: %d of %d still MISSED. A gap that closed is good news - move "
                         "it into MUTATIONS. A gap that now traps or fails to build is not a gap any more "
                         "either.\n" % (len(known["missed"]), len(KNOWN_MISSED)))
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok and known_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Mutation harness for the safety gates. A catch requires a NAMED TEST to fail, not a non-zero exit.

The mutation corpus is ops/mutate/gates_corpus.py; this file is the runner and the floors.

The mutations that matter most are the nineteen under THE INVARIANT there. If the suite does not catch them,
the suite does not protect the invariant CLAUDE.md lists first - motorway and trunk are PENALISED, not
excluded - and this repository has already broken that once, making the flagship Mountain View -> SF fixture
unroutable. Most of them exist because reviews of PR #82 refused freeway geometry with the whole suite green,
twelve shapes in all: `motorway_link` + `oneway`, `motorroad`, `expressway`, `foot`/`bicycle`, `lanes`,
`maxspeed`, `destination`, `horse`, a `horse`/`moped` loop, `motor_vehicle != "yes"`, and then `sidewalk` and
`int_ref` from the sixth review. Roughly half the rest turn a rule that requires positive evidence into one
that fires on a tag being absent or merely present - how a gate set quietly starts refusing rural roads.

Written on the corrected contract (T-0132, and the harness discussion on PR #70):
  * the pass condition is `caught == len(MUTATIONS)`. A trap, a compile failure and a stale anchor each FAIL
    the run - `caught + len(trapped)` was the defect found on PR #70, where breaking a harness's own
    FAIL_LINE regex produced "caught: 0, trapped: 3" and exit 0;
  * a catch means a NAMED test recorded an issue, and the name is PRINTED. A non-zero exit with no name is a
    trap. The second review of PR #82 had to write its own runner to establish the names this one now prints;
  * every subject and every discovered test file must be byte-identical to `git show HEAD:` BEFORE anything
    is built. That review put one line into Gates.swift and this harness measured the mutant and printed
    "28 of 28", exit 0, while the invariant was broken on disk;
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`, and empties EVERY test file that
    could catch a mutation - discovered, not hardcoded, see TEST_FILES below;
  * the EQUIVALENT arm requires MISSED specifically, not merely "not caught";
  * the KNOWN_MISSED arm is asserted the other way round, and is actually executed.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from gates_corpus import CONSIDERED, DECISION, EQUIVALENT, GATES, KNOWN_MISSED, MUTATIONS, REASON  # noqa: E402

SUBJECTS = (GATES, DECISION, REASON, CONSIDERED)

# Inside `.build/`, which .gitignore already covers. As `.build-mutate-gates` it left an untracked directory
# behind after every run, and ops/lib/check-worktrees only reports untracked paths inside the task's
# `touches:`, so nothing complained. Raised on the first review of PR #82.
SCRATCH = ".build/mutate-gates"

# Every suite that could catch a mutation - DISCOVERED, not one hardcoded path.
#
# T-0132: a suite split at the 300-line cap silently broke the hardcoded-single-path form in five separate
# harnesses. The half that moved out kept catching mutations while `--prove-vacuity` went on printing "EVERY
# test file is replaced". The reviewer of PR #82 reproduced that decay here, and the second round of fixes
# split this very suite into three files - so the decay would have landed for real. A file counts if it
# mentions any of the three symbols under test; that is a property of the tree, so a split half is picked up
# the moment it exists.
SUBJECT_SYMBOLS = re.compile(r"\bGates\b|\bGateDecision\b|\bGateReason\b|\bConsideredTags\b")


def discover_test_files():
    out = []
    for p in sorted((ROOT / "Tests").rglob("*.swift")):
        if SUBJECT_SYMBOLS.search(p.read_text(encoding="utf-8", errors="replace")):
            out.append(p)
    return out


TEST_FILES = discover_test_files()

# Floors on the HARNESS's own population.
#
# Found by the sign-off reviewer of PR #73, against this file specifically: `return 0 if caught ==
# len(MUTATIONS) and eq_ok and known_ok else 1` is VACUOUSLY TRUE on empty lists. Emptying the lists gives
# "caught by a named test: 0 of 0 ... exit 0" and, worse, "VACUITY PROOF OK ... MISSED=0 of 0".
#
# MIN_MUTATIONS IS THE REAL COUNT, not a round number below it. At 18 against a population of 21 the floor
# refused an empty corpus but not a deletion, so the first reviewer of PR #82 deleted BOTH motorway mutations
# plus one more and got `caught by a named test: 18 of 18 ... exit 0` - a clean sheet with the invariant no
# longer measured. Adding a mutation means bumping this number, in a different file from the list itself.
MIN_MUTATIONS = 48
MIN_EQUIVALENT = 2

# NOT a completeness floor, and it must not be read as one: TEST_FILES is discovered precisely so that the
# count CAN change when a suite is split, and a floor at today's count would fail on the split it exists to
# survive. It refuses one thing only - a discovery that matched nothing.
MIN_TEST_FILES = 1

# A catch is a NAMED test recording an issue, and group 1 is that name. Swift Testing prints
#   x Test "a motorway is never gated, because ..." recorded an issue at GatesTests.swift:40:9: ...
# for a display-named test and `Test motorwayIsNeverGated() recorded an issue` for one without. Also matching
# "Test run with N tests ... failed" - which is what this regex used to be alone - counts a crash or any
# other non-assertion failure as a catch, and names nothing.
FAIL_LINE = re.compile(r'Test\s+(?:"([^"]*)"|([A-Za-z_]\w*\(\)))\s+recorded an issue')


def failing_test_names(txt: str):
    """The distinct NAMES that recorded an issue, in order. Empty means nothing named objected. A regex
    broken in the over-matching direction (no capture group, matching every line) still yields "names" here,
    so the EQUIVALENT arm goes on catching that: it would report the equivalent mutant caught."""
    seen = []
    for m in FAIL_LINE.finditer(txt):
        groups = [g for g in (m.groups() or ()) if g]
        name = groups[0] if groups else " ".join(m.group(0).split())[:60]
        if name not in seen:
            seen.append(name)
    return seen


def head_bytes(path: pathlib.Path):
    rel = path.relative_to(ROOT).as_posix()
    p = subprocess.run(["git", "show", "HEAD:" + rel], cwd=ROOT, capture_output=True)
    return p.stdout if p.returncode == 0 else None


def not_at_head(paths):
    """Paths whose bytes on disk differ from `git show HEAD:`, with why. Without this the harness snapshots
    whatever is on disk as "pristine" and measures THAT: the second review of PR #82 put one `expressway`
    branch into Gates.swift, ran this harness unmodified, and got "caught by a named test: 28 of 28" / exit 0
    over a tree that hard-excludes every expressway-tagged motorway. Printing the md5 was not enough."""
    bad = []
    for p in paths:
        h = head_bytes(p)
        if h is None:
            bad.append((p, "not tracked at HEAD"))
        elif h != p.read_bytes():
            bad.append((p, "differs from HEAD"))
    return bad


def empty_suite(path: pathlib.Path) -> str:
    """An empty suite named after the file it replaces - two identically-named structs would not compile, and
    a compile failure would make the vacuity proof pass for the wrong reason."""
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))


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
        names = []
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
                names = failing_test_names(txt)
                verdict = "caught" if names else ("trapped" if code != 0 else "missed")
        finally:
            path.write_bytes(pristine[path])
        out[verdict].append(name)
        label = {"caught": "caught", "trapped": "trapped", "compile_only": "compile-only", "missed": "MISSED"}
        note = {"caught": "by: " + " | ".join(names),
                "trapped": "non-zero exit, but NO named test failed - does not count",
                "compile_only": "a fact about Swift, not about these tests - does not count",
                "missed": "exit=0  no test objected"}
        sys.stdout.write("%-12s%-62s %s\n" % (label[verdict], name, note[verdict]))
    return out


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    if len(MUTATIONS) < MIN_MUTATIONS or len(EQUIVALENT) < MIN_EQUIVALENT:
        sys.stdout.write("REFUSING: %d mutations and %d equivalent mutants, expected at least %d and %d.\n"
                         "A harness that examines nothing exits 0 and proves nothing.\n"
                         % (len(MUTATIONS), len(EQUIVALENT), MIN_MUTATIONS, MIN_EQUIVALENT))
        return 2
    if len(TEST_FILES) < MIN_TEST_FILES:
        sys.stdout.write("REFUSING: discovered %d test file(s) mentioning Gates/GateDecision/GateReason,\n"
                         "expected at least %d. With none, --prove-vacuity would empty nothing.\n"
                         % (len(TEST_FILES), MIN_TEST_FILES))
        return 2

    pristine = {f: f.read_bytes() for f in SUBJECTS}
    pristine_tests = {f: f.read_bytes() for f in TEST_FILES}

    # BEFORE any build, and before --prove-vacuity empties anything.
    dirty = not_at_head(list(pristine) + list(pristine_tests))
    if dirty:
        sys.stdout.write("REFUSING: the subject is not what HEAD says it is, so nothing measured below would\n"
                         "mean anything. A mutant left on disk reads as 'pristine' and the run certifies it.\n")
        for p, why in dirty:
            sys.stdout.write("  %s: %s\n" % (p.relative_to(ROOT).as_posix(), why))
        sys.stdout.write("Commit or restore these, then re-run.\n")
        return 2

    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s  == HEAD\n" % (f.name, hashlib.md5(b).hexdigest()))
    sys.stdout.write("test files discovered: %s\n" % ", ".join(f.name for f in TEST_FILES))

    eq = None
    known = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: EVERY test file that mentions the subject is replaced by\n"
                             "an empty suite (%d discovered), so every mutation must report MISSED - not\n"
                             "merely 'not caught'.\n" % len(TEST_FILES))
            for f in TEST_FILES:
                f.write_text(empty_suite(f), encoding="utf-8", newline="\n")

        # Built TWICE before the baseline is declared broken, for the same reason each mutation is. On this
        # Windows checkout a first build into a fresh scratch directory can fail with "unable to create
        # symbolic link ... I/O error (code: 512)" and succeed immediately after. The mutation loop allowed
        # for that; the baseline did not, so a transient failure aborted the run and nothing was measured.
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
            sys.stdout.write("\nEQUIVALENT MUTANTS - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            eq = run_all(pristine, EQUIVALENT)
            if KNOWN_MISSED:
                sys.stdout.write("\nKNOWN GAPS - each must still go MISSED; a gap that closed FAILS the run\n")
                known = run_all(pristine, KNOWN_MISSED)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        for f, b in pristine_tests.items():
            f.write_bytes(b)

    if not_at_head(list(pristine) + list(pristine_tests)):
        sys.stdout.write("RESTORE FAILED - the working tree is not back at HEAD\n")
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
        sys.stdout.write("VACUITY PROOF %s: with the %d discovered test file(s) emptied, caught=%d (need 0)\n"
                         "  and MISSED=%d of %d\n"
                         "  (requiring MISSED to be complete, not just caught==0, is what stops a harness\n"
                         "   broken in the compile-only direction from proving its own non-vacuity)\n"
                         % ("OK" if ok else "FAILED", len(TEST_FILES), len(r["caught"]),
                            len(r["missed"]), len(MUTATIONS)))
        return 0 if ok else 1

    known_ok = True
    if KNOWN_MISSED:
        known_ok = known is not None and len(known["missed"]) + len(known["trapped"]) == len(KNOWN_MISSED)
        if not known_ok:
            sys.stdout.write("KNOWN-GAP ARM FAILED: %d of %d stayed MISSED as asserted. A gap that closed is\n"
                             "  good news - move it into MUTATIONS.\n"
                             % (0 if known is None else len(known["missed"]) + len(known["trapped"]),
                                len(KNOWN_MISSED)))
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok and known_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Mutation harness for the hazard strip. A catch requires a NAMED TEST to fail, not a non-zero exit.

Shape settled by six rounds of review on this file and its siblings:

  * each mutation is BUILT first, and a compile failure is `compile-only` and does not count, because a
    compiler error is a fact about Swift and not about this suite;
  * a mutation detected by a TRAP rather than an assertion is reported separately AND DOES NOT COUNT - a
    crash is the suite noticing, but not through a check;
  * SKIP is its own bucket - a mutation that did not land means the harness is STALE, which is the
    opposite of what MISSED means;
  * EQUIVALENT mutants are asserted the OTHER WAY ROUND: they cannot change behaviour, so a catch there is
    a FAILURE, because it means a test has an opinion about how the code is written rather than what it
    does - and the way a person satisfies such a demand is by anchoring a test on source text;
  * the subject is compared to `git show HEAD:` BEFORE anything is built, and a difference REFUSES. The
    PR #80 reviewer planted a behaviour-changing line on a row no anchor quotes and this harness printed
    "pristine", "BASELINE exit=0", "21 of 21", exit 0 - certifying a defective subject with a clean sheet.
    "Pristine" was a word about a variable, not a claim anyone checked. Now it is checked, and the final
    restore is verified against HEAD too rather than against bytes this process read from the same disk;
  * `--prove-vacuity` empties EVERY test file that can catch a mutation and requires every mutation to
    report MISSED - COMPLETE, and not merely `caught == 0`, which a harness broken in the compile-only
    direction also satisfies. Which files those are is GREPPED each run (`subject_test_files()`), and a
    file found by the grep that is not in `EMPTIED` refuses the run rather than being silently left
    populated - the proof's "no tests present" premise would otherwise be false;
  * EVERY build is retried once, the baseline included, before a failure is believed: a fresh scratch dir
    on this box fails with an I/O 512 symlink error often enough to have produced a false verdict;
  * the floors below EQUAL the shipped population, so deleting any one mutation refuses the run;
  * the pass condition is `caught == len(MUTATIONS)`. It shipped as `caught + trapped ==` and the PR #70
    reviewer showed what that buys: with the subject pristine and only FAIL_LINE broken, everything scores
    `trapped` and the run exits 0 - the harness cannot tell "covered" from "I am broken".

Half the mutations move a NUMBER or a comparison direction, because an earlier harness was all-structural -
delete a guard, invert a comparison - which is exactly where such a suite is blind. The batch added after
the FIRST PR #80 review attacked the blind spot it found - a hazard removed at the TOP of its range - and
the batch added after the SECOND attacks what that fix left behind: each ceiling had been closed by probing
one value above it, so `.prefix(9)` and `noCellMinutes <= 100_000` survived a suite that had just closed
`.prefix(7)` and `< 600`. A ceiling is only gone when the probe is at the top of the TYPE.

TWO entries lost their anchor when the second review's blocker was fixed (`where !c.source.isEmpty` no
longer exists in the source). They were REPLACED by three, not dropped: every way of losing an unattributed
closure that they protected is now a mutation that must be CAUGHT, and the third covers the option the
review named and nothing tested. This file is not under the 300-line cap; P-SRC-02 asserts
that over `Sources/**/*.swift` and `Tests/**/*.swift`, and ops/lib/queue.py is 1007 lines.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
STRIP = ROOT / "Sources" / "ScenicKit" / "Hazards" / "HazardStrip.swift"
FLAG = ROOT / "Sources" / "ScenicKit" / "Hazards" / "HazardFlag.swift"
TESTS = ROOT / "Tests" / "ScenicKitTests" / "HazardStripTests.swift"
OMISSION_TESTS = ROOT / "Tests" / "ScenicKitTests" / "HazardStripOmissionTests.swift"
# Every test file `--prove-vacuity` empties. `subject_test_files()` greps for the real set each run and the
# run REFUSES if the grep finds one that is not here, so this tuple cannot quietly go stale.
EMPTIED = (TESTS, OMISSION_TESTS)
# Everything the run must find byte-identical to HEAD before it builds anything: the two subjects, both
# test files, and this harness. A mutation report is a claim about a COMMIT, and it is worth nothing about
# a dirty tree. Stated plainly, because it is a real limit: including this file catches an uncommitted
# local edit to the instrument, NOT an author who deletes the check - the modified code is what runs. The
# floors, the EQUIVALENT arm and `--prove-vacuity` are the guards against a weakened harness; this one is
# against measuring something other than what is under review.
HEAD_CHECKED = (STRIP, FLAG, TESTS, OMISSION_TESTS, pathlib.Path(__file__).resolve())
SCRATCH = ".build/mutate-hazards"  # inside .build/, which .gitignore covers: the harness must not dirty
                                   # the worktree it certifies, and `ops/sane` counts untracked files.


def empty_suite(path: pathlib.Path) -> str:
    """A distinct suite and type name per file - two files both declaring `EmptyHazardSuite` would be a
    redeclaration error, and the vacuity proof would then be measuring the Swift compiler again."""
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%sSuite {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (path.stem, path.stem))

# Floors on the HARNESS's own population. Without them the pass condition and `--prove-vacuity` are both
# VACUOUSLY TRUE on empty lists - "0 of 0 ... exit 0" and "VACUITY PROOF OK ... MISSED=0 of 0", the proof
# certifying its own vacuity. The failure that actually occurs is a mutation removed with a plausible
# reason and nothing to say the count fell - so these EQUAL the shipped population rather than sitting
# under it. The PR #80 reviewer found 13 here against 15 shipped, which refuses nothing: two could go.
# Adding a mutation means raising these by hand, which is the point - the number is a claim, not a length.
# 21 -> 28: two entries whose anchor no longer exists were replaced by three that pin the SAME behaviour
# from the other side (an unattributed closure must reach the strip), plus five from the PR #80 review,
# plus one for the empty-TAG guard, which the closure fix left with a test but no mutation.
MIN_MUTATIONS = 28
MIN_EQUIVALENT = 3

MUTATIONS = [
    # --- the thresholds -------------------------------------------------------------------------------
    ("surface threshold 2 km -> 0.1, so every rural lane raises it", STRIP,
     "public static let surfaceUnknownMinimumKm = 2.0",
     "public static let surfaceUnknownMinimumKm = 0.1"),

    ("surface threshold 2 km -> 50, so it never fires", STRIP,
     "public static let surfaceUnknownMinimumKm = 2.0",
     "public static let surfaceUnknownMinimumKm = 50.0"),

    ("surface comparison non-strict, so exactly 2 km fires", STRIP,
     "if facts.surfaceUnknownKm > surfaceUnknownMinimumKm {",
     "if facts.surfaceUnknownKm >= surfaceUnknownMinimumKm {"),

    ("no-cell threshold 5 -> 60 minutes", STRIP,
     "public static let noCellMinimumMinutes = 5",
     "public static let noCellMinimumMinutes = 60"),

    ("no-cell comparison strict, so exactly 5 minutes stops firing", STRIP,
     "if facts.noCellMinutes >= noCellMinimumMinutes {",
     "if facts.noCellMinutes > noCellMinimumMinutes {"),

    ("twilight fires on arrival at or before dusk", STRIP,
     "let twilight = facts.civilTwilight, arrival > twilight {",
     "let twilight = facts.civilTwilight, arrival >= twilight {"),

    # --- the ordering, which is the product -----------------------------------------------------------
    ("closures sort last instead of first", FLAG,
     "        case .closure:          return 0",
     "        case .closure:          return 9"),

    ("surface advisory outranks a ford", FLAG,
     "        case .surfaceUnknown:   return 6",
     "        case .surfaceUnknown:   return 0"),

    ("an unrecognised tag sorts below the advisories", FLAG,
     "        case .unrecognised:     return 3",
     "        case .unrecognised:     return 8"),

    # NOT named "losing the stable order": the replacement also inverts the comparator, so its catch is
    # evidence about the DIRECTION of the sort and says nothing about stability. The PR #80 reviewer was
    # right that the old name claimed more than the mutation shows. Stability within one severity cannot
    # be mutation-tested here at all - see the EQUIVALENT list for why.
    ("sort by rank DESCENDING, so the strip is read worst-last", STRIP,
     "        return out.enumerated()\n"
     "            .sorted { ($0.element.severityRank, $0.offset) < ($1.element.severityRank, $1.offset) }\n"
     "            .map(\\.element)",
     "        return out.sorted { $0.severityRank > $1.severityRank }"),

    # --- nothing is dropped ---------------------------------------------------------------------------
    ("drop the unclassified tags entirely", STRIP,
     "        for tag in Set(facts.unclassified).sorted() where !tag.isEmpty {\n"
     "            out.append(.unrecognised(tag))\n"
     "        }",
     "        // unclassified dropped"),

    ("stop deduplicating the unknown tags", STRIP,
     "        for tag in Set(facts.unclassified).sorted() where !tag.isEmpty {",
     "        for tag in facts.unclassified where !tag.isEmpty {"),

    # The OTHER empty string. `emptyStringsIgnored` lost its closure assertion when the PR #80 blocker was
    # fixed, leaving it with one assertion and - until this entry - no mutation pinning it, so it could
    # have rotted into a test that cannot fail. An empty TAG really is nothing: there the string IS the
    # hazard, which is the whole distinction the closure fix rests on, so it is worth a mutation of its own.
    ("accept an empty unknown tag as a hazard", STRIP,
     "        for tag in Set(facts.unclassified).sorted() where !tag.isEmpty {",
     "        for tag in Set(facts.unclassified).sorted() {"),

    ("report a ford as a gate", STRIP,
     "        if facts.hasFord { out.append(.ford) }",
     "        if facts.hasFord { out.append(.gate) }"),

    # --- the PR #80 blocker, now pinned in BOTH directions ----------------------------------------------
    # These three replace "accept a closure with no source" and "widen the closure source guard to swallow
    # a whitespace source", which pinned the OPPOSITE behaviour and whose anchor
    # (`where !c.source.isEmpty`) no longer exists in the source. They are not deletions dressed up: every
    # way of losing an unattributed closure that the old pair protected is reinstated here as a mutation
    # that must be CAUGHT, and a third covers the option the review named but nothing tested.
    ("drop a closure whose source is empty - the rank-0 hazard that vanished in PR #80", STRIP,
     "        for c in facts.closures {",
     "        for c in facts.closures where !c.source.isEmpty {"),

    ("drop a closure whose source is only whitespace", STRIP,
     "        for c in facts.closures {",
     "        for c in facts.closures where !c.source.trimmingCharacters(in: .whitespaces).isEmpty {"),

    ("demote an unattributed closure to .unrecognised, rank 0 -> rank 3", STRIP,
     "        for c in facts.closures {\n"
     "            out.append(.closure(source: c.source, until: c.until))\n"
     "        }",
     "        for c in facts.closures {\n"
     "            out.append(c.source.isEmpty ? .unrecognised(\"closure\")\n"
     "                                        : .closure(source: c.source, until: c.until))\n"
     "        }"),

    ("a clean route gets a reassuring flag", STRIP,
     "        var out: [HazardFlag] = []",
     "        var out: [HazardFlag] = [.unrecognised(\"checked\")]"),

    # --- nothing is dropped AT THE TOP OF ITS RANGE either ----------------------------------------------
    # Added after the PR #80 review. Every mutation above removes a hazard at its FLOOR or removes a whole
    # category; none took one away for being too big, and four such mutations survived the shipped suite.
    # Seven is the number of flag KINDS, so a strip truncated there looked complete in every fixture.
    ("truncate the strip to the first seven flags", STRIP,
     "        return out.enumerated()\n"
     "            .sorted { ($0.element.severityRank, $0.offset) < ($1.element.severityRank, $1.offset) }\n"
     "            .map(\\.element)",
     "        return Array(out.enumerated()\n"
     "            .sorted { ($0.element.severityRank, $0.offset) < ($1.element.severityRank, $1.offset) }\n"
     "            .map(\\.element).prefix(7))"),

    ("no-cell silently stops firing above 600 minutes", STRIP,
     "        if facts.noCellMinutes >= noCellMinimumMinutes {",
     "        if facts.noCellMinutes >= noCellMinimumMinutes && facts.noCellMinutes < 600 {"),

    ("the surface advisory silently stops firing above 100 km", STRIP,
     "        if facts.surfaceUnknownKm > surfaceUnknownMinimumKm {",
     "        if facts.surfaceUnknownKm > surfaceUnknownMinimumKm && facts.surfaceUnknownKm < 100 {"),

    # --- ... and at the top of the TYPE, not merely above the last fixture's number --------------------
    # The three below are the PR #80 reviewer's surviving mutations (SG1, SG14) and their siblings. Each of
    # the three above was closed by probing one value bigger than the ceiling, which only MOVED the ceiling
    # to whatever the new fixture happened to use: `.prefix(9)` and `<= 100_000` then survived the whole
    # suite. These are caught by Int.max, .greatestFiniteMagnitude and a swept strip length instead.
    ("truncate the strip to the first NINE flags - the number the last fix moved the cap to", STRIP,
     "        return out.enumerated()\n"
     "            .sorted { ($0.element.severityRank, $0.offset) < ($1.element.severityRank, $1.offset) }\n"
     "            .map(\\.element)",
     "        return Array(out.enumerated()\n"
     "            .sorted { ($0.element.severityRank, $0.offset) < ($1.element.severityRank, $1.offset) }\n"
     "            .map(\\.element).prefix(9))"),

    ("no-cell stops firing above 100_000 minutes, the last fixture's own top value", STRIP,
     "        if facts.noCellMinutes >= noCellMinimumMinutes {",
     "        if facts.noCellMinutes >= noCellMinimumMinutes && facts.noCellMinutes <= 100_000 {"),

    ("the surface advisory stops firing above 1e300 km, far past any fixture but not past Double", STRIP,
     "        if facts.surfaceUnknownKm > surfaceUnknownMinimumKm {",
     "        if facts.surfaceUnknownKm > surfaceUnknownMinimumKm && facts.surfaceUnknownKm < 1e300 {"),

    # --- RouteFacts is Equatable BY HAND (a tuple array cannot be synthesised), so each half of the
    # closure comparison can be deleted on its own. Nothing in the repository compared two RouteFacts.
    ("delete the closure END TIME half of RouteFacts ==", STRIP,
     "                && a.closures.map(\\.source) == b.closures.map(\\.source)\n"
     "                && a.closures.map(\\.until) == b.closures.map(\\.until)",
     "                && a.closures.map(\\.source) == b.closures.map(\\.source)"),

    ("delete the closure SOURCE half of RouteFacts ==", STRIP,
     "                && a.closures.map(\\.source) == b.closures.map(\\.source)\n"
     "                && a.closures.map(\\.until) == b.closures.map(\\.until)",
     "                && a.closures.map(\\.until) == b.closures.map(\\.until)"),

    # Neither half can be deleted unnoticed any more, but either could be made ORDER-BLIND, which deletes
    # only the part of the comparison that a one-element fixture cannot see. The PR #80 reviewer's SG10.
    # The two are separate mutations because each is invisible to the other's fixture.
    ("compare closure SOURCES order-blind, so a reordered feed reads as the same route", STRIP,
     "                && a.closures.map(\\.source) == b.closures.map(\\.source)",
     "                && a.closures.map(\\.source).sorted() == b.closures.map(\\.source).sorted()"),

    ("compare closure END TIMES as a set, so a reordered feed reads as the same route", STRIP,
     "                && a.closures.map(\\.until) == b.closures.map(\\.until)",
     "                && Set(a.closures.map(\\.until)) == Set(b.closures.map(\\.until))"),
]

# Cannot change behaviour, so a catch here is a FAILURE.
#
# The second and third arrived as SURVIVORS in the PR #80 review, and the reviewer refused to bank them as
# findings - correctly. `flags(for:)` appends in groups of non-decreasing rank (closure 0, ford 1, gate 2,
# unrecognised 3, noCell 4, twilight 5, surface 6) and within a group every element shares a rank, so
# ordering by (rank, offset) is ordering by offset, which is the order `out` is already in. The sort is
# therefore the IDENTITY for every possible input: deleting it, or flattening the rank table to a
# constant, cannot change what comes out. Proved by differential dump over 15000 input combinations
# (.artifacts/equiv_check.py, three byte-identical dumps, md5 70f0d004) as well as by the argument.
# They live HERE, where a catch fails the run, because the only test that could "close" them is one that
# reads `severityRank` or the source text - the exact defect this repository keeps shipping.
# PRECONDITION: if the appends are ever reordered out of rank order, these two stop being equivalent and
# this list must be revisited. That is also why the unstable-sort mutation is in NEITHER list: Swift's
# `sorted(by:)` is not contractually stable, so a rank-only sort is equivalent by implementation accident
# rather than by argument, and neither arm can honestly hold it.
EQUIVALENT = [
    ("reorder two independent appends that cannot collide on rank", STRIP,
     "        if facts.hasFord { out.append(.ford) }\n        if facts.hasGate { out.append(.gate) }",
     "        if facts.hasGate { out.append(.gate) }\n        if facts.hasFord { out.append(.ford) }"),

    ("delete the sort; ship the append order, which is already rank order", STRIP,
     "        return out.enumerated()\n"
     "            .sorted { ($0.element.severityRank, $0.offset) < ($1.element.severityRank, $1.offset) }\n"
     "            .map(\\.element)",
     "        return out"),

    ("flatten every severityRank to 0", FLAG,
     "        case .closure:          return 0\n"
     "        case .ford:             return 1\n"
     "        case .gate:             return 2\n"
     "        case .unrecognised:     return 3\n"
     "        case .noCell:           return 4\n"
     "        case .twilightArrival:  return 5\n"
     "        case .surfaceUnknown:   return 6",
     "        case .closure:          return 0\n"
     "        case .ford:             return 0\n"
     "        case .gate:             return 0\n"
     "        case .unrecognised:     return 0\n"
     "        case .noCell:           return 0\n"
     "        case .twilightArrival:  return 0\n"
     "        case .surfaceUnknown:   return 0"),
]

# A NAMED test, spelled out. The second branch used to be `|Test run with .*failed`, the RUN-LEVEL summary,
# which fires for any failure anywhere in the package - precisely "a non-zero exit, summarised", which the
# docstring above promises this is not. Narrowed after the PR #80 review; the verdict is unchanged.
FAIL_LINE = re.compile(r'Test "[^"]*" recorded an issue')


def subject_test_files():
    """Every test file that mentions the subject, found by GREP rather than remembered."""
    return [f for f in sorted((ROOT / "Tests").rglob("*.swift"))
            if any(n in f.read_text(encoding="utf-8", errors="replace")
                   for n in ("Hazard", "RouteFacts"))]


def vacuity_gap():
    """Test files that could catch a mutation and that `--prove-vacuity` does NOT empty. Any such file
    makes the proof's "no tests present" premise false, so one refuses the run. The PR #80 review
    established the set by hand with one grep; a fact a harness depends on belongs in the harness."""
    return [f.relative_to(ROOT).as_posix() for f in subject_test_files() if f not in set(EMPTIED)]


def head_diff():
    """Subjects and test files that differ from `git show HEAD:<path>`, as (path, on-disk md5, HEAD md5).

    A mutation report is a claim about a COMMIT. The PR #80 reviewer planted a rounding change on
    HazardStrip.swift:96 - a line no anchor quotes, so nothing went stale - and this harness reported
    `pristine ... md5 d4ed91e8`, `BASELINE exit=0`, `caught by a named test: 21 of 21`, EXIT 0, then
    restored the mutant. It never consulted git. `capture_output` without `text=True` on purpose: bytes,
    so nothing translates a newline on this Windows box and turns every file into a false difference."""
    bad = []
    for f in HEAD_CHECKED:
        rel = f.relative_to(ROOT).as_posix()
        p = subprocess.run(["git", "show", "HEAD:" + rel], cwd=ROOT, capture_output=True)
        if p.returncode != 0:
            bad.append((rel, "on disk", "NOT IN HEAD (untracked, or renamed since the commit)"))
            continue
        disk = f.read_bytes()
        if disk != p.stdout:
            bad.append((rel, hashlib.md5(disk).hexdigest(), hashlib.md5(p.stdout).hexdigest()))
    return bad


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


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    if len(MUTATIONS) < MIN_MUTATIONS or len(EQUIVALENT) < MIN_EQUIVALENT:
        sys.stdout.write("REFUSING: %d mutations and %d equivalent mutants, expected at least %d and %d.\n"
                         "A harness that examines nothing exits 0 and proves nothing.\n"
                         % (len(MUTATIONS), len(EQUIVALENT), MIN_MUTATIONS, MIN_EQUIVALENT))
        return 2
    gap = vacuity_gap()
    if gap:
        sys.stdout.write("REFUSING: --prove-vacuity empties %s, but these test files also reference\n"
                         "the subject and could catch a mutation: %s\n"
                         % (", ".join(f.name for f in EMPTIED), ", ".join(gap)))
        return 2
    # BEFORE ANY BUILD. Everything printed below is a claim about HEAD, so a subject that is not HEAD makes
    # every line of it false - including the word "pristine" two lines down.
    drift = head_diff()
    if drift:
        sys.stdout.write("REFUSING: the subject on disk is not HEAD, so nothing measured here would be a\n"
                         "statement about the commit under review:\n")
        for rel, disk, head in drift:
            sys.stdout.write("  %-52s disk %s  HEAD %s\n" % (rel, disk, head))
        sys.stdout.write("Commit or stash first. There is no flag to skip this: a harness that measures a\n"
                         "mutated file and prints a clean sheet is the failure this check exists for.\n")
        return 2
    pristine = {f: f.read_bytes() for f in (STRIP, FLAG)}
    pristine_tests = {f: f.read_bytes() for f in EMPTIED}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s  (== git show HEAD:)\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: every test file that mentions the subject (%s)\n"
                             "is replaced by an empty suite, so every mutation must report MISSED - not\n"
                             "merely 'not caught'.\n" % ", ".join(f.name for f in EMPTIED))
            for f in EMPTIED:
                f.write_text(empty_suite(f), encoding="utf-8", newline="\n")

        # Retried, exactly as the mutation build is. A fresh scratch directory on this box fails once with
        # an I/O 512 symlink error often enough that a single try turned a healthy run into EXIT 2.
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
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        for f, b in pristine_tests.items():
            f.write_bytes(b)

    # Verified against HEAD, not against the bytes this process read off the same disk: comparing a restore
    # to a "pristine" snapshot that was already wrong proves only that the run was consistently wrong.
    left_behind = head_diff()
    if left_behind:
        sys.stdout.write("RESTORE FAILED - these files no longer match git show HEAD:\n")
        for rel, disk, head in left_behind:
            sys.stdout.write("  %-52s disk %s  HEAD %s\n" % (rel, disk, head))
        return 2

    sys.stdout.write("\nrestored to HEAD: "
                     + ", ".join(hashlib.md5(f.read_bytes()).hexdigest()[:8] for f in pristine) + "\n")
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

    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

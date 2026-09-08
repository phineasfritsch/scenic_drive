#!/usr/bin/env python3
"""Mutation harness for the safety gates. A catch requires a NAMED TEST to fail, not a non-zero exit.

The mutation that matters most in this file is `gate motorways too`. If the suite does not catch it, the
suite does not protect the invariant CLAUDE.md lists first - motorway and trunk are PENALISED, not excluded -
and this repository has already broken that once, making the flagship Mountain View -> SF fixture unroutable.

Second in importance is the absent-versus-present pair. Roughly half the mutations here turn a rule that
requires positive evidence into one that fires on a tag being absent or merely present, because that is how a
gate set quietly starts refusing most of the rural roads the product exists to find - and every short fixture
still passes when it does.

Written on the corrected contract (see ops/mutate/guidance.py, and T-0132):
  * the pass condition is `caught == len(MUTATIONS)`. A trap, a compile failure and a stale anchor each FAIL
    the run - `caught + len(trapped)` was the defect found on PR #70 today, where breaking a harness's own
    FAIL_LINE regex produced "caught: 0, trapped: 3" and exit 0;
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`, and empties EVERY test file that
    could catch a mutation, each with an empty suite named after the file it stands in;
  * the EQUIVALENT arm requires MISSED specifically, not merely "not caught".
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
GATES = ROOT / "Sources" / "ScenicKit" / "Gates" / "Gates.swift"
DECISION = ROOT / "Sources" / "ScenicKit" / "Gates" / "GateDecision.swift"
SCRATCH = ".build-mutate-gates"

# Every suite that could catch a mutation, not one hardcoded file. A suite split at the 300-line cap silently
# broke this in five separate harnesses today; filed as T-0132.
TEST_FILES = [ROOT / "Tests" / "ScenicKitTests" / "GatesTests.swift"]


def empty_suite(path: pathlib.Path) -> str:
    """An empty suite named after the file it replaces - two identically-named structs would not compile, and
    a compile failure would make the vacuity proof pass for the wrong reason."""
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))


MUTATIONS = [
    # --- THE INVARIANT ------------------------------------------------------------------------------------
    # If only one mutation in this file is caught, it has to be this one.
    ("gate motorways, the invariant CLAUDE.md lists first", GATES,
     "        return .allowed\n    }\n}",
     '        if tags["highway"] == "motorway" || tags["highway"] == "trunk" {\n'
     '            return .refused(.noAccess)\n'
     '        }\n        return .allowed\n    }\n}'),

    ("gate motorway_link and trunk_link, the shape a 'tidy-up' actually takes", GATES,
     "        return .allowed\n    }\n}",
     '        if tags["highway"]?.hasPrefix("motorway") == true\n'
     '            || tags["highway"]?.hasPrefix("trunk") == true {\n'
     '            return .refused(.noAccess)\n'
     '        }\n        return .allowed\n    }\n}'),

    # --- absent is not negative ---------------------------------------------------------------------------
    ("refuse a way with NO surface tag, which would exclude most rural lanes", GATES,
     '        if let surface = tags["surface"], unpavedSurfaces.contains(surface) {',
     '        if !unpavedSurfaces.contains(tags["surface"] ?? "") == false || tags["surface"] == nil {'),

    ("refuse any way that has a surface tag at all", GATES,
     '        if let surface = tags["surface"], unpavedSurfaces.contains(surface) {',
     '        if tags["surface"] != nil {'),

    ("refuse every gate, locked or not", GATES,
     '        if tags["barrier"] == "gate", tags["locked"] == "yes" { return .refused(.lockedBarrier) }',
     '        if tags["barrier"] == "gate" { return .refused(.lockedBarrier) }'),

    ("refuse a way tagged locked even with no barrier", GATES,
     '        if tags["barrier"] == "gate", tags["locked"] == "yes" { return .refused(.lockedBarrier) }',
     '        if tags["locked"] == "yes" { return .refused(.lockedBarrier) }'),

    ("refuse every service way, not only driveways and parking aisles", GATES,
     '        if tags["highway"] == "service", let s = tags["service"], refusedServiceValues.contains(s) {',
     '        if tags["highway"] == "service" {'),

    ("refuse a driveway value even on a road that is not a service way", GATES,
     '        if tags["highway"] == "service", let s = tags["service"], refusedServiceValues.contains(s) {',
     '        if let s = tags["service"], refusedServiceValues.contains(s) {'),

    ("refuse ford = no as well as ford = yes", GATES,
     '        if tags["ford"] == "yes" { return .refused(.ford) }',
     '        if tags["ford"] != nil { return .refused(.ford) }'),

    # --- the sets themselves ------------------------------------------------------------------------------
    ("drop compacted and fine_gravel from the unpaved set", GATES,
     '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",',
     '        "gravel", "dirt", "ground", "sand", "unpaved",'),

    ("call asphalt unpaved", GATES,
     '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel",',
     '        "gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel", "asphalt",'),

    ("let destination-only access through", GATES,
     '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination"]',
     '    public static let closedAccess: Set<String> = ["private", "no", "permit"]'),

    ("refuse permissive access", GATES,
     '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination"]',
     '    public static let closedAccess: Set<String> = ["private", "no", "permit", "destination",\n'
     '                                                   "permissive"]'),

    ("move the tracktype boundary, letting grade3 through", GATES,
     '    public static let refusedTracktypes: Set<String> = ["grade3", "grade4", "grade5"]',
     '    public static let refusedTracktypes: Set<String> = ["grade4", "grade5"]'),

    ("move the tracktype boundary the other way, refusing grade2", GATES,
     '    public static let refusedTracktypes: Set<String> = ["grade3", "grade4", "grade5"]',
     '    public static let refusedTracktypes: Set<String> = ["grade2", "grade3", "grade4", "grade5"]'),

    ("refuse intermediate smoothness, which the plan allows", GATES,
     '        "bad", "very_bad", "horrible", "very_horrible", "impassable",',
     '        "intermediate", "bad", "very_bad", "horrible", "very_horrible", "impassable",'),

    ("let a merely bad road through", GATES,
     '        "bad", "very_bad", "horrible", "very_horrible", "impassable",',
     '        "very_bad", "horrible", "very_horrible", "impassable",'),

    # --- the reason, which the autopsy reads --------------------------------------------------------------
    ("report an unpaved surface as a locked barrier", GATES,
     "            return .refused(.unpavedSurface)",
     "            return .refused(.lockedBarrier)"),

    ("report a ford as rough surface", GATES,
     '        if tags["ford"] == "yes" { return .refused(.ford) }',
     '        if tags["ford"] == "yes" { return .refused(.tooRough) }'),

    ("a refusal reports itself as allowed", DECISION,
     "    public var isAllowed: Bool {\n        if case .allowed = self { return true }\n        return false",
     "    public var isAllowed: Bool {\n        return true"),

    ("an allowed way reports a reason anyway", DECISION,
     "    public var reason: GateReason? {\n        if case let .refused(r) = self { return r }\n"
     "        return nil",
     "    public var reason: GateReason? {\n        if case let .refused(r) = self { return r }\n"
     "        return .ford"),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE.
EQUIVALENT = [
    ("reorder two independent rules that cannot both fire", GATES,
     '        if tags["ford"] == "yes" { return .refused(.ford) }',
     '        if tags["ford"] == "yes" { return .refused(GateReason.ford) }'),
]

# Mutations this suite is KNOWN not to catch, asserted the other way round. Empty for now, and that is a
# claim: every mutation above is expected to be caught by a named test.
KNOWN_MISSED = []

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


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = {f: f.read_bytes() for f in (GATES, DECISION)}
    pristine_tests = {f: f.read_bytes() for f in TEST_FILES}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
    known = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: EVERY test file is replaced by an empty suite, so every\n"
                             "mutation must report MISSED - not merely 'not caught'.\n")
            for f in TEST_FILES:
                f.write_text(empty_suite(f), encoding="utf-8", newline="\n")

        # Built TWICE before the baseline is declared broken, for the same reason each mutation is. On this
        # Windows checkout a first build into a fresh scratch directory can fail with "unable to create
        # symbolic link ... I/O error (code: 512)" and succeed immediately after. The mutation loop already
        # allowed for that; the baseline did not, so a transient failure aborted the whole run with
        # "baseline does not build" and nothing was ever measured. That happened on this harness's first run.
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

    known_ok = not KNOWN_MISSED or (
        known is not None and len(known["missed"]) + len(known["trapped"]) == len(KNOWN_MISSED))
    if not known_ok and known is not None:
        sys.stdout.write("KNOWN-GAP ARM FAILED: a gap that closed is good news - move it into MUTATIONS.\n")
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok and known_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

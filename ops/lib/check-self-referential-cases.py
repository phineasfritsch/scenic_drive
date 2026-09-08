"""RED demonstration for check-self-referential-tests, on the real instances it exists to catch.

Every case below is copied from an assertion that actually shipped in this repository and was found by a
reviewer, not invented to make the check look good. Each is written into a throwaway test file, the check is
run, and it must fire. Then a set of NEGATIVE cases - assertions that look similar and are legitimate - must
NOT fire, because a check that flags every comparison is a check people turn off.

Run: python ops/lib/check-self-referential-cases.py
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECK = ROOT / "ops" / "lib" / "check-self-referential-tests.py"

# Floors on the SUITE, not on the tree. Deleting cases until a change looks green is the cheapest way to
# make this check stop objecting, and it leaves no trace: the OK line just says a smaller number.
MIN_RED_CASES = 8
MIN_GREEN_CASES = 6

# Enough types and files to clear the check's own vacuity floors.
SCAFFOLD_SOURCES = {
    "LearnedCorridorSpeeds.swift":
        "public struct LearnedCorridorSpeeds {\n"
        "    public static let maxRatio = 1.0\n"
        "    public static let confidenceThreshold = 5\n"
        "}\n",
    "LambdaSearch.swift":
        "public struct LambdaSearch {\n    public static let maxLambda = 8.0\n}\n",
    "RetraceDetector.swift":
        "public enum RetraceDetector {\n    public static let cellSizeMeters = 25.0\n}\n",
    "AppleMapsDirections.swift":
        "public struct AppleMapsDirections {\n    public static let maxWaypoints = 9\n}\n",
    # Geo must be DECLARED here or the metamorphic-symmetry negative case is vacuous: rule A only looks at
    # members of types under Sources/, so without this the function-call lookahead is never reached and the
    # case is green whether the lookahead exists or not. A reviewer proved that by deleting the lookahead
    # and watching nothing change.
    "Geo.swift":
        "public enum Geo {\n    public static let earthRadiusMeters = 6_371_008.8\n"
        "    public static func distanceMeters(_ a: Double, _ b: Double) -> Double { 0 }\n}\n",
}

# Real assertions, not comment lines. The check floors on assertions EXAMINED - a reviewer showed that
# counting files PRESENT let three files containing no assertions clear the gate, and pointed out that two
# of this scaffold's own three files were a single comment line. So the scaffold has to carry a real
# population. Every one of these is a legitimate literal comparison that must never fire, which keeps the
# case's own line the only variable in the run.
_PAD_ASSERTIONS = "\n".join("        #expect(value%d == %d)" % (i, i) for i in range(1, 13))

SCAFFOLD_TESTS = {
    "PadOne.swift":
        'import Testing\n@Suite("pad one") struct PadOneSuite {\n'
        '    @Test("pad") func pad() {\n' + _PAD_ASSERTIONS + "\n    }\n}\n",
    "PadTwo.swift":
        'import Testing\n@Suite("pad two") struct PadTwoSuite {\n'
        '    @Test("pad") func pad() {\n' + _PAD_ASSERTIONS + "\n    }\n}\n",
}

# (name, the line, must_fire, expected_substring_when_firing)
#
# The substring is not decoration. `fired = code == 1` alone treats a TRACEBACK as a successful catch: a
# reviewer replaced the matcher body with `raise` and every RED case reported `ok`. A red case must show
# that the check found the thing, not merely that it exited non-zero.
CASES = [
    # --- real instances, verbatim in shape ------------------------------------------------------------
    ("T-0118: a clamp asserted against its own constant",
     "        #expect(r2 <= LearnedCorridorSpeeds.maxRatio)", True,
     "LearnedCorridorSpeeds.maxRatio"),

    ("T-0118: a loop bound taken from the constant under test",
     "        for n in 1..<LearnedCorridorSpeeds.confidenceThreshold {", True,
     "range bound taken from the constant"),

    ("T-0116: both sides of one object",
     "        #expect(out.duration <= out.ceiling)", True,
     "out.duration vs out.ceiling"),

    ("T-0114: a cap asserted through its own symbol",
     "        #expect(pinned.count == AppleMapsDirections.maxWaypoints)", True,
     "AppleMapsDirections.maxWaypoints"),

    ("a constant on the left, a computed value on the right",
     "        #expect(LambdaSearch.maxLambda > measured)", True,
     "LambdaSearch.maxLambda"),

    ("a range built from the constant, closed form",
     "        for i in 0...RetraceDetector.cellSizeMeters {", True,
     "RetraceDetector.cellSizeMeters"),

    # --- negatives: legitimate assertions that must NOT fire -------------------------------------------
    ("pinning a constant against a literal, which is the CORRECT shape",
     "        #expect(LearnedCorridorSpeeds.maxRatio == 1.0)", False, None),

    ("a metamorphic symmetry property over two invocations",
     "        #expect(Geo.distanceMeters(a, b) == Geo.distanceMeters(b, a))", False, None),

    ("a value compared against a literal",
     "        #expect(out.duration <= 3300.0)", False, None),

    ("two different receivers, which this check deliberately does not cover",
     "        #expect(pieces.p90 == whole.p90)", False, None),

    ("an allowlisted line with a stated reason",
     "        #expect(r2 <= LearnedCorridorSpeeds.maxRatio)  "
     "// self-ref-ok: the clamp value is pinned separately by constantsArePinned", False, None),

    ("a constant mentioned in a comment only",
     "        // #expect(r2 <= LearnedCorridorSpeeds.maxRatio)", False, None),

    # --- the escape hatch, which promised more than it enforced ---------------------------------------
    ("a one-word reason does NOT silence the check",
     "        #expect(r2 <= LearnedCorridorSpeeds.maxRatio)  // self-ref-ok: later", True,
     "LearnedCorridorSpeeds.maxRatio"),

    ("a marker with no reason at all does NOT silence the check",
     "        #expect(r2 <= LearnedCorridorSpeeds.maxRatio)  // self-ref-ok:", True,
     "LearnedCorridorSpeeds.maxRatio"),

    ("a marker inside a Swift string does NOT silence the check",
     '        #expect(name == LearnedCorridorSpeeds.maxRatio)  '
     '// note: write \\"// self-ref-ok: because reasons\\" to suppress', True,
     "LearnedCorridorSpeeds.maxRatio"),

    # --- literal forms the remedy text itself recommends ----------------------------------------------
    ("a constant pinned against a leading-dot float is the CORRECT shape",
     "        #expect(LambdaSearch.maxLambda == .5)", False, None),

    ("a constant pinned against .infinity is the CORRECT shape",
     "        #expect(LambdaSearch.maxLambda == .infinity)", False, None),

    ("a constant pinned against an array literal is the CORRECT shape",
     '        #expect(LambdaSearch.codes == ["a", "b"])', False, None),

    ("a constant pinned against a negative float is the CORRECT shape",
     "        #expect(LambdaSearch.maxLambda == -1.5)", False, None),

    # reviewer-pr77's finding 4: the RHS is read as the rest of the line, so a trailing message argument was
    # captured with the value and failed the literal test. This fired on the REAL tree - on
    # `Geo.earthRadiusMeters == 6_371_008.8, "WGS84 mean radius"` - taking P-TEST-02 red on correct code
    # written in the style 7 of the 31 existing assertions use.
    ("the CORRECT shape with a trailing message argument",
     "        #expect(Geo.earthRadiusMeters == 6_371_008.8, \"WGS84 mean radius\")", False, None),

    ("the CORRECT shape with a message argument that itself contains a comma",
     "        #expect(LambdaSearch.maxLambda == 8.0, \"the ceiling, not a target\")", False, None),

    # reviewer-pr77's finding 1: MEMBER carries `(?!\s*\()` so that a CALL is not mistaken for a constant.
    # Nothing exercised it. The shape that does is a call on the RIGHT-hand side - with the lookahead
    # deleted this line is reported, with it present it is silent - so this case is what pins the lookahead.
    # The previously-claimed case did not: it passed either way.
    ("a call on the right-hand side is not a constant",
     "        #expect(x <= Geo.distanceMeters(a, b))", False, None),
]


def run_case(line: str) -> tuple[int, str]:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="selfref-"))
    try:
        (tmp / "ops" / "lib").mkdir(parents=True)
        (tmp / "Sources" / "Probe").mkdir(parents=True)
        (tmp / "Tests" / "ProbeTests").mkdir(parents=True)
        shutil.copy(CHECK, tmp / "ops" / "lib" / CHECK.name)
        for name, body in SCAFFOLD_SOURCES.items():
            (tmp / "Sources" / "Probe" / name).write_text(body, encoding="utf-8", newline="\n")
        for name, body in SCAFFOLD_TESTS.items():
            (tmp / "Tests" / "ProbeTests" / name).write_text(body, encoding="utf-8", newline="\n")
        (tmp / "Tests" / "ProbeTests" / "Case.swift").write_text(
            "import Testing\n@testable import Probe\n\n@Suite(\"probe\") struct ProbeSuite {\n"
            "    @Test(\"probe\") func probe() {\n" + line + "\n    }\n}\n",
            encoding="utf-8", newline="\n")
        p = subprocess.run([sys.executable, str(tmp / "ops" / "lib" / CHECK.name)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ok = True

    # A suite over no cases is not a suite. `CASES = []` printed "SELF-REF CASES OK (0 cases)" and exited 0,
    # and so did a suite with only negatives - the sibling check-self-referential-history.py has had exactly
    # this guard ("a demonstration over nothing is not a demonstration") since it was written; this file did
    # not. Both directions are required: greens alone cannot show the matcher fires, reds alone cannot show
    # it ever stays quiet.
    reds = sum(1 for _, _, must_fire, _ in CASES if must_fire)
    greens = len(CASES) - reds
    if reds < MIN_RED_CASES or greens < MIN_GREEN_CASES:
        sys.stdout.write("SELF-REF CASES FAIL: %d red and %d green cases, expected at least %d and %d - "
                         "a demonstration over nothing is not a demonstration\n"
                         % (reds, greens, MIN_RED_CASES, MIN_GREEN_CASES))
        return 2

    for name, line, must_fire, expect_text in CASES:
        code, out = run_case(line)
        # A finding, not merely a non-zero exit. A traceback is also exit 1, and treating that as a catch
        # made every RED case pass against a matcher replaced by `raise`.
        #
        # The same reasoning applies to the GREEN half and was missing: `fired = False` is what a negative
        # case wants, and a matcher that raises on every input produces exactly that - so nine of nineteen
        # cases passed against a matcher replaced by `raise`, and the suite exited 0. A negative case must
        # therefore show the check RAN and was SILENT: exit 0 with its own OK line, not merely "did not fire".
        fired = code == 1 and "SELF-REF FAIL" in out
        if not must_fire and not (code == 0 and "SELF-REF OK" in out):
            ok = False
            sys.stdout.write("FAIL   green  %s\n         did not fire, but the check did not report OK "
                             "either (exit %d) - a crash is not a clean pass\n" % (name, code))
            for l in out.strip().splitlines()[:3]:
                sys.stdout.write("         %s\n" % l)
            continue
        if fired and expect_text and expect_text not in out:
            ok = False
            sys.stdout.write("FAIL   TEXT   %s\n         fired, but did not report %r\n"
                             % (name, expect_text))
            continue
        if code == 2:
            sys.stdout.write("SCAFFOLD FAIL %-58s %s\n" % (name, out.strip().splitlines()[:1]))
            ok = False
            continue
        if fired == must_fire:
            sys.stdout.write("ok     %-6s %s\n" % ("RED" if must_fire else "green", name))
        else:
            ok = False
            sys.stdout.write("FAIL   %-6s %s\n         expected %s, got exit %d\n"
                             % ("RED" if must_fire else "green", name,
                                "a finding" if must_fire else "no finding", code))
            for l in out.strip().splitlines()[:3]:
                sys.stdout.write("         %s\n" % l)

    # The floors, seen red rather than asserted in prose.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="selfref-empty-"))
    try:
        (tmp / "ops" / "lib").mkdir(parents=True)
        (tmp / "Sources").mkdir()
        (tmp / "Tests").mkdir()
        shutil.copy(CHECK, tmp / "ops" / "lib" / CHECK.name)
        p = subprocess.run([sys.executable, str(tmp / "ops" / "lib" / CHECK.name)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode == 2 and "examines nothing" in p.stdout:
            sys.stdout.write("ok     FLOOR  an empty tree refuses instead of passing\n")
        else:
            ok = False
            sys.stdout.write("FAIL   FLOOR  an empty tree gave exit %d: %s\n"
                             % (p.returncode, p.stdout.strip()[:100]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    sys.stdout.write("\nSELF-REF CASES %s (%d cases)\n" % ("OK" if ok else "FAIL", len(CASES)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

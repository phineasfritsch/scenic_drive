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
}

SCAFFOLD_TESTS = {
    "PadOne.swift": "// keeps the file count above the floor\n",
    "PadTwo.swift": "// keeps the file count above the floor\n",
}

# (name, the line, must_fire)
CASES = [
    # --- real instances, verbatim in shape ------------------------------------------------------------
    ("T-0118: a clamp asserted against its own constant",
     "        #expect(r2 <= LearnedCorridorSpeeds.maxRatio)", True),

    ("T-0118: a loop bound taken from the constant under test",
     "        for n in 1..<LearnedCorridorSpeeds.confidenceThreshold {", True),

    ("T-0116: both sides of one object",
     "        #expect(out.duration <= out.ceiling)", True),

    ("T-0114: a cap asserted through its own symbol",
     "        #expect(pinned.count == AppleMapsDirections.maxWaypoints)", True),

    ("a constant on the left, a computed value on the right",
     "        #expect(LambdaSearch.maxLambda > measured)", True),

    ("a range built from the constant, closed form",
     "        for i in 0...RetraceDetector.cellSizeMeters {", True),

    # --- negatives: legitimate assertions that must NOT fire -------------------------------------------
    ("pinning a constant against a literal, which is the CORRECT shape",
     "        #expect(LearnedCorridorSpeeds.maxRatio == 1.0)", False),

    ("a metamorphic symmetry property over two invocations",
     "        #expect(Geo.distanceMeters(a, b) == Geo.distanceMeters(b, a))", False),

    ("a value compared against a literal",
     "        #expect(out.duration <= 3300.0)", False),

    ("two different receivers, which this check deliberately does not cover",
     "        #expect(pieces.p90 == whole.p90)", False),

    ("an allowlisted line with a stated reason",
     "        #expect(r2 <= LearnedCorridorSpeeds.maxRatio)  "
     "// self-ref-ok: the clamp value is pinned separately by constantsArePinned", False),

    ("a constant mentioned in a comment only",
     "        // #expect(r2 <= LearnedCorridorSpeeds.maxRatio)", False),
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
    for name, line, must_fire in CASES:
        code, out = run_case(line)
        fired = code == 1
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

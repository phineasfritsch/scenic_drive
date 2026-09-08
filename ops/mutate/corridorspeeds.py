"""Mutation harness for LearnedCorridorSpeeds. A catch requires a NAMED TEST to fail, not a non-zero exit.

Tracked in ops/ rather than .artifacts/, because .artifacts/ is gitignored and a task whose `acceptance:`
line names a file nobody else can run has no reproducible red evidence. Each mutation is built first: a
mutation that does not compile is reported `compile-only` and does not count, since a compiler error is a
fact about Swift and not about this suite.

Run `--prove-vacuity` to check the harness itself: it replaces the test file with an empty suite and
requires every mutation to report MISSED. A harness that still reports catches with no tests present is
measuring the compiler.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "ScenicKit" / "Traffic" / "LearnedCorridorSpeeds.swift"
KEY = ROOT / "Sources" / "ScenicKit" / "Traffic" / "CorridorKey.swift"
TESTS = ROOT / "Tests" / "ScenicKitTests" / "LearnedCorridorSpeedsTests.swift"
SCRATCH = ".build-mutate-corridorspeeds"

EMPTY_SUITE = ('import Testing\n'
               '@Suite("empty") struct EmptyCorridorSuite {\n'
               '    @Test("nothing") func nothing() { #expect(true) }\n'
               '}\n')

# (name, file, old, new)
MUTATIONS = [
    # --- the two product invariants ------------------------------------------------------------------
    ("default the ratio to 1.0 instead of admitting we do not know", SRC,
     "        guard isConfident(about: key), let r = ratios[key] else { return nil }\n        return r",
     "        guard let r = ratios[key] else { return 1.0 }\n        return r"),

    ("always claim the ETA is learned", SRC,
     "guard freeFlow.isFinite, freeFlow > 0, let r = ratio(for: key) else { return (freeFlow, false) }",
     "guard freeFlow.isFinite, freeFlow > 0, let r = ratio(for: key) else { return (freeFlow, true) }"),

    ("drop the badge after one sample", SRC,
     "public static let confidenceThreshold = 5",
     "public static let confidenceThreshold = 1"),

    ("raise the badge threshold to twenty, so it never clears", SRC,
     "public static let confidenceThreshold = 5",
     "public static let confidenceThreshold = 20"),

    ("add Codable to the key so it can be logged", KEY,
     "public struct CorridorKey: Hashable, Sendable {",
     "public struct CorridorKey: Hashable, Sendable, Codable {"),

    # --- the clamp. maxRatio had NO real test: a reviewer moved it to 3.0 and the suite stayed green,
    # --- after which a learned corridor returned an ETA below the free-flow it was handed, badge on.
    ("let a corridor be learned as three times faster than free flow", SRC,
     "public static let maxRatio = 1.0",
     "public static let maxRatio = 3.0"),

    ("drop the congestion floor to nothing", SRC,
     "public static let minRatio = 0.3",
     "public static let minRatio = 0.001"),

    ("stop clamping the ratio at all", SRC,
     "let sample = min(Self.maxRatio, max(Self.minRatio, raw))",
     "let sample = raw"),

    ("clamp to the wrong ends, swapping the floor and the ceiling", SRC,
     "let sample = min(Self.maxRatio, max(Self.minRatio, raw))",
     "let sample = max(Self.maxRatio, min(Self.minRatio, raw))"),

    # --- the learning --------------------------------------------------------------------------------
    ("accept any sample the caller offers", SRC,
     "guard actual.isFinite, freeFlow.isFinite, actual > 0, freeFlow > 0 else { return false }",
     "// guard removed"),

    ("count a rejected sample toward confidence", SRC,
     "        guard actual.isFinite, freeFlow.isFinite, actual > 0, freeFlow > 0 else { return false }",
     "        counts[key] = (counts[key] ?? 0) + 1\n"
     "        guard actual.isFinite, freeFlow.isFinite, actual > 0, freeFlow > 0 else { return false }"),

    ("let the second sample replace the first instead of blending with it", SRC,
     "        if n == 0 {",
     "        if n <= 1 {"),

    ("blend the first sample against an assumed 1.0", SRC,
     "        if n == 0 {\n            ratios[key] = sample\n        } else {\n"
     "            ratios[key] = Self.smoothing * sample + (1 - Self.smoothing) * (ratios[key] ?? sample)\n"
     "        }",
     "        ratios[key] = Self.smoothing * sample + (1 - Self.smoothing) * (ratios[key] ?? 1.0)"),

    ("invert the smoothing, so the newest drive is 70 percent of the estimate", SRC,
     "public static let smoothing = 0.3",
     "public static let smoothing = 0.7"),

    ("take the ratio the other way up, so congestion reads as speed", SRC,
     "        let raw = freeFlow / actual",
     "        let raw = actual / freeFlow"),

    # --- the key -------------------------------------------------------------------------------------
    ("bucket the week from the calendar's first weekday", KEY,
     "let mondayBased = (weekday + 5) % 7",
     "let mondayBased = weekday - 1"),

    ("bucket by hour of the DAY, losing the difference between Tuesday and Sunday", KEY,
     "self.init(cell: cell, hourOfWeek: mondayBased * 24 + hour)",
     "self.init(cell: cell, hourOfWeek: hour)"),

    ("accept an hour outside the week", KEY,
     "guard (0..<168).contains(hourOfWeek) else { return nil }",
     "guard hourOfWeek >= -1000 else { return nil }"),
]


FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def build():
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(pristine):
    caught, compile_only, missed, trapped = 0, [], [], []
    for name, path, old, new in MUTATIONS:
        text = pristine[path].decode('utf-8')
        if old not in text:
            sys.stdout.write("SKIP        %-56s anchor not found - harness stale\n" % name)
            missed.append(name)
            continue
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if path.read_bytes() == pristine[path]:
                sys.stdout.write("SKIP        %-56s mutation did not land\n" % name)
                missed.append(name)
                continue
            # Build twice before believing a compile failure. Other agents run swift builds on this box
            # concurrently and a transient scratch-directory collision produced a false compile-only
            # verdict for a mutation that compiles fine - checked by hand, exit 0.
            if build() != 0 and build() != 0:
                verdict, code = "compile-only", 1
            else:
                code, out = test()
                if FAIL_LINE.search(out):
                    verdict = "caught"
                elif code != 0:
                    # Non-zero with no named failure means the test process died - a Swift trap. The suite
                    # DID detect the mutation (a test drove the code into it), but not through an assertion,
                    # so it is reported separately rather than counted as a named-test catch. Calling a crash
                    # a passing check would be the kind of flattery this harness exists to avoid.
                    verdict = "trapped"
                else:
                    verdict = "MISSED"
        finally:
            path.write_bytes(pristine[path])

        if verdict == "caught":
            caught += 1
            sys.stdout.write("caught      %-56s exit=%d\n" % (name, code))
        elif verdict == "trapped":
            trapped.append(name)
            sys.stdout.write("trapped     %-56s the code trapped; no assertion fired\n" % name)
        elif verdict == "compile-only":
            compile_only.append(name)
            sys.stdout.write("%-11s %-56s NOT a test catch\n" % (verdict, name))
        else:
            missed.append(name)
            sys.stdout.write("MISSED      %-56s exit=0  no test objected\n" % name)
    return caught, compile_only, missed, trapped


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = {f: f.read_bytes() for f in (SRC, KEY)}
    pristine_tests = TESTS.read_bytes()
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: replacing the test file with an empty suite.\n"
                             "Every mutation must now report MISSED; a catch here would mean the harness is\n"
                             "measuring the Swift compiler rather than these tests.\n")
            TESTS.write_text(EMPTY_SUITE, encoding="utf-8", newline="\n")

        if build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _ = test()
        sys.stdout.write("BASELINE                                                      exit=%d\n" % code)
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2

        caught, compile_only, missed, trapped = run_all(pristine)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        TESTS.write_bytes(pristine_tests)

    if any(f.read_bytes() != b for f, b in pristine.items()) or TESTS.read_bytes() != pristine_tests:
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2
    sys.stdout.write("\nrestored, md5 %s\n" % hashlib.md5(SRC.read_bytes()).hexdigest())
    sys.stdout.write("caught by a named test: %d   trapped: %d   compile-only: %d   MISSED: %d   of %d\n"
                     % (caught, len(trapped), len(compile_only), len(missed), len(MUTATIONS)))
    for n in trapped:
        sys.stdout.write("  trapped (detected, but by a crash and not an assertion): %s\n" % n)
    for n in compile_only:
        sys.stdout.write("  compile-only: %s\n" % n)
    for n in missed:
        sys.stdout.write("  MISSED: %s\n" % n)

    if prove:
        ok = caught == 0
        sys.stdout.write("VACUITY PROOF %s: with no tests present, %d mutations were reported caught\n"
                         % ("OK" if ok else "FAILED", caught))
        return 0 if ok else 1
    return 0 if caught + len(trapped) == len(MUTATIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

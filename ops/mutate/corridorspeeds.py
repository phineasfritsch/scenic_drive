"""Mutation harness for LearnedCorridorSpeeds and CorridorKey. A catch requires a NAMED TEST to fail.

Each mutation is applied to a pristine tree, built, run, and reverted. A mutation that does not compile is
reported `compile-only` and does not count: a compiler error is a fact about Swift, not about this suite.

## The exit code, which used to lie

This file shipped as

    return 0 if caught + len(trapped) == len(MUTATIONS) else 1

while its own docstring said a trap is NOT a catch. The reviewer of PR #75 handed the harness a single
trapping mutation (`counts[key] ?? 0` -> `counts[key]!`) with the subject otherwise pristine; it printed
"caught by a named test: 0   trapped: 1" and returned EXIT 0. So the pass condition is now
`caught == len(MUTATIONS)`, full stop, matching ops/mutate/guidance.py. Four consequences, all deliberate:

  * A trap is a real detection but not by a check, so it does not count. If a mutation only ever traps,
    either the test that should have caught it is missing or the mutation is a poor one - both need a person.
  * SKIP is its own bucket and fails the run. A mutation whose anchor has moved means the harness is stale,
    which is the opposite of what MISSED means; folding it into MISSED hides a dead check as a known gap.
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`. Requiring only `caught == 0`
    would also be satisfied by a harness broken in the compile-only direction.
  * The EQUIVALENT arm requires its mutants to go MISSED specifically, not merely "not caught". A mutation
    that changes no behaviour must be invisible to the suite; a catch there means a test has an opinion about
    how the code is WRITTEN rather than what it DOES.

Both test files are blanked during the vacuity proof. Splitting the key tests into their own file and
blanking only one of them would have let the surviving file "prove" the other's non-vacuity.
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
SPEED_TESTS = ROOT / "Tests" / "ScenicKitTests" / "LearnedCorridorSpeedsTests.swift"
KEY_TESTS = ROOT / "Tests" / "ScenicKitTests" / "CorridorKeyTests.swift"
# Inside .build/ so `.gitignore`'s `.build/` covers it. `.build-mutate-corridorspeeds/` did not match that
# pattern, so the command named in the task's `acceptance:` line left an untracked directory behind.
SCRATCH = ".build/mutate-corridorspeeds"

EMPTY_SUITES = {
    SPEED_TESTS: ('import Testing\n'
                  '@Suite("empty") struct EmptyCorridorSuite {\n'
                  '    @Test("nothing") func nothing() { #expect(true) }\n'
                  '}\n'),
    KEY_TESTS: ('import Testing\n'
                '@Suite("empty key") struct EmptyCorridorKeySuite {\n'
                '    @Test("nothing") func nothing() { #expect(true) }\n'
                '}\n'),
}

HAND_WRITTEN_HASHABLE = ("public struct CorridorKey: Hashable, Sendable {\n"
                         "    public static func == (a: CorridorKey, b: CorridorKey) -> Bool {\n"
                         "        a.hourOfWeek == b.hourOfWeek\n"
                         "    }\n"
                         "    public func hash(into h: inout Hasher) { h.combine(hourOfWeek) }\n")

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

    ("report an accepted sample as rejected", SRC,
     "        counts[key] = n + 1\n        return true",
     "        counts[key] = n + 1\n        return false"),

    ("let the second sample replace the first instead of blending with it", SRC,
     "        if n == 0 {",
     "        if n <= 1 {"),

    ("blend the first sample against an assumed 1.0", SRC,
     "        if n == 0 {\n            ratios[key] = sample\n        } else {\n"
     "            ratios[key] = Self.smoothing * sample + (1 - Self.smoothing) * (ratios[key] ?? sample)\n"
     "        }",
     "        ratios[key] = Self.smoothing * sample + (1 - Self.smoothing) * (ratios[key] ?? 1.0)"),

    ("take the ratio the other way up, so congestion reads as speed", SRC,
     "        let raw = freeFlow / actual",
     "        let raw = actual / freeFlow"),

    # --- smoothing. It was pinned from above (0.7) and at exactly 0.0 and nowhere else, so the model could
    # --- be made INERT - green suite, 31-minute ETA for a 90-minute drive - by lowering it.
    ("invert the smoothing, so the newest drive is 70 percent of the estimate", SRC,
     "public static let smoothing = 0.3",
     "public static let smoothing = 0.7"),

    ("nudge the smoothing up to 0.4, inside the outlier test's tolerance", SRC,
     "public static let smoothing = 0.3",
     "public static let smoothing = 0.4"),

    ("halve the smoothing to 0.15, so the model learns at half speed", SRC,
     "public static let smoothing = 0.3",
     "public static let smoothing = 0.15"),

    ("smother the smoothing to 0.001, so the model is inert but green", SRC,
     "public static let smoothing = 0.3",
     "public static let smoothing = 0.001"),

    # --- the key: WHEN -------------------------------------------------------------------------------
    ("bucket the week from the calendar's first weekday", KEY,
     "let mondayBased = (weekday + 5) % 7",
     "let mondayBased = weekday - 1"),

    ("bucket by hour of the DAY, losing the difference between Tuesday and Sunday", KEY,
     "self.init(cell: cell, hourOfWeek: mondayBased * 24 + hour)",
     "self.init(cell: cell, hourOfWeek: hour)"),

    ("accept an hour outside the week", KEY,
     "guard (0..<168).contains(hourOfWeek) else { return nil }",
     "guard hourOfWeek >= -1000 else { return nil }"),

    ("read the bucket in UTC instead of the calendar's own time zone", KEY,
     "        let c = calendar.dateComponents([.weekday, .hour], from: date)",
     "        var cal = calendar\n"
     "        cal.timeZone = TimeZone(identifier: \"UTC\")!\n"
     "        let c = cal.dateComponents([.weekday, .hour], from: date)"),

    # --- the key: WHERE. Every store-level test used one cell, so the whole `cell` half was unpinned.
    ("hand-write Hashable so it forgets the cell and only two hours can collide", KEY,
     "public struct CorridorKey: Hashable, Sendable {\n",
     HAND_WRITTEN_HASHABLE),

    ("truncate the cell id to sixteen bits on the way in", KEY,
     "        self.cell = cell\n",
     "        self.cell = cell & 0xFFFF\n"),

    # --- adjust()'s own guard. `record` has six parameterised cases for this input class; `adjust` had none.
    ("drop adjust's free-flow guard entirely", SRC,
     "guard freeFlow.isFinite, freeFlow > 0, let r = ratio(for: key) else { return (freeFlow, false) }",
     "guard let r = ratio(for: key) else { return (freeFlow, false) }"),

    ("weaken adjust's guard to finiteness, letting zero and negative durations through", SRC,
     "guard freeFlow.isFinite, freeFlow > 0, let r = ratio(for: key) else { return (freeFlow, false) }",
     "guard freeFlow.isFinite, let r = ratio(for: key) else { return (freeFlow, false) }"),
]

# Mutants that cannot change behaviour. Anything but MISSED here means a test is asserting how the code is
# written rather than what it does.
EQUIVALENT = [
    ("reorder record's four independent guard conditions", SRC,
     "guard actual.isFinite, freeFlow.isFinite, actual > 0, freeFlow > 0 else { return false }",
     "guard freeFlow.isFinite, actual.isFinite, freeFlow > 0, actual > 0 else { return false }"),

    ("state isConfident's comparison the other way round", SRC,
     "        sampleCount(for: key) >= Self.confidenceThreshold",
     "        Self.confidenceThreshold <= sampleCount(for: key)"),
]

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
    """One verdict per mutation. SKIP is its own bucket, never folded into MISSED: a mutation that did not
    land says the harness is stale, which is the opposite of what MISSED means."""
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    for name, path, old, new in mutations:
        text = pristine[path].decode("utf-8")
        if old not in text:
            sys.stdout.write("SKIP        %-62s anchor not found - the harness is stale\n" % name)
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
        label = {"caught": "caught", "trapped": "trapped", "compile_only": "compile-only",
                 "missed": "MISSED"}
        note = {"caught": "exit=%d" % code,
                "trapped": "non-zero exit, but NO named test failed - does not count",
                "compile_only": "a fact about Swift, not about these tests - does not count",
                "missed": "exit=0  no test objected"}
        sys.stdout.write("%-12s%-62s %s\n" % (label[verdict], name, note[verdict]))
    return out


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = {f: f.read_bytes() for f in (SRC, KEY)}
    pristine_tests = {f: f.read_bytes() for f in (SPEED_TESTS, KEY_TESTS)}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: BOTH test files are replaced by empty suites, so every\n"
                             "mutation must report MISSED - not merely 'not caught'.\n")
            for f, empty in EMPTY_SUITES.items():
                f.write_text(empty, encoding="utf-8", newline="\n")

        if build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _ = test()
        sys.stdout.write("BASELINE                                                              exit=%d\n"
                         % code)
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2

        r = run_all(pristine, MUTATIONS)

        if not prove:
            sys.stdout.write("\nEQUIVALENT MUTANTS - cannot change behaviour, so anything but MISSED is a "
                             "FAILURE\n")
            eq = run_all(pristine, EQUIVALENT)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        for f, b in pristine_tests.items():
            f.write_bytes(b)

    if any(f.read_bytes() != b for f, b in pristine.items()) or \
       any(f.read_bytes() != b for f, b in pristine_tests.items()):
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2

    sys.stdout.write("\nrestored: " + ", ".join(hashlib.md5(f.read_bytes()).hexdigest()[:8]
                                                for f in pristine) + "\n")
    sys.stdout.write("caught by a named test: %d of %d   (trapped %d, compile-only %d, MISSED %d, "
                     "skipped %d)\n"
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
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has\n"
                         "  an opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Find assertions whose expected value comes from the thing they check.

## Why this exists

In one session this defect was found EIGHT times by six different reviewers, and four of those were inside
tests written specifically to close a previous instance of it. The pattern is not carelessness; it is that
the shape is invisible from the inside. When you have just written `maxRatio = 1.0`, writing
`#expect(r <= LearnedCorridorSpeeds.maxRatio)` reads like a check of the clamp. It is a tautology, and it
stays green when the constant moves to 3.0 - which is how a learned corridor came to return an ETA below the
free-flow duration it was handed, with the badge off.

The real instances, all from `git log`:

  #expect(r2 <= LearnedCorridorSpeeds.maxRatio)          maxRatio 1.0 -> 3.0 stayed green
  #expect(out.duration <= out.ceiling)                   a mutated ceiling was invisible
  for n in 1..<LearnedCorridorSpeeds.confidenceThreshold  became an empty range at 1; passed over 0 iterations
  #expect(cN.y == cE.x)                                  both offsets cancelled the function under test
  #expect(abs(pieces.p90 - whole.p90) < 1e-9)            asserted consistency, never correctness

## What it detects, and what it does not

Three shapes, chosen because they can be recognised from the token stream with no false-positive rate worth
arguing about:

  A. **Tautology against a constant.** A comparison in `#expect(...)` where one side is `Type.member` - a
     static member of a type declared under `Sources/` - and the other side is not a literal. True for any
     value the constant takes.
  B. **Both sides of one object.** `#expect(x.a <op> x.b)`, where the same receiver produces the expected
     value and the actual one.
  C. **A range bound taken from the constant under test.** `for i in 0..<Type.member`. Lower the constant
     and the loop body stops running; the test passes over zero iterations.

**Not detected**, and this is stated so the check is not mistaken for complete: two DIFFERENT objects both
produced by the code under test (`pieces.p90` against `whole.p90`) needs dataflow, not pattern matching. The
fourth real instance above is invisible here. A check that claimed to cover it would be the same defect one
level up.

## The escape hatch

A line ending in `// self-ref-ok: <reason>` is allowed. The reason is required and must be more than a word,
because "the point of an allowlist is that entries are argued for" is the only thing keeping it from
becoming a way to silence the check.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCES = ROOT / "Sources"
TESTS = ROOT / "Tests"

# Refuse to pass over an empty or truncated tree. The pin this implements exists because checks that
# iterate over nothing exit 0; that is the same defect this file is about, one level up.
MIN_TEST_FILES = 3
MIN_TYPES = 3

ALLOW = re.compile(r"//\s*self-ref-ok:\s*(?P<reason>.+?)\s*$")
# NON-capturing. The first version captured the operator, so `m.group(3)` in the same-object
# rule returned "<=" instead of the second member and the finding printed "out.duration vs
# out.<=". The match was right and the message was nonsense, which is the kind of thing that
# gets a check ignored.
COMPARISON = r"(?:==|!=|<=|>=|<|>)"

# `Type.member` where Type starts uppercase, and member is NOT followed by `(`.
#
# Deliberately not anchored on a list of known type names: a new type must be covered the day it is added,
# not the day somebody remembers to add it here.
#
# The negative lookahead excludes function calls, and it is there because the first version flagged
# `#expect(Geo.distanceMeters(a, b) == Geo.distanceMeters(b, a))` in the existing suite. That is a
# metamorphic symmetry property - two invocations with different arguments - and it is a legitimate and good
# test. Comparing the code against ITSELF is fine; comparing it against a CONSTANT OF ITS OWN is the defect.
MEMBER = r"[A-Z][A-Za-z0-9_]*\.[a-z][A-Za-z0-9_]*(?!\s*\()"
LITERAL = re.compile(r"^-?(\d[\d_]*(\.\d+)?([eE][-+]?\d+)?|0x[0-9a-fA-F]+|\"[^\"]*\"|true|false|nil)$")


def declared_types() -> set[str]:
    """Type names declared under Sources/. Only these count as 'the thing under test'."""
    out: set[str] = set()
    for f in SOURCES.rglob("*.swift"):
        for m in re.finditer(r"^\s*(?:public\s+|internal\s+|private\s+|final\s+)*"
                             r"(?:struct|class|enum|actor|protocol)\s+([A-Z][A-Za-z0-9_]*)",
                             f.read_text(encoding="utf-8"), re.M):
            out.add(m.group(1))
    return out


def strip_comment(line: str) -> str:
    """Everything before a `//` that is not inside a string literal. Crude but adequate here."""
    in_string = False
    i = 0
    while i < len(line) - 1:
        c = line[i]
        if c == "\\" and in_string:
            i += 2
            continue
        if c == '"':
            in_string = not in_string
        elif c == "/" and line[i + 1] == "/" and not in_string:
            return line[:i]
        i += 1
    return line


def problems_in(path: pathlib.Path, types: set[str]) -> list[tuple[int, str, str]]:
    found: list[tuple[int, str, str]] = []
    text = path.read_text(encoding="utf-8")
    for n, raw in enumerate(text.splitlines(), 1):
        if ALLOW.search(raw):
            continue
        line = strip_comment(raw).strip()
        if not line:
            continue

        # C. A range bound taken from a static member of the code under test.
        for m in re.finditer(r"(?:\.\.<|\.\.\.)\s*(" + MEMBER + r")", line):
            owner = m.group(1).split(".")[0]
            if owner in types:
                found.append((n, "range bound taken from the constant under test", m.group(1)))

        if "#expect(" not in line and "#require(" not in line:
            continue

        # A. A comparison against a static member of the code under test, where the other side is not a
        #    literal - so the assertion holds for any value that member takes.
        for m in re.finditer(r"([A-Za-z0-9_.\[\]!?]+)\s*" + COMPARISON + r"\s*(" + MEMBER + r")\b", line):
            lhs, member = m.group(1).strip(), m.group(2)
            if member.split(".")[0] in types and not LITERAL.match(lhs):
                found.append((n, "compared against the constant it checks; true for any value", member))
        for m in re.finditer(r"(" + MEMBER + r")\s*" + COMPARISON + r"\s*([A-Za-z0-9_.\[\]!?]+)", line):
            member, rhs = m.group(1), m.group(2).strip()
            if member.split(".")[0] in types and not LITERAL.match(rhs):
                found.append((n, "compared against the constant it checks; true for any value", member))

        # B. Both sides of one object: the receiver supplies the expected value and the actual one.
        for m in re.finditer(r"\b([a-z][A-Za-z0-9_]*)\.([a-z][A-Za-z0-9_]*)\s*" + COMPARISON
                             + r"\s*\1\.([a-z][A-Za-z0-9_]*)", line):
            if m.group(2) != m.group(3):
                found.append((n, "both sides come from the same object under test",
                              f"{m.group(1)}.{m.group(2)} vs {m.group(1)}.{m.group(3)}"))
    return found


def main(argv: list[str]) -> int:
    types = declared_types()
    files = sorted(TESTS.rglob("*.swift")) if TESTS.is_dir() else []

    if len(files) < MIN_TEST_FILES:
        sys.stdout.write("SELF-REF FAIL: found %d test files, expected at least %d - "
                         "a check that examines nothing exits 0 and proves nothing\n"
                         % (len(files), MIN_TEST_FILES))
        return 2
    if len(types) < MIN_TYPES:
        sys.stdout.write("SELF-REF FAIL: found %d types under Sources/, expected at least %d - "
                         "with no types to recognise, every assertion looks fine\n" % (len(types), MIN_TYPES))
        return 2

    problems = []
    for f in files:
        for line_no, why, what in problems_in(f, types):
            problems.append((f.relative_to(ROOT).as_posix(), line_no, why, what))

    if "--list-types" in argv:
        sys.stdout.write("types under Sources/: " + ", ".join(sorted(types)) + "\n")

    if problems:
        sys.stdout.write("SELF-REF FAIL: %d assertion(s) take their expected value from the code under test\n"
                         % len(problems))
        for path, line_no, why, what in problems:
            sys.stdout.write("  %s:%d  %s\n      %s\n" % (path, line_no, why, what))
        sys.stdout.write("\n  Compare against a value the test computed, or a literal. If the assertion is\n"
                         "  genuinely right as written, end the line with `// self-ref-ok: <why>`.\n")
        return 1

    sys.stdout.write("SELF-REF OK (%d test files, %d types under Sources/)\n" % (len(files), len(types)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

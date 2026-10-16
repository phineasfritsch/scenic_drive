#!/usr/bin/env python3
"""Mutation harness AND population for etl/profilegate.py and the shipped car_scenic_base.json (T-0012 R9).

WHY IT HAS ONE. `profilegate` evaluates the routing profile's hard gates on one tag row - the profile layer of
P-PROD-01's three-layer parity. It encodes and it evaluates, so CLAUDE.md's Verification section and P-PROC-06
say it ships a population with a literal floor. The shipped profile json is a SUBJECT too: a deleted clause
there is the defect P-PROD-01 exists for, and it must be caught by a named test, not by reading the diff.

THE CONTRACT is ops/mutate/extractadapter.py's, kept identically: `(name, file, old, new)` with `old` verbatim
in the pristine file or SKIP and FAIL; a catch requires a NAMED TEST to fail; the subjects, the emptied test
files and THIS FILE are compared to `git show HEAD:` first; `MIN_MUTATIONS` equals the shipped population;
an EQUIVALENT entry caught is a failure; `--prove-vacuity` empties the tests and requires every mutation MISSED.
Every `__pycache__` under services/etl is purged and the run sleeps past the mtime granularity per mutant.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mutate_only

import extractadapter as harness  # noqa: E402  the protocol: pristine guard, pycache purge, arm

ROOT = harness.ROOT
ETL = harness.ETL
SUBJECT = ETL / "etl" / "profilegate.py"
PROFILE = ROOT / "services" / "routing" / "profiles" / "car_scenic_base.json"
UNIT_TESTS = ETL / "tests" / "test_profilegate.py"
PARITY_TESTS = ETL / "tests" / "test_gate_parity.py"
EMPTIED = (UNIT_TESTS, PARITY_TESTS)
SUBJECTS = (SUBJECT, PROFILE)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/profilegate.py",)
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

ACCESS = '"road_access == PRIVATE || road_access == NO || road_access == DESTINATION", "multiply_by": "0" }'
UNKNOWN_IDENT = "        if tok not in self.values:\n            raise ValueError("
UNREADABLE = '        if match is None:\n            raise ValueError("unreadable expression %r at %d" % (expression, at))'
SURFACE_NAMES = ("GRAVEL", "DIRT", "GROUND", "SAND", "UNPAVED", "COMPACTED")

MUTATIONS = [
    ("a _link class kept whole", SUBJECT, "        value = value[: -len(LINK_SUFFIX)]", "        value = value"),
    ("an unknown highway kept as its own class", SUBJECT, 'return value if value in ROAD_CLASSES else "OTHER"',
     "return value"),
    ("TRACK not a road class", SUBJECT, '"ROAD", "TRACK", "BRIDLEWAY"', '"ROAD", "BRIDLEWAY"'),
    ("permit read as YES", SUBJECT, 'PERMIT_ACCESS = "PRIVATE"', 'PERMIT_ACCESS = "YES"'),
    ("the last restriction key wins", SUBJECT, "        worst = max(worst, rank)", "        worst = rank"),
    ("the least restrictive key wins", SUBJECT, "        worst = max(worst, rank)", "        worst = min(worst, rank)"),
    ("motor_vehicle not read", SUBJECT, '("motorcar", "motor_vehicle", "vehicle", "access")',
     '("motorcar", "vehicle", "access")'),
    ("access not read", SUBJECT, '("motorcar", "motor_vehicle", "vehicle", "access")',
     '("motorcar", "motor_vehicle", "vehicle")'),
    ("PRIVATE outranks NO", SUBJECT, '"AGRICULTURAL", "PRIVATE", "NO")', '"AGRICULTURAL", "NO", "PRIVATE")'),
    ("an unknown access value is the worst", SUBJECT, "if value in ROAD_ACCESS else 0",
     "if value in ROAD_ACCESS else len(ROAD_ACCESS) - 1"),
    ("an absent surface is OTHER", SUBJECT, '        return "MISSING"', '        return "OTHER"'),
    ("an unknown surface kept as its own value", SUBJECT, 'return value if value in SURFACES else "OTHER"',
     "return value"),
    ("SAND not a surface", SUBJECT, '"GRASS", "SAND", "WOOD"', '"GRASS", "WOOD"'),
    ("car_access held false", SUBJECT, '"car_access": True}', '"car_access": False}'),
    ("|| evaluated as &&", SUBJECT, "            value = value or right", "            value = value and right"),
    ("&& evaluated as ||", SUBJECT, "            value = value and right", "            value = value or right"),
    ("! ignored", SUBJECT, "            return not self.unary()", "            return self.unary()"),
    ("== and != swapped", SUBJECT, "(value == constant) if op == \"==\" else (value != constant)",
     "(value != constant) if op == \"==\" else (value == constant)"),
    ("trailing tokens accepted", SUBJECT, "        if self.peek() is not None:", "        if False:"),
    ("an unknown encoded value reads false", SUBJECT, UNKNOWN_IDENT,
     "        if tok not in self.values:\n            return False\n            raise ValueError("),
    ("a non-boolean read as a boolean", SUBJECT, "        if not isinstance(value, bool):", "        if False:"),
    ("an unbalanced parenthesis accepted", SUBJECT, '            if self.take() != ")":', "            if False:"),
    ("an unreadable character skipped", SUBJECT, UNREADABLE,
     "        if match is None:\n            at += 1\n            continue"),
    ("any rule shape read", SUBJECT, "        if set(rule) != RULE_KEYS:", "        if False:"),
    ("the last firing factor replaces the product", SUBJECT, "            product *= factor",
     "            product = factor"),
    ("every rule's factor applied", SUBJECT, '        if fires(rule["if"], values):',
     '        if True or fires(rule["if"], values):'),
    ("a low priority read as gated", SUBJECT, "    return priority(tags, profile) == 0.0",
     "    return priority(tags, profile) <= 0.5"),
    ("the request profile read instead", SUBJECT, '/ "car_scenic_base.json"', '/ "car_scenic_request.json"'),
    ("profile: DESTINATION let through", PROFILE, " || road_access == DESTINATION", ""),
    ("profile: PRIVATE let through", PROFILE, '"road_access == PRIVATE || ', '"'),
    ("profile: NO let through", PROFILE, " || road_access == NO ||", " ||"),
    ("profile: the access gate a penalty", PROFILE, ACCESS, ACCESS.replace('"0" }', '"0.1" }')),
    ("profile: FINE_GRAVEL let through", PROFILE, " || surface == FINE_GRAVEL", ""),
    ("profile: TRACK let through", PROFILE, '"road_class == TRACK"', '"road_class == TRACK && false"'),
    ("profile: car_access inverted", PROFILE, '"!car_access"', '"car_access"'),
    ("profile: motorway hard-excluded", PROFILE, '    { "if": "road_class == TRACK"',
     '    { "if": "road_class == MOTORWAY", "multiply_by": "0" },\n    { "if": "road_class == TRACK"'),
    ("profile: trunk hard-excluded", PROFILE, '    { "if": "road_class == TRACK"',
     '    { "if": "road_class == TRUNK", "multiply_by": "0" },\n    { "if": "road_class == TRACK"'),
] + [("profile: %s let through" % s, PROFILE, "surface == %s || " % s, "") for s in SURFACE_NAMES]

EQUIVALENT = [
    ("tokens strips both ends - `_TOKEN` opens with `\\s*`, so leading whitespace is consumed by the first match "
     "either way, and `rstrip` already removed the trailing run", SUBJECT,
     "    stripped = expression.rstrip()", "    stripped = expression.strip()"),
]
KNOWN_MISSED = []

MIN_MUTATIONS = 43
harness.PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"] + [str(path) for path in EMPTIED]


def main(argv: list | None = None) -> int:
    only = mutate_only.select_only(sys.argv[1:] if argv is None else argv,
                                   [m[0] for m in list(MUTATIONS) + list(EQUIVALENT)], substring=True,
                                   split=False)
    parser = argparse.ArgumentParser(allow_abbrev=False, prog="ops/mutate/profilegate.py",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--prove-vacuity", action="store_true",
                        help="empty the test files and require every mutation to be MISSED")
    parser.add_argument("--only", action="append", default=[], metavar="SUBSTRING",
                        help="run only the entries whose name contains SUBSTRING (repeatable); the floor still "
                             "counts the whole population")
    args = parser.parse_args(argv)
    if len(MUTATIONS) < MIN_MUTATIONS:
        print("population is %d, floor is %d" % (len(MUTATIONS), MIN_MUTATIONS), file=sys.stderr)
        return 1
    mutations = [m for m in MUTATIONS if only is None or m[0] in only]
    equivalent = [m for m in EQUIVALENT if only is None or m[0] in only]
    harness.assert_pristine(GUARDED)
    originals = {path: path.read_text(encoding="utf-8") for path in SUBJECTS + EMPTIED}
    subjects = {path: originals[path] for path in SUBJECTS}
    if args.prove_vacuity:
        for path in EMPTIED:
            path.write_text("", encoding="utf-8", newline="\n")
        caught, missed, skipped = harness.arm(mutations, subjects, False, "VACUITY")
        harness.restore(originals)
        harness.assert_pristine(GUARDED)
        ok = caught == 0 and skipped == 0 and missed == len(mutations)
        print("VACUITY %s" % ("PROVED" if ok else "FAILED"))
        return 0 if ok else 1
    code, failed = harness.run_tests()
    if code != 0 or failed:
        print("BASELINE is not green: exit %d, %s" % (code, failed), file=sys.stderr)
        return 1
    print("BASELINE exit=0, %d mutations, floor %d" % (len(mutations), MIN_MUTATIONS))
    caught, missed, skipped = harness.arm(mutations, subjects, True, "MUTATIONS")
    eq_caught, _eq_missed, eq_skipped = harness.arm(equivalent, subjects, False, "EQUIVALENT")
    harness.assert_pristine(GUARDED)
    ok = caught == len(mutations) and skipped == 0 and eq_caught == 0 and eq_skipped == 0 and not KNOWN_MISSED
    print("MUTATE %s  caught=%d/%d equivalent_caught=%d" % ("OK" if ok else "FAILED", caught,
                                                            len(mutations), eq_caught))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

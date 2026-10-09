#!/usr/bin/env python3
"""Mutation harness AND population for etl/fallback.py (T-0270, ruling F10).

WHY IT HAS ONE. `fallback.choose` decides which of placeallow's places the bundled fallback corpus carries -
the only places a device has before its first download - so it SELECTS, and CLAUDE.md's Verification section
and P-PROC-06 say it ships a population with a literal floor. Covered: every cap row raised, lowered and
dropped; the cut's bounds; the rank (reversed, by osm_id, input order, osm_type dropped, placeallow's
order); the refusal of an unruled class; the
kind stamp (here and in corpus.build's one new branch); the ceiling literal, its hand-off and its exit code; the
command's stdout count line (kept per class, places=) and its exit 2 for a malformed --built-at.

THE CONTRACT is ops/mutate/extractadapter.py's, kept identically: `(name, file, old, new)` entries whose `old`
must appear VERBATIM or the run FAILS; a catch requires a NAMED TEST to fail; subjects, emptied tests and this
file are compared to `git show HEAD:` first and after; `MIN_MUTATIONS` EQUALS the population; an EQUIVALENT
catch is a FAILURE; `--prove-vacuity` empties the tests and requires every mutation MISSED; `--only` runs a
named subset. Every `__pycache__` under services/etl is purged before each run, then 1.1 s.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mutate_only

import extractadapter as harness  # noqa: E402  the protocol: pristine guard, pycache purge, arm

ETL = harness.ETL
SUBJECT = ETL / "etl" / "fallback.py"
CORPUS = ETL / "etl" / "corpus.py"
TESTS = ETL / "tests" / "test_fallback.py"
COMMITTED_TESTS = ETL / "tests" / "test_fallback_committed.py"
EMPTIED = (TESTS, COMMITTED_TESTS)
SUBJECTS = (SUBJECT, CORPUS)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/fallback.py",)
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

CAP_ROWS = [("viewpoint", 200), ("peak", 200), ("waterfall", 200), ("beach", 200), ("trailhead", 200),
            ("museum", 150), ("garden", 150), ("park", 400), ("town", 150), ("cafe", 50)]


def row(cls: str, cap: int) -> str:
    return '    ("%s", %d),\n' % (cls, cap)


CUT = "        chosen.extend(ranked[:cap])"
RANK = '        ranked = sorted(by_class[cls], key=lambda p: place_id(p["osm_type"], p["osm_id"]))'
REFUSE = '            raise ValueError(f"place class {place[\'cls\']!r} has no cap in etl.fallback.CAPS")'
HANDOFF = "                              budget_bytes=FALLBACK_BUDGET_BYTES, kind=KIND)"
CEILING = "FALLBACK_BUDGET_BYTES = 1048576"
KIND_LINE = 'KIND = "fallback"'
EXIT = "        return corpus.BUDGET_EXIT"
CORPUS_KIND = '        if kind is not None:\n            writer.set_meta("kind", kind)'
REGION = "        report = corpus.build(extract, out_path, built_at, region=region,"
KEPT = '    report["kept"] = {cls: sum(1 for p in chosen if p["cls"] == cls) for cls, _cap in CAPS}'
BUILT_AT_GUARD = (
    "    try:\n"
    "        corpus.compact_built_at(args.built_at)\n"
    "    except ValueError:\n"
    "        print(f\"--built-at must be YYYY-MM-DDTHH:MM:SSZ, got {args.built_at!r}\", file=sys.stderr)\n"
    "        return 2\n")
PLACES_SUM = 'sum(report["kept"].values())'
CAPS_ORDER = "    for cls, cap in CAPS:"

MUTATIONS = (
    [("cap %s raised by one" % c, SUBJECT, row(c, n), row(c, n + 1)) for c, n in CAP_ROWS]
    + [("cap %s lowered by one" % c, SUBJECT, row(c, n), row(c, n - 1)) for c, n in CAP_ROWS]
    + [("cap row %s dropped" % c, SUBJECT, row(c, n), "") for c, n in CAP_ROWS]
    + [
        ("the cut keeps one past the cap", SUBJECT, CUT, "        chosen.extend(ranked[:cap + 1])"),
        ("the cut skips the best-ranked place", SUBJECT, CUT, "        chosen.extend(ranked[1:cap + 1])"),
        ("the cut is gone - every place kept", SUBJECT, CUT, "        chosen.extend(ranked)"),
        ("the rank reversed", SUBJECT, RANK, RANK[:-1] + ", reverse=True)"),
        ("the rank by osm_id, not place_id", SUBJECT, RANK,
         '        ranked = sorted(by_class[cls], key=lambda p: p["osm_id"])'),
        ("the rank is input order", SUBJECT, RANK, "        ranked = list(by_class[cls])"),
        ("the rank drops osm_type - every place ranked as a node", SUBJECT, RANK,
         RANK.replace('place_id(p["osm_type"], ', 'place_id("n", ')),
        ("the rank drops osm_type - every place ranked as a way", SUBJECT, RANK,
         RANK.replace('place_id(p["osm_type"], ', 'place_id("w", ')),
        ("the rank is placeallow's (osm_type, osm_id) order", SUBJECT, RANK,
         '        ranked = sorted(by_class[cls], key=lambda p: ("nwr".index(p["osm_type"]), p["osm_id"]))'),
        ("an unruled class is dropped silently", SUBJECT, REFUSE, "            continue"),
        ("the kind stamp says full", SUBJECT, KIND_LINE, 'KIND = "full"'),
        ("the kind is not handed to corpus.build", SUBJECT, HANDOFF,
         "                              budget_bytes=FALLBACK_BUDGET_BYTES)"),
        ("the ceiling is not handed to corpus.build", SUBJECT, HANDOFF, "                              kind=KIND)"),
        ("the ceiling literal doubled", SUBJECT, CEILING, "FALLBACK_BUDGET_BYTES = 2097152"),
        ("the ceiling literal halved", SUBJECT, CEILING, "FALLBACK_BUDGET_BYTES = 524288"),
        ("a refused build exits 0", SUBJECT, EXIT, "        return 0"),
        ("corpus.build never writes the kind", CORPUS, CORPUS_KIND, "        pass"),
        ("corpus.build stamps every corpus", CORPUS, CORPUS_KIND,
         '        writer.set_meta("kind", kind or "full")'),
        ("the kept count is over the uncapped selection", SUBJECT, KEPT, KEPT.replace("in chosen", "in places")),
        ("a malformed --built-at is not refused with exit 2", SUBJECT, BUILT_AT_GUARD, ""),
        ("places= prints the class count, not the place count", SUBJECT, PLACES_SUM, 'len(report["kept"])'),
    ]
)

EQUIVALENT = [
    ("the region not passed to corpus.build - the extract fallback.build writes carries the same `region`, and "
     "corpus.build reads `region or extract_region`", SUBJECT, REGION,
     "        report = corpus.build(extract, out_path, built_at,"),
    ("choose walks CAPS in sorted order, not the ruled order - corpuswriter.write_places inserts "
     "`rows = sorted(places)` (by place_id), and build counts `kept` from CAPS itself, so the order choose "
     "appends classes in reaches neither the file nor the count line", SUBJECT, CAPS_ORDER,
     "    for cls, cap in sorted(CAPS):"),
]
KNOWN_MISSED = []

MIN_MUTATIONS = 51
harness.PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"] + [str(path) for path in EMPTIED]


def main(argv: list | None = None) -> int:
    only = mutate_only.select_only(sys.argv[1:] if argv is None else argv,
                                   [m[0] for m in list(MUTATIONS) + list(EQUIVALENT)], substring=True,
                                   split=False)
    parser = argparse.ArgumentParser(allow_abbrev=False, prog="ops/mutate/fallback.py", description=__doc__.splitlines()[0])
    parser.add_argument("--prove-vacuity", action="store_true",
                        help="empty the test files and require every mutation to be MISSED")
    parser.add_argument("--only", action="append", default=[], metavar="SUBSTRING",
                        help="run only the entries whose name contains SUBSTRING (repeatable)")
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

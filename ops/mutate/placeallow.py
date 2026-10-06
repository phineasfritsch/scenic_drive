#!/usr/bin/env python3
"""Mutation harness AND population for etl/placeallow.py (T-0266, ruling R10).

WHY IT HAS ONE. `placeallow.select` decides which OSM features become the corpus's `places` rows - the
rows typed search and the Surprise pool read - and computes each row's point. It selects and it computes,
so CLAUDE.md's Verification section and P-PROC-06 say it ships a population with a literal floor. The four
classes the task names are all here: an allowlist row dropped (every row), a blocklist row dropped (every
row), an unnamed feature accepted, a class swapped; plus types, order, access, the chain predicate, the
location rule, the dedupe bounds and the count line.

THE CONTRACT is ops/mutate/extractadapter.py's, kept identically:

  * each entry is `(name, file, old, new)`; `old` must appear VERBATIM in the pristine file or the run
    reports SKIP and FAILS - a stale anchor is a harness that has gone quietly blind;
  * a catch requires a NAMED TEST to fail; a non-zero exit is Python noticing, not a check noticing;
  * the subject, the test file this suite empties, and THIS FILE are compared to `git show HEAD:` before
    anything runs, and the restore is verified afterwards: a mutation report is a claim about a COMMIT;
  * `MIN_MUTATIONS` EQUALS the shipped population, so deleting any one mutation refuses the run;
  * EQUIVALENT mutants cannot change behaviour, so a catch there is a FAILURE;
  * `--prove-vacuity` empties the test files and requires EVERY mutation to report MISSED; `--only` runs a
    named subset (a fix round re-runs the touched rows), the floor still counts the whole population.

PYTHON SUBJECTS: every `__pycache__` under services/etl is purged before each run and the run sleeps past
the filesystem's timestamp granularity (the whole-second mtime false green).
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import extractadapter as harness  # noqa: E402  the protocol: pristine guard, pycache purge, arm

ROOT = harness.ROOT
ETL = harness.ETL
SUBJECT = ETL / "etl" / "placeallow.py"
TESTS = ETL / "tests" / "test_placeallow.py"
GEOMETRY_TESTS = ETL / "tests" / "test_placeallow_geometry.py"
EMPTIED = (TESTS, GEOMETRY_TESTS)
SUBJECTS = (SUBJECT,)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/placeallow.py",)
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

ALLOW_ROWS = [
    '    Allow("tourism", "viewpoint", "nw", "viewpoint"),\n',
    '    Allow("natural", "peak", "n", "peak"),\n',
    '    Allow("waterway", "waterfall", "n", "waterfall"),\n',
    '    Allow("natural", "beach", "nwr", "beach"),\n',
    '    Allow("highway", "trailhead", "n", "trailhead"),\n',
    '    Allow("tourism", "museum", "nwr", "museum"),\n',
    '    Allow("amenity", "cafe", "nwr", "cafe"),\n',
    '    Allow("leisure", "garden", "nwr", "garden"),\n',
    '    Allow("leisure", "park", "nwr", "park"),\n',
    '    Allow("place", "city", "n", "town"),\n',
    '    Allow("place", "town", "n", "town"),\n',
    '    Allow("place", "village", "n", "town"),\n',
]
CHAIN_ROWS = [
    '    Chain("Starbucks", "Q37158", "starbucks"),\n',
    '    Chain("The Coffee Bean & Tea Leaf", "Q1141384", "coffee bean"),\n',
    '    Chain("Peet\'s Coffee", "Q1094101", "peet s"),\n',
    '    Chain("It\'s Boba Time", "Q119951349", "boba time"),\n',
    '    Chain("85°C", "Q4644852", "85 c"),\n',
    '    Chain("Blue Bottle Coffee", "Q4928917", "blue bottle"),\n',
    '    Chain("Ding Tea", "Q112123475", "ding tea"),\n',
    '    Chain("Philz Coffee", "Q18156812", "philz"),\n',
    '    Chain("Corner Bakery", "Q5171598", "corner bakery"),\n',
    '    Chain("7 Leaves Cafe", "Q118480682", "7 leaves"),\n',
    '    Chain("Le Pain Quotidien", "Q2046903", "le pain quotidien"),\n',
    '    Chain("Sharetea", "Q64827032", "sharetea"),\n',
    '    Chain("Joe & The Juice", "Q26221514", "joe the juice"),\n',
    '    Chain("Kreation Organic", "Q113363083", "kreation"),\n',
    '    Chain("Tapioca Express", "Q23462008", "tapioca express"),\n',
    '    Chain("Dutch Bros. Coffee", "Q5317253", "dutch bros"),\n',
    '    Chain("Quickly", "Q3771463", "quickly"),\n',
    '    Chain("Tastea", "Q122328236", "tastea"),\n',
]
NAME_RULE = '    name = (tags.get(NAME_KEY) or "").strip()'
NAME_RETURN = NAME_RULE + "\n    return name or None"
ACCESS_GATE = "        if tags.get(ACCESS_KEY) in REFUSED_ACCESS:"
UNNAMED = '        if name is None:\n            counts["unnamed"] += 1\n            continue'
ACCESS = 'REFUSED_ACCESS = frozenset({"private", "no"})'
QID_OR_BRAND = "        if qid == chain.wikidata or brand == chain.brand.casefold():"
BRAND = '    brand = (tags.get(BRAND_KEY) or "").casefold()'
NAME_MATCH = "        if contains_run(words, tokens(chain.phrase)):"
DISTINCT = "    distinct = list(dict.fromkeys(node_ids))"
ROLES = 'OUTER_ROLES = frozenset({"outer", ""})'
DP = "COORD_DP = 7"
MISSING = "    if not distinct or any(n not in nodes for n in distinct):"
BOX = "bbox[0] <= p_lat <= bbox[1] and bbox[2] <= p_lon <= bbox[3]"
KEY = "points.get((cls, name.casefold()), ())"
DEDUPE_SIDE = '        if osm_type != "n" and any('
SKIP_COUNT = '            counts["skipped_geometry"] += 1'
MEMBER_TYPE = 'if m.get("type") == MEMBER_WAY and (m.get("role") or "") in OUTER_ROLES]'
TYPE_TEST = "        if tags.get(row.key) == row.value and osm_type in row.types:"
GUARD = "    if not member_ways or any(w not in ways for w in member_ways):"
GUARDED_READ = GUARD + "\n        return None\n    return [n for w in member_ways for n in ways[w]]"
MEAN = MISSING + "\n        return None\n    lats = [nodes[n][0] for n in distinct]\n    lons = [nodes[n][1] for n in distinct]"
REL_LOCATE = "            node_ids = relation_nodes(members, ways)"
LOCATE_CALL = "        where = locate(node_ids or [], nodes)"

MUTATIONS = (
    [("drop allowlist row %d" % i, SUBJECT, row, "") for i, row in enumerate(ALLOW_ROWS)]
    + [("drop blocklist row %d" % i, SUBJECT, row, "") for i, row in enumerate(CHAIN_ROWS)]
    + [
        ("accept an unnamed feature - the guard gone", SUBJECT, UNNAMED,
         '        if False:\n            counts["unnamed"] += 1\n            continue'),
        ("accept a blank name - the strip gone", SUBJECT, NAME_RULE, '    name = tags.get(NAME_KEY) or ""'),
        ("swap viewpoint and peak", SUBJECT, ALLOW_ROWS[0] + ALLOW_ROWS[1],
         ALLOW_ROWS[0].replace('"viewpoint"),', '"peak"),') + ALLOW_ROWS[1].replace('"peak"),', '"viewpoint"),')),
        ("swap beach and park", SUBJECT, ALLOW_ROWS[3], ALLOW_ROWS[3].replace('"beach"),', '"park"),')),
        ("garden read as park", SUBJECT, ALLOW_ROWS[7], ALLOW_ROWS[7].replace('"garden"),', '"park"),')),
        ("village keeps its own class", SUBJECT, ALLOW_ROWS[11], ALLOW_ROWS[11].replace('"town"),', '"village"),')),
        ("museum read as cafe", SUBJECT, ALLOW_ROWS[5], ALLOW_ROWS[5].replace('"museum"),', '"cafe"),')),
        ("a peak way is a peak", SUBJECT, ALLOW_ROWS[1], ALLOW_ROWS[1].replace('"n", "peak"', '"nw", "peak"')),
        ("a viewpoint relation is a viewpoint", SUBJECT, ALLOW_ROWS[0], ALLOW_ROWS[0].replace('"nw"', '"nwr"')),
        ("a place=town way is a town", SUBJECT, ALLOW_ROWS[10], ALLOW_ROWS[10].replace('"n"', '"nw"')),
        ("ignore object types altogether", SUBJECT, TYPE_TEST, "        if tags.get(row.key) == row.value:"),
        ("cafe ahead of museum - the first-row order broken", SUBJECT, ALLOW_ROWS[5] + ALLOW_ROWS[6],
         ALLOW_ROWS[6] + ALLOW_ROWS[5]),
        ("park ahead of cafe", SUBJECT, ALLOW_ROWS[6] + ALLOW_ROWS[7] + ALLOW_ROWS[8],
         ALLOW_ROWS[8] + ALLOW_ROWS[6] + ALLOW_ROWS[7]),
        ("access=no admitted", SUBJECT, ACCESS, 'REFUSED_ACCESS = frozenset({"private"})'),
        ("access=customers refused too", SUBJECT, ACCESS, 'REFUSED_ACCESS = frozenset({"private", "no", "customers"})'),
        ("the QID/brand signal gone", SUBJECT, QID_OR_BRAND, "        if False:"),
        ("the QID signal alone gone", SUBJECT, QID_OR_BRAND, "        if brand == chain.brand.casefold():"),
        ("the brand signal alone gone", SUBJECT, QID_OR_BRAND, "        if qid == chain.wikidata:"),
        ("brand compared without casefolding", SUBJECT, BRAND, '    brand = tags.get(BRAND_KEY) or ""'),
        ("the name signal gone", SUBJECT, NAME_MATCH, "        if False:"),
        ("name matched as a substring, not as tokens", SUBJECT, NAME_MATCH,
         "        if chain.phrase.replace(' ', '') in name.casefold().replace(' ', ''):"),
        ("name tokens matched in any order", SUBJECT, NAME_MATCH,
         "        if set(tokens(chain.phrase)) <= set(words):"),
        ("a closed way counts its first node twice", SUBJECT, DISTINCT, "    distinct = list(node_ids)"),
        ("a relation's inner ring counts", SUBJECT, ROLES, 'OUTER_ROLES = frozenset({"outer", "", "inner"})'),
        ("a blank-role member way does not count", SUBJECT, ROLES, 'OUTER_ROLES = frozenset({"outer"})'),
        ("six decimal places", SUBJECT, DP, "COORD_DP = 6"),
        ("a missing node is not a skip", SUBJECT, MISSING, "    if not distinct:"),
        ("the bbox max lat exclusive", SUBJECT, BOX, BOX.replace("p_lat <= bbox[1]", "p_lat < bbox[1]")),
        ("the bbox min lat exclusive", SUBJECT, BOX, BOX.replace("bbox[0] <= p_lat", "bbox[0] < p_lat")),
        ("the bbox max lon exclusive", SUBJECT, BOX, BOX.replace("p_lon <= bbox[3]", "p_lon < bbox[3]")),
        ("the bbox min lon exclusive", SUBJECT, BOX, BOX.replace("bbox[2] <= p_lon", "bbox[2] < p_lon")),
        ("dedupe ignores lon", SUBJECT, BOX, "bbox[0] <= p_lat <= bbox[1]"),
        ("dedupe ignores lat", SUBJECT, BOX, "bbox[2] <= p_lon <= bbox[3]"),
        ("dedupe across classes", SUBJECT, KEY,
         "[pt for (c, n), pts in points.items() if n == name.casefold() for pt in pts]"),
        ("dedupe without casefolding", SUBJECT, KEY, "points.get((cls, name), ())"),
        ("dedupe gone", SUBJECT, DEDUPE_SIDE, "        if False and any("),
        ("dedupe drops the node, not the area", SUBJECT, DEDUPE_SIDE, '        if osm_type == "n" and any('),
        ("dedupe skips relations", SUBJECT, DEDUPE_SIDE, '        if osm_type == "w" and any('),
        ("dedupe skips ways", SUBJECT, DEDUPE_SIDE, '        if osm_type == "r" and any('),
        ("a padded name emitted unstripped", SUBJECT, NAME_RETURN,
         '    name = tags.get(NAME_KEY) or ""\n    return name if name.strip() else None'),
        ("strip spaces only, not tabs", SUBJECT, NAME_RULE, '    name = (tags.get(NAME_KEY) or "").strip(" ")'),
        ("strip the left only", SUBJECT, NAME_RULE, '    name = (tags.get(NAME_KEY) or "").lstrip()'),
        ("strip the right only", SUBJECT, NAME_RULE, '    name = (tags.get(NAME_KEY) or "").rstrip()'),
        ("access refuses nodes only", SUBJECT, ACCESS_GATE,
         '        if osm_type == "n" and tags.get(ACCESS_KEY) in REFUSED_ACCESS:'),
        ("access skips ways", SUBJECT, ACCESS_GATE,
         '        if osm_type != "w" and tags.get(ACCESS_KEY) in REFUSED_ACCESS:'),
        ("access skips relations", SUBJECT, ACCESS_GATE,
         '        if osm_type != "r" and tags.get(ACCESS_KEY) in REFUSED_ACCESS:'),
        ("a geometry skip goes uncounted", SUBJECT, SKIP_COUNT, '            counts["skipped_geometry"] += 0'),
        ("a node member counts as an outer way", SUBJECT, MEMBER_TYPE,
         MEMBER_TYPE.replace('m.get("type") == MEMBER_WAY and ', "")),
        ("B1 a relation is skipped only when EVERY member way is absent", SUBJECT, GUARD,
         GUARD.replace("any(", "all(")),
        ("B1b a partial relation located from the member ways present", SUBJECT, GUARDED_READ,
         GUARDED_READ.replace("any(", "all(").replace("ways[w]", "ways.get(w, ())")),
        ("the relation guard gone", SUBJECT, GUARD, "    if not member_ways:"),
        ("the relation guard gone, an absent way read as empty", SUBJECT, GUARDED_READ,
         GUARDED_READ.replace(" or any(w not in ways for w in member_ways)", "")
         .replace("ways[w]", "ways.get(w, ())")),
        ("a way is skipped only when EVERY node is absent", SUBJECT, MISSING, MISSING.replace("any(", "all(")),
        ("a partial way located from the nodes present", SUBJECT, MEAN,
         MEAN.replace("any(", "all(").replace("in distinct]", "in distinct if n in nodes]")),
        ("no distinct node is not a skip", SUBJECT, MISSING, "    if any(n not in nodes for n in distinct):"),
        ("a relation geometry skip goes uncounted", SUBJECT, REL_LOCATE,
         REL_LOCATE + "\n            if node_ids is None:\n                continue"),
        ("a way geometry skip goes uncounted", SUBJECT, LOCATE_CALL,
         LOCATE_CALL + '\n        if where is None and osm_type == "w":\n            continue'),
        ("an unlocatable relation handed to locate as None", SUBJECT, LOCATE_CALL,
         "        where = locate(node_ids, nodes)"),
    ]
)

EQUIVALENT = [
    ("dict.get's own default spelled out - `d.get(k)` IS `d.get(k, None)`", SUBJECT, BRAND,
     '    brand = (tags.get(BRAND_KEY, None) or "").casefold()'),
    ("membership of a set copy - `x in frozenset(s)` and `x in set(s)` are one relation", SUBJECT,
     ACCESS_GATE,
     "        if tags.get(ACCESS_KEY) in set(REFUSED_ACCESS):"),
    ("`ways.get(w, ())` behind the guard - line `if not member_ways or any(w not in ways ...)` returns None "
     "whenever a member way is absent, so the read below it only ever sees present keys", SUBJECT,
     GUARDED_READ, GUARDED_READ.replace("ways[w]", "ways.get(w, ())")),
    ("the empty-relation clause dropped - an empty member list yields [], and `locate([])` returns None by its "
     "own `not distinct`, so select counts the same skip", SUBJECT, GUARD,
     "    if any(w not in ways for w in member_ways):"),
]
KNOWN_MISSED = []

MIN_MUTATIONS = 88
harness.PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"] + [str(path) for path in EMPTIED]


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops/mutate/placeallow.py", description=__doc__.splitlines()[0])
    parser.add_argument("--prove-vacuity", action="store_true",
                        help="empty the test files and require every mutation to be MISSED")
    parser.add_argument("--only", action="append", default=[], metavar="SUBSTRING",
                        help="run only the entries whose name contains SUBSTRING (repeatable); the floor still "
                             "counts the whole population")
    args = parser.parse_args(argv)
    if len(MUTATIONS) < MIN_MUTATIONS:
        print("population is %d, floor is %d" % (len(MUTATIONS), MIN_MUTATIONS), file=sys.stderr)
        return 1
    mutations = [m for m in MUTATIONS if not args.only or any(o in m[0] for o in args.only)]
    equivalent = [m for m in EQUIVALENT if not args.only or any(o in m[0] for o in args.only)]
    if not mutations and not equivalent:
        print("--only matched nothing", file=sys.stderr)
        return 1
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

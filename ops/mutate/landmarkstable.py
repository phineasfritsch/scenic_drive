#!/usr/bin/env python3
"""Mutation harness AND population for the corpus landmarks table (T-0379, acceptance A9).

WHY IT HAS ONE. etl/corpus.py's landmark_rows encodes ele and the 5-dp point as integers and picks the candidate
ways handed to landmarks.nearest_way_id through a grid (way_cells, cell_of, CELL_DEG, MARGIN_DEG); a candidate
set that drops a near way stores a wrong or NULL nearest_way_id with every other column right. It computes, so
CLAUDE.md's Verification section and P-PROC-06 say it ships a population with a literal floor. The writer, the
content digest and the region build's flag are mutated beside it because each can lose the table whole.

THE CONTRACT is ops/mutate/extractadapter.py's, kept identically (see ops/mutate/landmarks.py): verbatim anchors
or SKIP-and-fail, a catch needs a NAMED TEST failing, the subjects / emptied tests / this file are compared to
`git show HEAD:` before and after, MIN_MUTATIONS EQUALS the population, an EQUIVALENT that is caught is a
failure, `--prove-vacuity` empties the tests and requires every mutation MISSED, `--only` runs a named subset.
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
CORPUS = ETL / "etl" / "corpus.py"
WRITER = ETL / "etl" / "corpuswriter.py"
DIGEST = ETL / "etl" / "contentdigest.py"
STAGE = ETL / "regionbuild" / "fullcorpus.py"
TESTS = ETL / "tests" / "test_corpus_landmarks.py"
REGION_TESTS = ETL / "tests" / "test_region_corpus.py"
EMPTIED = (TESTS, REGION_TESTS)
SUBJECTS = (CORPUS, WRITER, DIGEST, STAGE)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/corpus.py",)
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

MARGIN = "MARGIN_DEG = 0.01\n"
WAY_LAT = "        for i in range(cell_of(min(lats)), cell_of(max(lats)) + 1):"
WAY_LON = "            for j in range(cell_of(min(lons)), cell_of(max(lons)) + 1):"
FILE = "                cells.setdefault((i, j), []).append(index)"
WIDEN = "        widen = MARGIN_DEG / math.cos(math.radians(lat))"
LM_LAT = "        for i in range(cell_of(lat - MARGIN_DEG), cell_of(lat + MARGIN_DEG) + 1):"
LM_LON = "            for j in range(cell_of(lon - widen), cell_of(lon + widen) + 1):"
LOOKUP = "                near.update(cells.get((i, j), ()))"
ELE = '        ele = None if lm["ele_m"] is None else round(lm["ele_m"] * 10)'
ROW = ('        rows.append((lm["osm_type"], lm["osm_id"], lm["kind"], lm["name"], ele, round(lat * 1e5),\n'
       '                     round(lon * 1e5), landmarks.nearest_way_id((lat, lon), [pairs[k] for k in sorted(near)])))')
FOUND = '        found = landmarks.select(landmarks_osm)[0] if landmarks_osm is not None else []'
WRITE = '        writer.write_landmarks(landmark_rows(found, ways))'
INSERT = '            "VALUES (?,?,?,?,?,?,?,?)", sorted(rows, key=lambda row: (row[0], row[1])))'
SELECT = ('    ("landmarks",\n'
          '     "SELECT osm_type, osm_id, kind, name, ele_dm, lat_e5, lon_e5, nearest_way_id FROM landmarks "\n'
          '     "ORDER BY osm_type, osm_id"),\n')
FLAG = ('                        "--built-at", BUILT_AT, "--region", layout.region,\n'
        '                        "--landmarks-osm", str(layout.places_xml)])')
DIGEST_COLUMNS = ("osm_type", "osm_id", "kind", "name", "ele_dm", "lat_e5", "lon_e5", "nearest_way_id")
SELECTED = ", ".join(DIGEST_COLUMNS)
assert SELECT.count(SELECTED) == 1


def digest_without(*dropped: str) -> str:
    return SELECT.replace(SELECTED, ", ".join(c for c in DIGEST_COLUMNS if c not in dropped))


def digest_reading(column: str, expression: str) -> str:
    return SELECT.replace(SELECTED, ", ".join(expression if c == column else c for c in DIGEST_COLUMNS))


# The digest keeps every column but loses its precision: two corpora one unit apart share a content_sha256.
LOSSY_INTEGERS = ("ele_dm", "lat_e5", "lon_e5", "nearest_way_id")
# Lossy projections a one-unit step can miss (rv3): a quotient by k keeps v and v + 1 together unless v + 1 is a
# multiple of k; round(x, -1) and CAST(x AS REAL) return a REAL that render_field prints with 9 significant digits.
LOSSY_READS = (
    ("nearest_way_id", "nearest_way_id / 2"),
    ("ele_dm", "ele_dm / 3"),
    ("lat_e5", "lat_e5 / 7"),
    ("ele_dm", "round(ele_dm, -1)"),
    ("nearest_way_id", "CAST(nearest_way_id AS REAL)"),
)
assert SELECT.count("lat_e5, lon_e5") == 1
UNORDERED = SELECT.replace('\n     "ORDER BY osm_type, osm_id"', "")
assert UNORDERED != SELECT


CLI = "                       region=args.region, budget_bytes=args.budget_bytes, landmarks_osm=args.landmarks_osm)"

MUTATIONS = [
    ("margin under NEAR_M (0.001 deg)", CORPUS, MARGIN, "MARGIN_DEG = 0.001\n"),
    ("margin zero", CORPUS, MARGIN, "MARGIN_DEG = 0.0\n"),
    ("way filed from its max lat only", CORPUS, WAY_LAT, WAY_LAT.replace("cell_of(min(lats))", "cell_of(max(lats))")),
    ("way filed from its min lat only", CORPUS, WAY_LAT, WAY_LAT.replace("cell_of(max(lats)) + 1", "cell_of(min(lats)) + 1")),
    ("way lat cells end exclusive", CORPUS, WAY_LAT, WAY_LAT.replace(" + 1)", ")")),
    ("way filed from its max lon only", CORPUS, WAY_LON, WAY_LON.replace("cell_of(min(lons))", "cell_of(max(lons))")),
    ("way filed from its min lon only", CORPUS, WAY_LON, WAY_LON.replace("cell_of(max(lons)) + 1", "cell_of(min(lons)) + 1")),
    ("way lon cells end exclusive", CORPUS, WAY_LON, WAY_LON.replace(" + 1)", ")")),
    ("cell key filed (lon, lat)", CORPUS, FILE, FILE.replace("((i, j)", "((j, i)")),
    ("landmark reads no cell south", CORPUS, LM_LAT, LM_LAT.replace("cell_of(lat - MARGIN_DEG)", "cell_of(lat)")),
    ("landmark lat cells end exclusive", CORPUS, LM_LAT, LM_LAT.replace(" + 1)", ")")),
    ("landmark reads no cell west", CORPUS, LM_LON, LM_LON.replace("cell_of(lon - widen)", "cell_of(lon)")),
    ("landmark lon cells end exclusive", CORPUS, LM_LON, LM_LON.replace(" + 1)", ")")),
    ("landmark reads no cell east", CORPUS, LM_LON, LM_LON.replace("cell_of(lon + widen) + 1", "cell_of(lon) + 1")),
    ("lookup key (lon, lat)", CORPUS, LOOKUP, LOOKUP.replace("((i, j)", "((j, i)")),
    ("ele in metres", CORPUS, ELE, ELE.replace(" * 10)", ")")),
    ("ele truncated to whole metres", CORPUS, ELE, ELE.replace('round(lm["ele_m"] * 10)', 'round(lm["ele_m"]) * 10')),
    ("lat at e7", CORPUS, ROW, ROW.replace("round(lat * 1e5)", "round(lat * 1e7)")),
    ("lon at e4", CORPUS, ROW, ROW.replace("round(lon * 1e5)", "round(lon * 1e4)")),
    ("lat and lon columns swapped", CORPUS, ROW,
     ROW.replace("round(lat * 1e5),\n                     round(lon * 1e5)",
                 "round(lon * 1e5),\n                     round(lat * 1e5)")),
    ("nearest measured at (lon, lat)", CORPUS, ROW, ROW.replace("nearest_way_id((lat, lon)", "nearest_way_id((lon, lat)")),
    ("nearest over the last candidate only", CORPUS, ROW, ROW.replace("sorted(near)]", "sorted(near)][-1:]")),
    ("name dropped", CORPUS, ROW, ROW.replace('lm["name"], ele', 'None, ele')),
    ("kind fixed to peak", CORPUS, ROW, ROW.replace('lm["kind"]', '"peak"')),
    ("landmarks never selected", CORPUS, FOUND, "        found = []"),
    ("table never written", CORPUS, WRITE, "        writer.write_landmarks([])"),
    ("CLI flag not passed to build", CORPUS, CLI, CLI.replace(", landmarks_osm=args.landmarks_osm)", ")")),
    ("writer drops the first row", WRITER, INSERT, INSERT.replace("sorted(rows, key=lambda row: (row[0], row[1]))",
                                                                  "sorted(rows, key=lambda row: (row[0], row[1]))[1:]")),
    ("digest blind to landmarks", DIGEST, SELECT, ""),
    ("digest blind to the key (osm_type, osm_id)", DIGEST, SELECT, digest_without("osm_type", "osm_id")),
] + [
    ("digest blind to %s" % column, DIGEST, SELECT, digest_without(column)) for column in DIGEST_COLUMNS
] + [
    ("digest loses precision on %s" % column, DIGEST, SELECT, digest_reading(column, "%s / 10" % column))
    for column in LOSSY_INTEGERS
] + [
    ("digest truncates name", DIGEST, SELECT, digest_reading("name", "substr(name, 1, 8)")),
] + [
    ("digest reads %s" % expression, DIGEST, SELECT, digest_reading(column, expression))
    for column, expression in LOSSY_READS
] + [
    ("digest reads lat_e5 and lon_e5 swapped", DIGEST, SELECT, SELECT.replace("lat_e5, lon_e5", "lon_e5, lat_e5")),
] + [
    ("region build passes no landmarks", STAGE, FLAG,
     '                        "--built-at", BUILT_AT, "--region", layout.region])'),
]

EQUIVALENT = [
    ("cell size doubled: CELL_DEG only sets how ways are binned; every way is filed under each cell its bbox "
     "touches and a landmark reads every cell its MARGIN_DEG box touches, so the candidates stay a superset of "
     "the ways within NEAR_M for any CELL_DEG > 0 and landmarks.nearest_way_id decides alone - the stored rows "
     "are identical, only the candidate count moves",
     CORPUS, "CELL_DEG = 0.01\n", "CELL_DEG = 0.02\n"),
    ("no 1/cos widening: 0.01 deg of longitude is 921 m at 34 N (LA) and 885 m at 37.3 N (the Bay Area), three "
     "times NEAR_M, so every fixture and served region keeps a superset; the widening only matters poleward of "
     "74 deg, where 0.01 deg of longitude falls under 300 m",
     CORPUS, WIDEN, "        widen = MARGIN_DEG"),
    ("digest landmarks SELECT without ORDER BY: schema.py statement 19 is PRIMARY KEY (osm_type, osm_id) WITHOUT "
     "ROWID with no secondary index, so the table is one b-tree keyed (osm_type, osm_id) and the only plan for "
     "the unordered full scan walks it in key order - the rows reach the hash in the same sequence",
     DIGEST, SELECT, UNORDERED),
    ("digest reads lon_e5 as REAL: schema.py statement 19 CHECKs lon_e5 BETWEEN -18000000 AND 18000000, at most 8 "
     "digits, and render_field prints a REAL with format(value, '.9g'), so CAST(lon_e5 AS REAL) renders the same "
     "digits as the INTEGER (-11855000.0 -> '-11855000', 18000000.0 -> '18000000') - the serialisation is unchanged",
     DIGEST, SELECT, digest_reading("lon_e5", "CAST(lon_e5 AS REAL)")),
]
KNOWN_MISSED = []

MIN_MUTATIONS = 50
harness.PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"] + [str(path) for path in EMPTIED]


def main(argv: list | None = None) -> int:
    only = mutate_only.select_only(sys.argv[1:] if argv is None else argv,
                                   [m[0] for m in list(MUTATIONS) + list(EQUIVALENT)], substring=True,
                                   split=False)
    parser = argparse.ArgumentParser(allow_abbrev=False, prog="ops/mutate/landmarkstable.py",
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

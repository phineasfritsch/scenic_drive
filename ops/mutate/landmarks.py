#!/usr/bin/env python3
"""Mutation harness AND population for etl/landmarks.py (T-0241, ruling R11).

WHY IT HAS ONE. `landmarks.select` parses elevations, rounds points and refuses objects; `explain` and
`nearest_way_id` compare distances against a 300 m bound and order what they find. It computes, so CLAUDE.md's
Verification section and P-PROC-06 say it ships a population with a literal floor.

THE CONTRACT is ops/mutate/extractadapter.py's, kept identically (see ops/mutate/placeallow.py): verbatim
anchors or SKIP-and-fail, a catch needs a NAMED TEST failing, the subject / emptied tests / this file are
compared to `git show HEAD:` before and after, MIN_MUTATIONS EQUALS the population, an EQUIVALENT that is
caught is a failure, `--prove-vacuity` empties the tests and requires every mutation MISSED, `--only` runs
a named subset. Every `__pycache__` under services/etl is purged before each run (the whole-second mtime).
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
SUBJECT = ETL / "etl" / "landmarks.py"
TESTS = ETL / "tests" / "test_landmarks.py"
ROUTE_TESTS = ETL / "tests" / "test_landmarks_route.py"
EMPTIED = (TESTS, ROUTE_TESTS)
SUBJECTS = (SUBJECT,)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/landmarks.py",)
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

KINDS = 'KINDS = ("viewpoint", "peak")'
ELE = r'ELE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(m|ft)?")'
IS_STR = "    if not isinstance(raw, str):"
FULL = "    match = ELE.fullmatch(raw.strip())"
UNIT = "    if match.group(2) == FOOT:"
SCALE = "        value = value * FOOT_M"
ROUND_ELE = "    return round(value, ELE_DP)"
KIND_GATE = "    if row is None or row.cls not in KINDS:"
NODE_IDS = '    if osm_type == "n":\n        return [osm_id]'
ACCESS = "        if tags.get(placeallow.ACCESS_KEY) in placeallow.REFUSED_ACCESS:"
REFUSED = '            counts["refused_access"] += 1'
SKIPPED = '            counts["skipped_geometry"] += 1'
FOUND = "        found.append((osm_type, osm_id, kind, placeallow.name_of(tags), elevation_m(tags.get(ELE_KEY))))"
POINT = '"lat": round(lat, COORD_DP), "lon": round(lon, COORD_DP)}'
SORT = '    landmarks.sort(key=lambda lm: ("nwr".index(lm["osm_type"]), lm["osm_id"]))'
NAMED = '    counts["named"] = sum(1 for lm in landmarks if lm["name"] is not None)'
WAY_BOUND = "        if distance <= NEAR_M and (best is None or (distance, way_id) < best):"
WAY_RETURN = "    return None if best is None else best[1]"
EMPTY_ROUTE = "    if not route:\n        return []"
LEGS = "    legs = list(zip(route, route[1:])) or [(route[0], route[0])]"
UNNAMED = '        if lm["name"] is None:\n            continue'
NEAREST_LEG = "        distance, leg = min((geom.point_to_segment_m(point, a, b), i) for i, (a, b) in enumerate(legs))"
ROUTE_BOUND = "        if distance <= NEAR_M:\n            hits.append("
HIT = '            hits.append((leg, distance, lm["osm_id"], lm["name"]))'
ORDER = "    for _leg, _distance, _osm_id, name in sorted(hits):"
SAID = "        said.add(name.casefold())"
SEEN = "        if name.casefold() in said:"
CAP = "    return names[:MAX_NAMED]"

MUTATIONS = [
    ("viewpoints dropped", SUBJECT, KINDS, 'KINDS = ("peak",)'),
    ("peaks dropped", SUBJECT, KINDS, 'KINDS = ("viewpoint",)'),
    ("waterfalls admitted", SUBJECT, KINDS, 'KINDS = ("viewpoint", "peak", "waterfall")'),
    ("six decimal places", SUBJECT, "COORD_DP = 5", "COORD_DP = 6"),
    ("four decimal places", SUBJECT, "COORD_DP = 5", "COORD_DP = 4"),
    ("ele to 0.01 m", SUBJECT, "ELE_DP = 1", "ELE_DP = 2"),
    ("ele to whole metres", SUBJECT, "ELE_DP = 1", "ELE_DP = 0"),
    ("a foot a little long", SUBJECT, "FOOT_M = 0.3048", "FOOT_M = 0.305"),
    ("feet read as metres", SUBJECT, "FOOT_M = 0.3048", "FOOT_M = 1.0"),
    ("299 m", SUBJECT, "NEAR_M = 300.0", "NEAR_M = 299.0"),
    ("301 m", SUBJECT, "NEAR_M = 300.0", "NEAR_M = 301.0"),
    ("500 m - Saddle Peak rescued", SUBJECT, "NEAR_M = 300.0", "NEAR_M = 500.0"),
    ("one name", SUBJECT, "MAX_NAMED = 2", "MAX_NAMED = 1"),
    ("three names", SUBJECT, "MAX_NAMED = 2", "MAX_NAMED = 3"),
    ("no negative ele", SUBJECT, ELE, ELE.replace("(-?", "(")),
    ("a leading plus accepted", SUBJECT, ELE, ELE.replace("(-?", "([-+]?")),
    ("a trailing dot accepted", SUBJECT, ELE, ELE.replace(r"(?:\.\d+)?", r"(?:\.\d*)?")),
    ("comma decimals accepted", SUBJECT, ELE, ELE.replace(r"(?:\.\d+)?", r"(?:[.,]\d+)?")),
    ("one space at most", SUBJECT, ELE, ELE.replace(r")\s*(m", r") ?(m")),
    ("a unit required", SUBJECT, ELE, ELE.replace("(m|ft)?", "(m|ft)")),
    ("upper-case units accepted", SUBJECT, ELE, ELE.replace("(m|ft)?", "(m|ft|M|FT)?")),
    ("km read as metres", SUBJECT, ELE, ELE.replace("(m|ft)?", "(km|m|ft)?")),
    ("the type check gone", SUBJECT, IS_STR, "    if raw is None:"),
    ("a prefix match", SUBJECT, FULL, "    match = ELE.match(raw.strip())"),
    ("a search", SUBJECT, FULL, "    match = ELE.search(raw.strip())"),
    ("no strip", SUBJECT, FULL, "    match = ELE.fullmatch(raw)"),
    ("feet never converted", SUBJECT, UNIT, "    if False:"),
    ("metres converted as feet", SUBJECT, UNIT, "    if match.group(2) != FOOT:"),
    ("feet divided", SUBJECT, SCALE, "        value = value / FOOT_M"),
    ("ele unrounded", SUBJECT, ROUND_ELE, "    return value"),
    ("every allowlisted class a landmark", SUBJECT, KIND_GATE, "    if row is None:"),
    ("a node located as a way", SUBJECT, NODE_IDS, '    if osm_type == "n":\n        return ways.get(osm_id)'),
    ("access never refused", SUBJECT, ACCESS, "        if False:"),
    ("access=no admitted", SUBJECT, ACCESS, '        if tags.get(placeallow.ACCESS_KEY) == "private":'),
    ("access refusal uncounted", SUBJECT, REFUSED, '            counts["refused_access"] += 0'),
    ("geometry skip uncounted", SUBJECT, SKIPPED, '            counts["skipped_geometry"] += 0'),
    ("a blank name kept", SUBJECT, FOUND, FOUND.replace("placeallow.name_of(tags)", 'tags.get("name")')),
    ("ele never read", SUBJECT, FOUND, FOUND.replace("elevation_m(tags.get(ELE_KEY))", "None")),
    ("points unrounded", SUBJECT, POINT, '"lat": lat, "lon": lon}'),
    ("lat and lon swapped", SUBJECT, POINT, '"lat": round(lon, COORD_DP), "lon": round(lat, COORD_DP)}'),
    ("unsorted", SUBJECT, SORT, "    pass"),
    ("sorted backwards", SUBJECT, SORT, SORT.replace("]))", "]), reverse=True)")),
    ("named counts every landmark", SUBJECT, NAMED, '    counts["named"] = len(landmarks)'),
    ("nearest way bound exclusive", SUBJECT, WAY_BOUND, WAY_BOUND.replace("<= NEAR_M", "< NEAR_M")),
    ("nearest way ties keep the first seen", SUBJECT, WAY_BOUND,
     WAY_BOUND.replace("(distance, way_id) < best", "distance < best[0]")),
    ("nearest way is the farthest", SUBJECT, WAY_BOUND,
     WAY_BOUND.replace("(distance, way_id) < best", "(distance, way_id) > best")),
    ("nearest way unbounded", SUBJECT, WAY_BOUND, WAY_BOUND.replace("distance <= NEAR_M and ", "")),
    ("nearest way returns its distance", SUBJECT, WAY_RETURN, "    return None if best is None else best[0]"),
    ("an empty route not short-circuited", SUBJECT, EMPTY_ROUTE, "    pass"),
    ("a one-point route has no legs", SUBJECT, LEGS, "    legs = list(zip(route, route[1:]))"),
    ("unnamed landmarks named", SUBJECT, UNNAMED, '        if False:\n            continue'),
    ("the farthest leg measured", SUBJECT, NEAREST_LEG, NEAREST_LEG.replace("min(", "max(")),
    ("route bound exclusive", SUBJECT, ROUTE_BOUND, ROUTE_BOUND.replace("<= NEAR_M", "< NEAR_M")),
    ("route bound gone", SUBJECT, ROUTE_BOUND, ROUTE_BOUND.replace("distance <= NEAR_M", "True")),
    ("ordered by distance, not by route position", SUBJECT, HIT,
     '            hits.append((distance, leg, lm["osm_id"], lm["name"]))'),
    ("ties ordered by id, not distance", SUBJECT, HIT,
     '            hits.append((leg, lm["osm_id"], distance, lm["name"]))'),
    ("unordered", SUBJECT, ORDER, "    for _leg, _distance, _osm_id, name in hits:"),
    ("ordered backwards", SUBJECT, ORDER, "    for _leg, _distance, _osm_id, name in sorted(hits, reverse=True):"),
    ("a repeated name said twice", SUBJECT, SEEN, "        if False:"),
    ("repeats compared case-sensitively", SUBJECT, SAID, "        said.add(name)"),
    ("no cap", SUBJECT, CAP, "    return names"),
]

EQUIVALENT = [
    ("node_ids_of's way branch widened to every non-node - kind_of returns None for every relation (no "
     "ALLOWLIST row of KINDS carries 'r', pinned by test_landmark_types_are_placeallows_rows), so select never "
     "asks node_ids_of about one", SUBJECT, '    if osm_type == "w":\n        return ways.get(osm_id)',
     '    if osm_type != "n":\n        return ways.get(osm_id)'),
]
KNOWN_MISSED = []

MIN_MUTATIONS = 61
harness.PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"] + [str(path) for path in EMPTIED]


def main(argv: list | None = None) -> int:
    only = mutate_only.select_only(sys.argv[1:] if argv is None else argv,
                                   [m[0] for m in list(MUTATIONS) + list(EQUIVALENT)], substring=True,
                                   split=False)
    parser = argparse.ArgumentParser(allow_abbrev=False, prog="ops/mutate/landmarks.py",
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

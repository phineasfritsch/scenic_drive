"""The mutation population of services/etl/etl/curated.py and curatedslice.py (T-0183), run by ops/mutate/curated.py.

Each entry is `(name, file, old, new)`; `old` must occur VERBATIM in the pristine subject or the run reports SKIP
and fails. A catch is a NAMED test failing in tests/test_curated_schema.py or tests/test_curated_la.py.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ETL = ROOT / "services" / "etl"
CURATED = ETL / "etl" / "curated.py"
SLICE = ETL / "etl" / "curatedslice.py"
SUBJECTS = (CURATED, SLICE)
TESTS = (ETL / "tests" / "test_curated_schema.py", ETL / "tests" / "test_curated_la.py")

RANGE = "    if not low <= value <= high:"
DATE = "    return isinstance(value, datetime.date) and not isinstance(value, datetime.datetime)"
JOIN_SHAPE = "    if not isinstance(value, dict) or len(value) != 1:"
JOIN_MATCH = "    if not isinstance(ref, str) or JOIN_PATTERNS[key].fullmatch(ref) is None:"
NEAREST = "        if d <= RADIUS_M and (best is None or (d, way[\"way_id\"]) < best[:2]):"
GATE = "    if way.get(\"scenic_gate\") is not None or way.get(\"scenic_refused\") is not None:"
HIGHWAY = "            if \"highway\" not in tags or any(r not in nodes for r in refs) or not refs:"

MUTATIONS = [
    # --- curated.py: the literal bounds -----------------------------------------------------------------
    ("let a 91-character hook through", CURATED, "HOOK_MAX = 90", "HOOK_MAX = 91"),
    ("lower the curation floor to 0.5", CURATED, "SCORE_MIN = 0.6", "SCORE_MIN = 0.5"),
    ("raise the curation ceiling past 1.0", CURATED, "SCORE_MAX = 1.0", "SCORE_MAX = 1.1"),
    ("let a 4-minute dwell through", CURATED, "DWELL_MIN = 5", "DWELL_MIN = 4"),
    ("let a 181-minute dwell through", CURATED, "DWELL_MAX = 180", "DWELL_MAX = 181"),
    ("call a 366-day-old desk check fresh", CURATED, "FRESH_DAYS = 365", "FRESH_DAYS = 366"),
    ("accept a sixth decimal place", CURATED, "COORD_DP = 5", "COORD_DP = 6"),
    # --- curated.py: the comparisons ---------------------------------------------------------------------
    ("refuse a coordinate exactly on the bbox minimum", CURATED, RANGE, "    if not low < value <= high:"),
    ("refuse a coordinate exactly on the bbox maximum", CURATED, RANGE, "    if not low <= value < high:"),
    ("accept a timestamp as a verified_on date", CURATED, DATE, "    return isinstance(value, datetime.date)"),
    ("accept a verified_on in the future", CURATED, "    elif verified > today:", "    elif False:"),
    ("accept 1 as hours_exempt", CURATED, "    if not isinstance(seed[\"hours_exempt\"], bool):",
     "    if seed[\"hours_exempt\"] not in (True, False):"),
    ("accept any category", CURATED, "    if seed[\"category\"] not in placeallow.CLASSES:",
     "    if not seed[\"category\"]:"),
    ("accept a blank hook", CURATED, "    if not _text(hook) or len(hook) > HOOK_MAX:",
     "    if not isinstance(hook, str) or len(hook) > HOOK_MAX:"),
    ("accept a join with no key", CURATED, JOIN_SHAPE, "    if not isinstance(value, dict) or len(value) > 1:"),
    ("accept osm id 0", CURATED, "(node|way|relation)/[1-9][0-9]*", "(node|way|relation)/[0-9]+"),
    ("accept a join that only starts well-formed", CURATED, JOIN_MATCH,
     "    if not isinstance(ref, str) or JOIN_PATTERNS[key].match(ref) is None:"),
    ("accept an id that only starts as a slug", CURATED, "SLUG.fullmatch(seed[\"id\"])", "SLUG.match(seed[\"id\"])"),
    ("ignore an unknown seed field", CURATED, "    unknown = sorted(str(k) for k in seed if k not in FIELDS)",
     "    unknown = []"),
    ("ignore an unknown top-level key", CURATED, "    unknown = sorted(str(k) for k in doc if k not in TOP_KEYS)",
     "    unknown = []"),
    ("load another region's file", CURATED, "    if \"region\" in doc and doc[\"region\"] != region_id:",
     "    if False:"),
    ("accept an empty seed list", CURATED, "(not isinstance(seeds, list) or not seeds)",
     "(not isinstance(seeds, list))"),
    ("accept a duplicated id", CURATED, "if ids.count(i) > 1", "if ids.count(i) > 2"),
    ("load a file with problems", CURATED, "    if found:\n        raise", "    if False:\n        raise"),
    ("call a future date fresh", CURATED, "    return 0 <= (today - seed[\"verified_on\"]).days <= FRESH_DAYS",
     "    return (today - seed[\"verified_on\"]).days <= FRESH_DAYS"),
    # --- curated.py: the join ----------------------------------------------------------------------------
    ("join a way id against nodes", CURATED, "\"way\": \"w\"", "\"way\": \"n\""),
    ("join without checking the name", CURATED, "    return (name == seed[\"name\"] and", "    return (True and"),
    ("join without checking the latitude", CURATED, "round(lat_e7 / 1e7, COORD_DP) == seed[\"lat\"]", "True"),
    ("join without checking the longitude", CURATED, "round(lon_e7 / 1e7, COORD_DP) == seed[\"lon\"]", "True"),
    ("drop the hours-exempt arm of the plan predicate", CURATED,
     "    return joined(seed, conn) or seed[\"hours_exempt\"] is True", "    return joined(seed, conn)"),
    # --- curatedslice.py ---------------------------------------------------------------------------------
    ("widen the approach radius to 301 m", SLICE, "RADIUS_M = 300.0", "RADIUS_M = 301.0"),
    ("lower the score floor to 0.45", SLICE, "MIN_UNIT = 0.5", "MIN_UNIT = 0.45"),
    ("refuse a way scoring exactly 0.5", SLICE, "    return unit >= MIN_UNIT", "    return unit > MIN_UNIT"),
    ("pass a refused way", SLICE, GATE, "    if way.get(\"scenic_gate\") is not None:"),
    ("pass a gated way", SLICE, GATE, "    if way.get(\"scenic_refused\") is not None:"),
    ("take any road as the approach, whatever its name", SLICE,
     "        if way.get(\"name\") != seed[\"approach_hint\"]:\n            continue",
     "        if False:\n            continue"),
    ("take the farthest named way", SLICE, NEAREST,
     "        if d <= RADIUS_M and (best is None or d > best[0]):"),
    ("break a tie by the higher way_id", SLICE, NEAREST,
     "        if d <= RADIUS_M and (best is None or (d, -way[\"way_id\"]) < (best[0], -best[1])):"),
    ("pass any approach road that exists", SLICE, "    return way is not None and passes(way)",
     "    return way is not None"),
    ("measure from a swapped seed point", SLICE, "(seed[\"lon\"], seed[\"lat\"])", "(seed[\"lat\"], seed[\"lon\"])"),
    ("keep only ways near every seed", SLICE, "if any(distance_m(s, w) <= RADIUS_M for s in seeds)",
     "if all(distance_m(s, w) <= RADIUS_M for s in seeds)"),
    ("keep ways that are not highways", SLICE, HIGHWAY,
     "            if any(r not in nodes for r in refs) or not refs:"),
    ("write the slice in insertion order", SLICE, "json.dumps(doc, sort_keys=True,", "json.dumps(doc, sort_keys=False,"),
    ("record the input's sha1", SLICE, "hashlib.sha256(args.input", "hashlib.sha1(args.input"),
    ("cut a slice from a refused curated file", SLICE, "        return 2\n", "        return 0\n"),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE. The witness is in the name.
EQUIVALENT = [
    ("count rows with `not rows` - the places_by_osm UNIQUE index on (osm_type, osm_id) holds a lookup to 0 or 1 "
     "rows, so len(rows) != 1 and not rows agree on every table the corpus writer can build", CURATED,
     "    if len(rows) != 1:", "    if not rows:"),
    ("accept a YAML true as an int - _is_int guards only dwell_min, and True == 1 and False == 0 both lie below "
     "the literal DWELL_MIN = 5, so the range check refuses a bool whichever function let it through", CURATED,
     "    return isinstance(value, int) and not isinstance(value, bool)", "    return isinstance(value, int)"),
]

KNOWN_MISSED = []

MIN_MUTATIONS = 45

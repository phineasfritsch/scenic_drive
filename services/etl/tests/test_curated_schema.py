"""curated.yaml's schema, every bound tabled both ways, through the shipping `curated.load` (T-0183 R6).

Each row writes a one-seed curated.yaml beside a copy of the real LA region.json and loads it, so the YAML
parse, the region bbox read and the schema check are the code that judges the real file. A refused row must
also NAME the field it broke, so a value refused for the wrong reason is not counted as a pass.
"""
import datetime
import math
import shutil

import pytest
import yaml

from etl import curated, placeallow, region

TODAY = datetime.date(2026, 10, 16)
VALID = {
    "id": "stunt-road-viewpoint", "name": "Stunt Road Viewpoint", "hook": "A ridge road",
    "lat": 34.08133, "lon": -118.6455, "join": {"osm": "node/12073372395"}, "category": "viewpoint",
    "hours_exempt": True, "dwell_min": 10, "approach_hint": "Saddle Peak Road", "verified_on": TODAY,
    "curation_score": 0.9, "notes": "Desk-verified from OSM data, not visited.",
}
BBOX = region.load("la").bbox
HEX32, HEX24 = "0123456789abcdef" * 2, "0123456789abcdef01234567"

# (field, value, accepted)
BOUNDS = [
    ("hook", "x" * curated.HOOK_MAX, True), ("hook", "x" * (curated.HOOK_MAX + 1), False),
    ("hook", "x", True), ("hook", "", False), ("hook", "   ", False), ("hook", 5, False),
    ("lat", BBOX.min_lat, True), ("lat", BBOX.max_lat, True),
    ("lat", round(BBOX.min_lat - 1e-5, 5), False), ("lat", round(BBOX.max_lat + 1e-5, 5), False),
    ("lat", math.nextafter(BBOX.min_lat, 0.0), False), ("lat", math.nextafter(BBOX.max_lat, 90.0), False),
    ("lat", 34.123456, False), ("lat", 34, False), ("lat", True, False), ("lat", math.nan, False),
    ("lat", math.inf, False), ("lat", "34.1", False), ("lat", None, False),
    ("lon", BBOX.min_lon, True), ("lon", BBOX.max_lon, True),
    ("lon", round(BBOX.min_lon - 1e-5, 5), False), ("lon", round(BBOX.max_lon + 1e-5, 5), False),
    ("lon", -118.123456, False), ("lon", -118, False), ("lon", -math.inf, False), ("lon", False, False),
    ("curation_score", curated.SCORE_MIN, True), ("curation_score", curated.SCORE_MAX, True),
    ("curation_score", math.nextafter(curated.SCORE_MIN, 0.0), False),
    ("curation_score", math.nextafter(curated.SCORE_MAX, 2.0), False),
    ("curation_score", 0.59999, False), ("curation_score", 1, False), ("curation_score", True, False),
    ("curation_score", math.nan, False), ("curation_score", "0.8", False), ("curation_score", None, False),
    ("dwell_min", curated.DWELL_MIN, True), ("dwell_min", curated.DWELL_MAX, True),
    ("dwell_min", curated.DWELL_MIN - 1, False), ("dwell_min", curated.DWELL_MAX + 1, False),
    ("dwell_min", 10.0, False), ("dwell_min", True, False), ("dwell_min", "10", False), ("dwell_min", None, False),
    ("hours_exempt", True, True), ("hours_exempt", False, True), ("hours_exempt", 1, False),
    ("hours_exempt", "true", False), ("hours_exempt", None, False),
    ("category", "restaurant", False), ("category", "Viewpoint", False), ("category", None, False),
    ("verified_on", TODAY, True), ("verified_on", TODAY - datetime.timedelta(days=400), True),
    ("verified_on", TODAY + datetime.timedelta(days=1), False), ("verified_on", "2026-10-16", False),
    ("verified_on", datetime.datetime(2026, 10, 16, 12, 0), False), ("verified_on", None, False),
    ("id", "a", True), ("id", "a-b-1", True), ("id", "A", False), ("id", "a_b", False), ("id", "-a", False),
    ("id", "a-", False), ("id", "a--b", False), ("id", "", False), ("id", 5, False),
    ("name", "", False), ("name", "  ", False), ("name", None, False),
    ("approach_hint", "", False), ("approach_hint", None, False), ("notes", "", False), ("notes", 3, False),
    ("join", {"osm": "node/1"}, True), ("join", {"osm": "way/422130705"}, True),
    ("join", {"osm": "relation/7"}, True), ("join", {"osm": "node/0"}, False), ("join", {"osm": "nodes/1"}, False),
    ("join", {"osm": "node/1x"}, False), ("join", {"osm": "n/1"}, False), ("join", {"osm": 1}, False),
    ("join", {"gers_id": HEX32}, True), ("join", {"gers_id": HEX32[:-1]}, False),
    ("join", {"gers_id": HEX32.upper()}, False), ("join", {"fsq_place_id": HEX24}, True),
    ("join", {"fsq_place_id": HEX24 + "0"}, False), ("join", {"osm": "node/1", "gers_id": HEX32}, False),
    ("join", {}, False), ("join", {"osm_id": "node/1"}, False), ("join", "node/1", False),
] + [("category", cls, True) for cls in placeallow.CLASSES]


def write(tmp_path, doc):
    (tmp_path / "la").mkdir(exist_ok=True)
    shutil.copy(region.REGIONS / "la" / "region.json", tmp_path / "la" / "region.json")
    text = doc if isinstance(doc, str) else yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
    (tmp_path / "la" / curated.FILENAME).write_text(text, encoding="utf-8")


def refusal(tmp_path, doc):
    """None when the shipping loader accepts `doc`, else its problems - the text after the path line, which
    holds the tmp directory and so the test's own name."""
    write(tmp_path, doc)
    try:
        curated.load("la", TODAY, tmp_path)
    except curated.CurationError as err:
        return str(err).split("\n", 1)[1]
    return None


def one(seed):
    return {"region": "la", "seeds": [seed]}


def test_the_valid_seed_is_accepted(tmp_path):
    write(tmp_path, one(VALID))
    assert curated.load("la", TODAY, tmp_path) == [VALID]


@pytest.mark.parametrize("field,value,accepted", BOUNDS, ids=["%s=%r" % (f, v) for f, v, _ in BOUNDS])
def test_every_bound(tmp_path, field, value, accepted):
    err = refusal(tmp_path, one(dict(VALID, **{field: value})))
    if accepted:
        assert err is None
    else:
        assert err is not None and field in err


def test_every_field_is_required(tmp_path):
    for field in curated.FIELDS:
        seed = {k: v for k, v in VALID.items() if k != field}
        err = refusal(tmp_path, one(seed))
        assert err is not None and "missing field(s) ['%s']" % field in err, field


def test_an_unknown_field_is_refused(tmp_path):
    err = refusal(tmp_path, one(dict(VALID, golden_hour=True)))
    assert err is not None and "unknown field(s) ['golden_hour']" in err


TOP = [
    ("missing region", {"seeds": [VALID]}, "missing top-level key(s) ['region']"),
    ("missing seeds", {"region": "la"}, "missing top-level key(s) ['seeds']"),
    ("unknown key", {"region": "la", "seeds": [VALID], "extra": 1}, "unknown top-level key(s) ['extra']"),
    ("other region", {"region": "sfbay", "seeds": [VALID]}, "region 'sfbay' is not 'la'"),
    ("empty seeds", {"region": "la", "seeds": []}, "seeds is not a non-empty list"),
    ("seeds a mapping", {"region": "la", "seeds": VALID}, "seeds is not a non-empty list"),
    ("seed a string", {"region": "la", "seeds": ["x"]}, "a seed is not a mapping"),
    ("doc a list", [VALID], "curated.yaml is not a mapping"),
    ("doc empty", "", "curated.yaml is not a mapping"),
    ("duplicate id", {"region": "la", "seeds": [VALID, VALID]}, "id 'stunt-road-viewpoint' appears more than once"),
]


@pytest.mark.parametrize("label,doc,named", TOP, ids=[t[0] for t in TOP])
def test_the_top_level(tmp_path, label, doc, named):
    err = refusal(tmp_path, doc)
    assert err is not None and named in err, label


FRESH = [(0, True), (curated.FRESH_DAYS, True), (curated.FRESH_DAYS + 1, False), (-1, False)]


@pytest.mark.parametrize("age_days,ok", FRESH)
def test_fresh_bounds(age_days, ok):
    seed = dict(VALID, verified_on=TODAY - datetime.timedelta(days=age_days))
    assert curated.fresh(seed, TODAY) is ok

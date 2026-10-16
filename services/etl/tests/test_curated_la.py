"""The plan's Curation pytest over the SHIPPED regions/la/curated.yaml (T-0183).

Three named predicates, each over committed data: the LA places table the app bundles (the join), the
committed slice of the LA tagged PBF (the approach road, rulings R3/R4) and today's date (freshness, R5).
Each has a refusal table beside it so the predicate is seen deciding, not only passing.
"""
import datetime
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from etl import curated, curatedslice, region
from regionbuild import places

TODAY = datetime.date.today()
SEEDS = curated.load("la", TODAY)
PLACES = places.REPO / places.BUNDLE["la"][0]
SLICE = Path(__file__).resolve().parent / "fixtures" / "la_curated_approach.json"


@pytest.fixture(scope="module")
def conn():
    db = sqlite3.connect("file:%s?mode=ro" % PLACES.as_posix(), uri=True)
    yield db
    db.close()


def test_the_la_file_holds_the_five_seeds():
    assert [s["id"] for s in SEEDS] == ["stunt-road-viewpoint", "top-of-topanga-overlook", "stone-canyon-overlook",
                                        "griffith-observatory", "calabasas-peak-trailhead"]


def test_every_seed_joins_exactly_one_place_or_is_hours_exempt(conn):
    assert [s["id"] for s in SEEDS if not curated.joins_or_exempt(s, conn)] == []


def test_every_la_seed_joins_its_place_by_name_and_coordinate(conn):
    assert [s["id"] for s in SEEDS if not curated.joined(s, conn)] == []


def test_approach_road_within_300_m_passes_the_gate_and_scores_at_least_half():
    doc = json.loads(SLICE.read_text(encoding="utf-8"))
    assert doc["seeds"] == curatedslice.seed_points(SEEDS), "the slice was cut for other seeds - re-cut it"
    assert doc["radius_m"] == curatedslice.RADIUS_M
    assert [s["id"] for s in SEEDS if not curatedslice.approach_ok(s, doc["ways"])] == []


def test_the_committed_slice_is_the_cutters_own_encoding():
    text = SLICE.read_text(encoding="utf-8")
    doc = json.loads(text)
    assert text == curatedslice.encode(doc["source_sha256"], SEEDS, doc["ways"])
    assert doc["source_sha256"] == "163008e47d5fc59e6e3efe05cd7004f42d5ec7cd3732c8c7f056797ea933230c"


def test_verified_on_is_within_twelve_months():
    assert [s["id"] for s in SEEDS if not curated.fresh(s, TODAY)] == []


GRIFFITH = next(s for s in SEEDS if s["id"] == "griffith-observatory")
JOINS = [
    ("the shipped seed", {}, True, True),
    ("an id with no place, not exempt", {"join": {"osm": "way/1"}}, False, False),
    ("an id with no place, exempt", {"join": {"osm": "way/1"}, "hours_exempt": True}, False, True),
    ("the right id under the wrong type", {"join": {"osm": "node/422130705"}}, False, False),
    ("another place's id", {"join": {"osm": "node/5061361321"}}, False, False),
    ("a renamed seed", {"name": "Griffith Park Observatory"}, False, False),
    ("a coordinate one step off", {"lat": round(GRIFFITH["lat"] + 1e-5, 5)}, False, False),
    ("a gers join, not exempt", {"join": {"gers_id": "0" * 32}}, False, False),
    ("a gers join, exempt", {"join": {"gers_id": "0" * 32}, "hours_exempt": True}, False, True),
]


@pytest.mark.parametrize("label,change,joined,plan", JOINS, ids=[j[0] for j in JOINS])
def test_the_join_refuses_a_broken_seed(conn, label, change, joined, plan):
    seed = dict(GRIFFITH, **change)
    assert curated.joined(seed, conn) is joined
    assert curated.joins_or_exempt(seed, conn) is plan


SEED = {"lat": 34.1, "lon": -118.5, "approach_hint": "Canyon Road"}


def north_m(metres: float) -> float:
    """The latitude offset that puts a horizontal way `metres` from SEED by the shipping distance."""
    probe = 0.001
    d = curatedslice.distance_m(SEED, way(1, probe))
    return probe * metres / d


def way(way_id, dlat, name="Canyon Road", **tags):
    row = {"way_id": way_id, "highway": "tertiary", "name": name, "scenic_gate": None, "scenic_refused": None,
           "scenic_score_unit": "0.6000", "coords": [[-118.51, 34.1 + dlat], [-118.49, 34.1 + dlat]]}
    row.update(tags)
    return row


APPROACH = [
    ("ungated at 0.6", [way(1, 0.0001)], True),
    ("exactly 0.5", [way(1, 0.0001, scenic_score_unit="0.5000")], True),
    ("0.4999", [way(1, 0.0001, scenic_score_unit="0.4999")], False),
    ("gated", [way(1, 0.0001, scenic_gate="unpaved_surface")], False),
    ("refused", [way(1, 0.0001, scenic_refused="1", scenic_score_unit=None)], False),
    ("no unit", [way(1, 0.0001, scenic_score_unit=None)], False),
    ("unit nan", [way(1, 0.0001, scenic_score_unit="nan")], False),
    ("unit text", [way(1, 0.0001, scenic_score_unit="high")], False),
    ("only another name", [way(1, 0.0001, name="Other Road")], False),
    ("no ways", [], False),
    ("nearest named way is gated", [way(1, 0.0001, scenic_gate="track"), way(2, 0.0010)], False),
    ("nearest named way passes", [way(1, 0.0010, scenic_gate="track"), way(2, 0.0001)], True),
    ("a nearer other-named gated way", [way(1, 0.00001, name="Fire Road", scenic_gate="track"),
                                       way(2, 0.0010)], True),
    ("tie: lower way_id decides (bad)", [way(2, 0.0001), way(1, 0.0001, scenic_gate="track")], False),
    ("tie: lower way_id decides (good)", [way(1, 0.0001), way(2, 0.0001, scenic_gate="track")], True),
]


@pytest.mark.parametrize("label,ways,ok", APPROACH, ids=[a[0] for a in APPROACH])
def test_the_approach_refuses_a_broken_road(label, ways, ok):
    assert curatedslice.approach_ok(SEED, ways) is ok


@pytest.mark.parametrize("metres,ok", [(299.9, True), (300.1, False)])
def test_the_300_m_radius_both_sides(metres, ok):
    road = way(1, north_m(metres))
    assert abs(curatedslice.distance_m(SEED, road) - metres) < 0.01
    assert curatedslice.approach_ok(SEED, [road]) is ok


CLIP = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6">
<node id="1" lat="34.0814000" lon="-118.6460000"/>
<node id="2" lat="34.0814000" lon="-118.6450000"/>
<node id="3" lat="34.1000000" lon="-118.6000000"/>
<node id="4" lat="34.1000000" lon="-118.6010000"/>
<way id="20"><nd ref="3"/><nd ref="4"/><tag k="highway" v="tertiary"/></way>
<way id="10"><nd ref="1"/><nd ref="2"/><tag k="highway" v="tertiary"/><tag k="name" v="Saddle Peak Road"/>\
<tag k="scenic_score_unit" v="0.6446"/><tag k="surface" v="asphalt"/></way>
<way id="30"><nd ref="1"/><nd ref="2"/><tag k="building" v="yes"/></way>
<way id="40"><nd ref="1"/><nd ref="9"/><tag k="highway" v="service"/></way>
</osm>
"""


def test_the_shipped_cutter_writes_exactly_the_ways_within_300_m(tmp_path):
    (tmp_path / "la").mkdir()
    shutil.copy(region.REGIONS / "la" / "region.json", tmp_path / "la")
    shutil.copy(region.REGIONS / "la" / curated.FILENAME, tmp_path / "la")
    clip = tmp_path / "clip.osm.xml"
    clip.write_text(CLIP, encoding="utf-8", newline="\n")
    out = tmp_path / "slice.json"
    argv = ["--input", str(clip), "--region", "la", "--root", str(tmp_path), "--today", TODAY.isoformat(),
            "--out", str(out)]
    assert curatedslice.main(argv) == 0
    import hashlib
    expected = {"radius_m": 300.0, "seeds": curatedslice.seed_points(SEEDS),
                "source_sha256": hashlib.sha256(clip.read_bytes()).hexdigest(),
                "ways": [{"way_id": 10, "coords": [[-118.646, 34.0814], [-118.645, 34.0814]], "highway": "tertiary",
                          "name": "Saddle Peak Road", "scenic_gate": None, "scenic_refused": None,
                          "scenic_score_unit": "0.6446"}]}
    assert json.loads(out.read_text(encoding="utf-8")) == expected
    assert out.read_text(encoding="utf-8") == curatedslice.encode(expected["source_sha256"], SEEDS,
                                                                 expected["ways"])
    (tmp_path / "la" / curated.FILENAME).write_text("region: la\nseeds: []\n", encoding="utf-8")
    assert curatedslice.main(argv) == 2

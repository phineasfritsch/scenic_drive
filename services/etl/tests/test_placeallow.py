"""The extract's places array from the OSM allowlist (T-0266), through the SHIPPING entry point.

Every test runs `python -m etl.extractadapter --places-osm` (its `main`) over a committed fixture OSM XML or
a per-row XML written here, and reads the extract it wrote. Expected rows are typed literals, never the
module's own tables: the allowlist, the chain list and the osmium expressions are restated below by hand, so a
row dropped or changed in etl/placeallow.py turns a test red by name (rulings R2-R7 in the task Log).
"""
from __future__ import annotations

import json
import pathlib
import sqlite3

import pytest

from etl import corpus, extractadapter
from etl.extractplace import load_places

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "places_allowlist.osm.xml"
WAYDOC = {"region": "la", "ways": [{"way_id": 1, "tags": {"highway": "residential", "name": "Fixture Rd"},
                                    "coords": [[34.0, -118.0], [34.001, -118.001]]}]}

# The whole array, (osm_type, osm_id) ascending: cls, name, lat, lon.
EXPECTED = [
    ("n", 101, "viewpoint", "Inspiration Point", 34.09, -118.61),
    ("n", 111, "peak", "Saddle Peak", 34.0756, -118.6544),
    ("n", 113, "peak", "Castro Peak", 34.0861, -118.7856),
    ("n", 121, "waterfall", "Escondido Falls", 34.0333, -118.8667),
    ("n", 133, "beach", "Point Dume Beach", 34.001, -118.806),
    ("n", 135, "beach", "Topanga State Beach", 34.31, -118.69),
    ("n", 141, "trailhead", "Backbone Trailhead", 34.08, -118.7),
    ("n", 161, "cafe", "Topanga Living Cafe", 34.09, -118.6),
    ("n", 191, "town", "Pasadena", 34.1478, -118.1445),
    ("n", 192, "town", "Malibu", 34.0259, -118.7798),
    ("n", 193, "town", "Agoura", 34.1442, -118.7615),
    ("n", 221, "museum", "Museum Cafe", 34.1, -118.3),
    ("n", 223, "viewpoint", "Topanga Lookout", 34.11, -118.31),
    ("n", 225, "cafe", "Park Cafe", 34.12, -118.32),
    ("n", 233, "garden", "Open Garden", 34.13, -118.33),
    ("n", 234, "garden", "Patron Garden", 34.14, -118.34),
    ("n", 238, "cafe", "Starbucksy", 34.15, -118.35),
    ("n", 239, "cafe", "Bean Coffee House", 34.16, -118.36),
    ("n", 240, "cafe", "Coffee Beanery", 34.17, -118.37),
    ("n", 251, "park", "Glenoaks Park", 34.175, -118.265),
    ("n", 253, "park", "Sycamore Park", 34.195, -118.245),
    ("n", 255, "museum", "Autry", 34.905, -118.295),
    ("n", 257, "park", "Edge Park", 34.31, -118.39),
    ("n", 259, "park", "Near Park", 34.4100001, -118.39),
    ("n", 261, "park", "Low Park", 34.5, -118.4),
    ("n", 263, "park", "Under Park", 34.5999999, -118.4),
    ("n", 267, "park", "West Park", 34.705, -118.4000001),
    ("n", 269, "park", "East Park", 34.805, -118.3899999),
    ("w", 102, "viewpoint", "Mulholland Scenic Overlook", 34.15, -118.55),
    ("w", 131, "beach", "Zuma Beach", 34.02, -118.82),
    ("w", 151, "museum", "Getty Villa", 34.0463333, -118.5643333),
    ("w", 171, "garden", "Descanso Gardens", 34.2, -118.205),
    ("w", 181, "park", "Griffith Park", 34.135, -118.295),
    ("w", 256, "park", "Autry", 34.905, -118.295),
    ("w", 260, "park", "Near Park", 34.405, -118.395),
    ("w", 264, "park", "Under Park", 34.605, -118.395),
    ("w", 268, "park", "West Park", 34.705, -118.395),
    ("w", 270, "park", "East Park", 34.805, -118.395),
    ("r", 132, "beach", "Leo Carrillo Beach", 34.0366667, -118.9333333),
]
COUNT_LINE = ("PLACES places=39 unnamed=2 refused_access=4 chain=1 skipped_geometry=3 deduped=5 "
              "viewpoint=3 peak=2 waterfall=1 beach=4 trailhead=1 museum=3 cafe=5 garden=3 park=14 town=3")


def run_adapter(tmp_path, osm_xml, capsys=None):
    waydoc = tmp_path / "doc.json"
    waydoc.write_text(json.dumps(WAYDOC), encoding="utf-8")
    out = tmp_path / "extract.json"
    argv = ["--input", str(waydoc), "--out", str(out)]
    if osm_xml is not None:
        argv += ["--places-osm", str(osm_xml)]
    assert extractadapter.main(argv) == 0
    lines = capsys.readouterr().out.splitlines() if capsys else []
    return json.loads(out.read_text(encoding="utf-8")), out, lines


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("placeallow")
    doc, out, _ = run_adapter(tmp, FIXTURE)
    return doc, out


def rows(doc):
    return [(p["osm_type"], p["osm_id"], p["cls"], p["name"], p["lat"], p["lon"]) for p in doc["places"]]


def keys(doc):
    return {(p["osm_type"], p["osm_id"]) for p in doc["places"]}


def test_places_equal_the_fixture_exactly(built):
    assert rows(built[0]) == EXPECTED
    assert all(set(p) == {"osm_type", "osm_id", "cls", "name", "lat", "lon"} for p in built[0]["places"])


@pytest.mark.parametrize("osm_type,osm_id,cls", [
    ("n", 101, "viewpoint"), ("n", 111, "peak"), ("n", 121, "waterfall"), ("w", 131, "beach"),
    ("n", 141, "trailhead"), ("w", 151, "museum"), ("n", 161, "cafe"), ("w", 171, "garden"),
    ("w", 181, "park"), ("n", 191, "town"), ("n", 192, "town"), ("n", 193, "town"),
], ids=["tourism=viewpoint", "natural=peak", "waterway=waterfall", "natural=beach", "highway=trailhead",
        "tourism=museum", "amenity=cafe", "leisure=garden", "leisure=park", "place=city", "place=town",
        "place=village"])
def test_allowlist_row_admits_its_tag_as_its_class(built, osm_type, osm_id, cls):
    match = [r for r in rows(built[0]) if r[:2] == (osm_type, osm_id)]
    assert [r[2] for r in match] == [cls]


@pytest.mark.parametrize("osm_type,osm_id", [("w", 112), ("w", 122), ("w", 142), ("w", 194), ("r", 103)],
                         ids=["peak-way", "waterfall-way", "trailhead-way", "town-way", "viewpoint-relation"])
def test_an_object_type_outside_its_row_is_refused(built, osm_type, osm_id):
    assert (osm_type, osm_id) not in keys(built[0])


@pytest.mark.parametrize("osm_id", [201, 202], ids=["no-name", "blank-name"])
def test_an_unnamed_feature_is_refused(built, osm_id):
    assert ("n", osm_id) not in keys(built[0])


@pytest.mark.parametrize("osm_id,name", [(113, "Castro Peak"), (253, "Sycamore Park")],
                         ids=["spaces-both-sides", "leading-tab-trailing-space"])
def test_a_kept_name_is_emitted_stripped(built, osm_id, name):
    assert [r[3] for r in rows(built[0]) if r[:2] == ("n", osm_id)] == [name]


@pytest.mark.parametrize("osm_id", [211, 212, 213, 214],
                         ids=["natural=waterfall", "place=hamlet", "tourism=attraction", "leisure=nature_reserve"])
def test_a_tag_outside_the_allowlist_is_refused(built, osm_id):
    assert ("n", osm_id) not in keys(built[0])


@pytest.mark.parametrize("osm_id,cls", [(221, "museum"), (223, "viewpoint"), (225, "cafe")],
                         ids=["museum-before-cafe", "viewpoint-before-peak", "cafe-before-park"])
def test_the_first_matching_row_names_the_class(built, osm_id, cls):
    assert [r[2] for r in rows(built[0]) if r[:2] == ("n", osm_id)] == [cls]


@pytest.mark.parametrize("osm_type,osm_id,kept", [
    ("n", 231, False), ("n", 232, False), ("n", 233, True), ("n", 234, True), ("w", 235, False),
    ("r", 236, False),
], ids=["access=private", "access=no", "access=yes", "access=customers", "way-access=private",
        "relation-access=no"])
def test_access_private_or_no_refuses_and_nothing_else_does(built, osm_type, osm_id, kept):
    assert ((osm_type, osm_id) in keys(built[0])) is kept


# (brand, brand:wikidata, a measured LA spelling of the name) - restated by hand from the task Log.
CHAINS = [
    ("Starbucks", "Q37158", "Barns & Noble Starbucks"),
    ("The Coffee Bean & Tea Leaf", "Q1141384", "Coffee Bean and Tea Leaf"),
    ("Peet's Coffee", "Q1094101", "Peet's Coffee"),
    ("It's Boba Time", "Q119951349", "Its Boba Time"),
    ("85°C", "Q4644852", "85°C Bakery Cafe"),
    ("Blue Bottle Coffee", "Q4928917", "Blue Bottle - Playa Vista"),
    ("Ding Tea", "Q112123475", "Ding Tea"),
    ("Philz Coffee", "Q18156812", "Philz Coffee"),
    ("Corner Bakery", "Q5171598", "Corner Bakery"),
    ("7 Leaves Cafe", "Q118480682", "7 Leaves"),
    ("Le Pain Quotidien", "Q2046903", "Le Pain Quotidien"),
    ("Sharetea", "Q64827032", "Sharetea"),
    ("Joe & The Juice", "Q26221514", "Joe & The Juice"),
    ("Kreation Organic", "Q113363083", "Kreation Organic"),
    ("Tapioca Express", "Q23462008", "Tapioca Express"),
    ("Dutch Bros. Coffee", "Q5317253", "Dutch Bros. Coffee"),
    ("Quickly", "Q3771463", "Quickly"),
    ("Tastea", "Q122328236", "Tastea"),
]


def chain_xml(tmp_path, brand, qid, name):
    def cafe(osm_id, *tags):
        body = "".join('<tag k="%s" v="%s"/>' % (k, v.replace("&", "&amp;")) for k, v in tags)
        return '<node id="%d" lat="34.1" lon="-118.1"><tag k="amenity" v="cafe"/>%s</node>' % (osm_id, body)
    path = tmp_path / "chain.osm.xml"
    path.write_text("<?xml version='1.0' encoding='UTF-8'?>\n<osm version=\"0.6\">"
                    + cafe(1, ("brand:wikidata", qid), ("name", "Neutral One"))
                    + cafe(2, ("brand", brand.upper()), ("name", "Neutral Two"))
                    + cafe(3, ("name", name))
                    + cafe(4, ("name", "Neutral Control"))
                    + "</osm>\n", encoding="utf-8")
    return path


@pytest.mark.parametrize("brand,qid,name", CHAINS, ids=[c[1] for c in CHAINS])
def test_blocklist_row_refuses_by_wikidata_by_brand_and_by_name(tmp_path, capsys, brand, qid, name):
    doc, _, lines = run_adapter(tmp_path, chain_xml(tmp_path, brand, qid, name), capsys)
    assert rows(doc) == [("n", 4, "cafe", "Neutral Control", 34.1, -118.1)]
    assert lines[-1] == ("PLACES places=1 unnamed=0 refused_access=0 chain=3 skipped_geometry=0 deduped=0 "
                         "viewpoint=0 peak=0 waterfall=0 beach=0 trailhead=0 museum=0 cafe=1 garden=0 "
                         "park=0 town=0")


def test_the_blocklist_applies_to_every_class(built):
    assert ("n", 237) not in keys(built[0])


@pytest.mark.parametrize("osm_id", [238, 239, 240], ids=["Starbucksy", "Bean Coffee House", "Coffee Beanery"])
def test_a_chain_name_matches_whole_tokens_in_order_only(built, osm_id):
    assert ("n", osm_id) in keys(built[0])


@pytest.mark.parametrize("osm_type,osm_id", [("w", 102), ("w", 131), ("w", 151), ("r", 132)],
                         ids=["closed-way-counts-its-first-node-once", "open-way", "three-node-way",
                              "relation-outer-and-blank-roles-not-inner"])
def test_an_area_is_the_vertex_mean_of_its_distinct_nodes(built, osm_type, osm_id):
    assert [r for r in rows(built[0]) if r[:2] == (osm_type, osm_id)] == \
        [r for r in EXPECTED if r[:2] == (osm_type, osm_id)]


@pytest.mark.parametrize("osm_type,osm_id", [("w", 241), ("r", 242), ("r", 243)],
                         ids=["way-node-missing", "relation-way-missing", "relation-no-outer"])
def test_missing_geometry_is_skipped_never_guessed(built, osm_type, osm_id):
    assert (osm_type, osm_id) not in keys(built[0])


@pytest.mark.parametrize("node,area,merged", [
    (251, ("w", 252), True), (257, ("w", 258), True), (261, ("w", 262), True), (259, ("w", 260), False),
    (263, ("w", 264), False), (267, ("w", 268), False), (269, ("w", 270), False), (255, ("w", 256), False),
    (135, ("r", 136), True), (253, ("w", 254), True),
], ids=["inside-casefolded-name", "max-corner-inclusive", "min-corner-inclusive", "above-max-lat",
        "below-min-lat", "west-of-min-lon", "east-of-max-lon", "same-name-other-class", "relation-area",
        "padded-node-name"])
def test_a_node_inside_a_same_named_area_of_its_class_keeps_the_node(built, node, area, merged):
    assert ("n", node) in keys(built[0])
    assert (area in keys(built[0])) is not merged


def test_the_count_line_counts_every_removal(tmp_path, capsys):
    _, _, lines = run_adapter(tmp_path, FIXTURE, capsys)
    assert lines[-1] == COUNT_LINE


def test_every_place_passes_load_places_and_reaches_the_corpus(built, tmp_path):
    loaded = load_places(built[1])
    assert sorted((r[1], r[2]) for r in loaded) == sorted(r[:2] for r in EXPECTED)
    out = tmp_path / "corpus.sqlite"
    corpus.build(str(built[1]), str(out), "2026-10-05T00:00:00Z")
    conn = sqlite3.connect(str(out))
    try:
        per_cls = dict(conn.execute("SELECT cls, count(*) FROM places GROUP BY cls").fetchall())
        fts = conn.execute("SELECT count(*) FROM places_fts").fetchone()[0]
    finally:
        conn.close()
    assert per_cls == {"viewpoint": 3, "peak": 2, "waterfall": 1, "beach": 4, "trailhead": 1, "museum": 3,
                       "cafe": 5, "garden": 3, "park": 14, "town": 3}
    assert fts == 39


def test_no_places_osm_means_no_places_key(tmp_path):
    doc, _, _ = run_adapter(tmp_path, None)
    assert "places" not in doc


def test_the_osmium_expressions_are_the_allowlist(capsys):
    from etl import placeallow
    assert placeallow.main(["--expressions"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "nw/tourism=viewpoint", "n/natural=peak", "n/waterway=waterfall", "nwr/natural=beach",
        "n/highway=trailhead", "nwr/tourism=museum", "nwr/amenity=cafe", "nwr/leisure=garden",
        "nwr/leisure=park", "n/place=city", "n/place=town", "n/place=village"]

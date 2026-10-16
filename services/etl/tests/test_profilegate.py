"""etl.profilegate on its own: the GraphHopper-11 encoding, the expression evaluator, and its refusals (T-0012).

test_gate_parity.py drives the module over the shipped profile; this file pins each piece by exact equality so
a mutant that the fixture's rows happen not to reach is still seen.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from etl import profilegate as pg

ENCODINGS = [
    ({"highway": "motorway"}, {"road_class": "MOTORWAY", "road_access": "YES", "surface": "MISSING"}),
    ({"highway": "motorway_link"}, {"road_class": "MOTORWAY", "road_access": "YES", "surface": "MISSING"}),
    ({"highway": "trunk_link", "surface": "asphalt"}, {"road_class": "TRUNK", "road_access": "YES",
                                                       "surface": "ASPHALT"}),
    ({"highway": "track", "surface": "fine_gravel"}, {"road_class": "TRACK", "road_access": "YES",
                                                      "surface": "FINE_GRAVEL"}),
    ({"highway": "living_street"}, {"road_class": "LIVING_STREET", "road_access": "YES", "surface": "MISSING"}),
    ({"highway": "proposed"}, {"road_class": "OTHER", "road_access": "YES", "surface": "MISSING"}),
    ({}, {"road_class": "OTHER", "road_access": "YES", "surface": "MISSING"}),
    ({"highway": "residential", "surface": "earth"}, {"road_class": "RESIDENTIAL", "road_access": "YES",
                                                      "surface": "OTHER"}),
    ({"highway": "service", "access": "destination"}, {"road_class": "SERVICE", "road_access": "DESTINATION",
                                                       "surface": "MISSING"}),
    ({"highway": "service", "access": "permit"}, {"road_class": "SERVICE", "road_access": "PRIVATE",
                                                  "surface": "MISSING"}),
    ({"highway": "service", "access": "designated"}, {"road_class": "SERVICE", "road_access": "YES",
                                                      "surface": "MISSING"}),
    ({"highway": "service", "access": "no", "motor_vehicle": "destination"},
     {"road_class": "SERVICE", "road_access": "NO", "surface": "MISSING"}),
    ({"highway": "service", "access": "yes", "motorcar": "private"},
     {"road_class": "SERVICE", "road_access": "PRIVATE", "surface": "MISSING"}),
    ({"highway": "service", "vehicle": "agricultural", "access": "customers"},
     {"road_class": "SERVICE", "road_access": "AGRICULTURAL", "surface": "MISSING"}),
    ({"highway": "service", "motor_vehicle": "no"}, {"road_class": "SERVICE", "road_access": "NO",
                                                     "surface": "MISSING"}),
]


@pytest.mark.parametrize("tags,want", ENCODINGS, ids=[str(i) for i in range(len(ENCODINGS))])
def test_encoding_is_graphhoppers(tags, want):
    assert pg.encode(tags) == {**NO_GATE_FACTS, **want, "car_access": True}


NO_GATE_FACTS = {"track_type": "MISSING", "smoothness": "MISSING", "gate_locked_barrier": False, "gate_ford": False,
                 "gate_service_way": False}
# T-0381 R7: the table GateEncodingTest runs GraphHopper's own parsers and our GateFactParser over.
ENCODING_TABLE = (pathlib.Path(__file__).resolve().parents[2] / "routing" / "plugins" / "scenic-score-parser" / "src"
                  / "test" / "resources" / "gate_encoding.json")
TABLE_ROWS = json.loads(ENCODING_TABLE.read_text(encoding="utf-8"))["rows"]


@pytest.mark.parametrize("row", TABLE_ROWS, ids=[json.dumps(r["tags"], sort_keys=True) for r in TABLE_ROWS])
def test_encoding_matches_the_plugin_table(row):
    got = pg.encode(row["tags"])
    assert {key: got[key] for key in NO_GATE_FACTS} == row["encoded"]
    assert sorted(row["encoded"]) == sorted(NO_GATE_FACTS)


def test_the_plugin_table_is_whole():
    assert ENCODING_TABLE.is_file() and len(TABLE_ROWS) == 44


def test_road_access_order_is_graphhoppers_enum():
    assert pg.ROAD_ACCESS == ("YES", "DESTINATION", "CUSTOMERS", "DELIVERY", "FORESTRY", "AGRICULTURAL",
                              "PRIVATE", "NO")
    assert pg.CAR_RESTRICTION_KEYS == ("motorcar", "motor_vehicle", "vehicle", "access")


VALUES = {"road_class": "TRACK", "road_access": "NO", "surface": "DIRT", "car_access": True}
EXPRESSIONS = [
    ("true", True), ("false", False), ("car_access", True), ("!car_access", False), ("!!car_access", True),
    ("road_class == TRACK", True), ("road_class != TRACK", False), ("road_class == MOTORWAY", False),
    ("road_class == MOTORWAY || road_access == NO", True), ("road_class == MOTORWAY || surface == GRAVEL", False),
    ("road_class == TRACK && road_access == NO", True), ("road_class == TRACK && road_access == YES", False),
    ("road_class == MOTORWAY && road_access == NO", False),
    ("false || false || surface == DIRT", True), ("true && true && false", False),
    ("road_class == MOTORWAY && false || true", True), ("true || true && false", True),
    ("!(road_class == TRACK)", False), ("(false || true) && true", True), ("  road_class==TRACK  ", True),
]


@pytest.mark.parametrize("expression,want", EXPRESSIONS, ids=[e for e, _ in EXPRESSIONS])
def test_expression_evaluator(expression, want):
    assert pg.fires(expression, VALUES) is want


REFUSED = ["road_class = TRACK", "road_class == TRACK ||", "(road_class == TRACK", "road_class == TRACK)",
           "max_speed > 50", "road_class", "road_class == TRACK road_access", "", "scenic_score >= 7", "(true true",
           "true ;", "toll == ALL", "road_class == TRACK || road_environment == FORD", "!max_speed"]


@pytest.mark.parametrize("expression", REFUSED, ids=[repr(e) for e in REFUSED])
def test_an_unreadable_expression_refuses(expression):
    with pytest.raises(ValueError):
        pg.fires(expression, VALUES)


# T-0381 R8: GraphHopper refuses a constant outside the enum and a comparison on a boolean at load.
OUTSIDE = ["track_type == GRADE_3", "track_type != grade3", "smoothness == ROUGH", "road_class == FREEWAY",
           "surface == EARTH", "road_access == PERMIT", "gate_ford == TRUE", "gate_ford != false",
           "gate_service_way == YES", "car_access == true", "road_class == road_class", "track_type == ("]


@pytest.mark.parametrize("expression", OUTSIDE, ids=[repr(e) for e in OUTSIDE])
def test_a_comparison_outside_the_values_refuses(expression):
    with pytest.raises(ValueError):
        pg.fires(expression, pg.encode({}))


def test_every_enum_value_is_comparable():
    for name, domain in pg.DOMAINS.items():
        for constant in domain:
            assert pg.fires("%s == %s || %s != %s" % (name, constant, name, constant), pg.encode({})) is True
    assert pg.DOMAINS["track_type"] == frozenset(pg.TRACK_TYPES)
    assert pg.DOMAINS["smoothness"] == frozenset(pg.SMOOTHNESS)


def _profile(tmp_path, rules):
    path = tmp_path / "p.json"
    path.write_text(json.dumps({"priority": rules}), encoding="utf-8")
    return path


def test_priority_is_the_product_of_the_firing_rules(tmp_path):
    rules = [{"if": "road_class == TRACK", "multiply_by": "0.5"}, {"if": "true", "multiply_by": "0.4"},
             {"if": "road_class == MOTORWAY", "multiply_by": "0.1"}]
    path = _profile(tmp_path, rules)
    assert pg.priority({"highway": "track"}, path) == 0.5 * 0.4
    assert pg.priority({"highway": "motorway"}, path) == 0.4 * 0.1
    assert pg.gated({"highway": "track"}, path) is False
    zero = _profile(tmp_path, rules + [{"if": "surface == DIRT", "multiply_by": "0"}])
    assert pg.gated({"highway": "track", "surface": "dirt"}, zero) is True
    assert pg.gated({"highway": "track", "surface": "gravel"}, zero) is False


@pytest.mark.parametrize("rule", [{"else_if": "true", "multiply_by": "0"}, {"if": "true"},
                                  {"if": "true", "multiply_by": "0", "limit_to": "1"},
                                  {"if": "true", "multiply_by": "zero"}])
def test_a_rule_this_module_cannot_read_refuses(tmp_path, rule):
    with pytest.raises((ValueError, KeyError)):
        pg.priority({"highway": "track"}, _profile(tmp_path, [rule]))


def _model(tmp_path, data):
    path = tmp_path / "m.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


AVERAGE = {"if": "true", "limit_to": "car_average_speed"}
SPEED_ZERO = {"limit_to": {"if": "road_class == MOTORWAY || road_class == TRUNK", "limit_to": "0"},
              "multiply_by": {"if": "road_class == MOTORWAY || road_class == TRUNK", "multiply_by": 0}}


@pytest.mark.parametrize("key", sorted(SPEED_ZERO))
def test_a_firing_speed_of_zero_is_an_exclusion(tmp_path, key):
    """rv1 B1: GraphHopper never routes an edge of speed 0, so a speed-block zero is a gate like a priority 0."""
    path = _model(tmp_path, {"speed": [AVERAGE, SPEED_ZERO[key]], "priority": [], "distance_influence": 30})
    assert pg.gated({"highway": "trunk"}, path) is True
    assert pg.gated({"highway": "motorway_link"}, path) is True
    assert pg.gated({"highway": "residential"}, path) is False
    slow = _model(tmp_path, {"speed": [AVERAGE, {"if": "road_class == MOTORWAY", "limit_to": "50"}]})
    assert pg.gated({"highway": "motorway"}, slow) is False


UNREAD_MODELS = {
    "areas": {"areas": {}, "priority": []},
    "distance_influence_text": {"distance_influence": "30"},
    "distance_influence_negative": {"distance_influence": -1},
    "distance_influence_bool": {"distance_influence": True},
    "speed_else_if": {"speed": [AVERAGE, {"else_if": "true", "limit_to": "0"}]},
    "speed_two_values": {"speed": [{"if": "true", "limit_to": "0", "multiply_by": "1"}]},
    "speed_extra_key": {"speed": [{"if": "true", "limit_to": "car_average_speed", "note": "x"}]},
    "speed_no_value": {"speed": [{"if": "true"}]},
    "speed_unknown_name": {"speed": [{"if": "true", "limit_to": "max_speed"}]},
    "speed_negative": {"speed": [{"if": "true", "limit_to": "-1"}]},
}


@pytest.mark.parametrize("name", sorted(UNREAD_MODELS))
def test_a_model_this_module_cannot_read_refuses(tmp_path, name):
    with pytest.raises((ValueError, KeyError, TypeError)):
        pg.gated({"highway": "residential"}, _model(tmp_path, UNREAD_MODELS[name]))


def test_the_shipped_profile_gates_exactly_its_clauses():
    """Over the shipped file: one tag set per clause is gated, and the same way without it is not."""
    assert pg.gated({"highway": "residential"}) is False
    assert pg.gated({"highway": "residential", "access": "destination"}) is True
    assert pg.gated({"highway": "residential", "access": "customers"}) is False
    assert pg.gated({"highway": "residential", "surface": "sand"}) is True
    assert pg.gated({"highway": "residential", "surface": "asphalt"}) is False
    assert pg.gated({"highway": "track", "surface": "asphalt"}) is True
    assert pg.gated({"highway": "motorway"}) is False
    assert pg.gated({"highway": "trunk", "surface": "asphalt", "smoothness": "good", "tracktype": "grade1"}) is False


GATED_BY_T0381 = [({"highway": "tertiary", "tracktype": t}, True) for t in ("grade3", "grade4", "grade5")] + [
    ({"highway": "tertiary", "tracktype": t}, False) for t in ("grade1", "grade2", "grade6")] + [
    ({"highway": "residential", "smoothness": s}, True)
    for s in ("bad", "very_bad", "horrible", "very_horrible", "impassable")] + [
    ({"highway": "residential", "smoothness": s}, False)
    for s in ("excellent", "good", "intermediate", "rough", "")] + [
    ({"highway": "tertiary", "barrier": "gate", "locked": "yes"}, True),
    ({"highway": "tertiary", "barrier": "gate", "locked": "no"}, False),
    ({"highway": "tertiary", "barrier": "bollard", "locked": "yes"}, False),
    ({"highway": "unclassified", "ford": "yes"}, True), ({"highway": "unclassified", "ford": "no"}, False),
    ({"highway": "service", "service": "driveway"}, True), ({"highway": "service", "service": "parking_aisle"}, True),
    ({"highway": "service", "service": "drive-through"}, True),
    ({"highway": "service", "service": "emergency_access"}, True),
    ({"highway": "service", "service": "alley"}, False), ({"highway": "service"}, False),
    ({"highway": "motorway", "service": "driveway"}, False),
]
# rv1 B1: every gating value padded is a near miss - GraphHopper 11's valueOf and GateFacts compare untrimmed.
GATED_BY_T0381 += [({**tags, key: pad % tags[key]}, False) for tags, want in list(GATED_BY_T0381) if want
                   for key in sorted(tags) if key != "highway" for pad in (" %s", "%s ")]


@pytest.mark.parametrize("tags,want", GATED_BY_T0381, ids=[json.dumps(t, sort_keys=True) for t, _ in GATED_BY_T0381])
def test_the_shipped_profile_gates_the_t0381_clauses(tags, want):
    """Each new clause over the SHIPPED file: its positive evidence gates, its near misses do not."""
    assert pg.gated(tags) is want

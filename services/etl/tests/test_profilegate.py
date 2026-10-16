"""etl.profilegate on its own: the GraphHopper-11 encoding, the expression evaluator, and its refusals (T-0012).

test_gate_parity.py drives the module over the shipped profile; this file pins each piece by exact equality so
a mutant that the fixture's rows happen not to reach is still seen.
"""
from __future__ import annotations

import json

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
    assert pg.encode(tags) == {**want, "car_access": True}


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
           "max_speed > 50", "road_class", "road_class == TRACK road_access", "", "scenic_score >= 7"]


@pytest.mark.parametrize("expression", REFUSED, ids=[repr(e) for e in REFUSED])
def test_an_unreadable_expression_refuses(expression):
    with pytest.raises(ValueError):
        pg.fires(expression, VALUES)


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


def test_the_shipped_profile_gates_exactly_its_clauses():
    """Over the shipped file: one tag set per clause is gated, and the same way without it is not."""
    assert pg.gated({"highway": "residential"}) is False
    assert pg.gated({"highway": "residential", "access": "destination"}) is True
    assert pg.gated({"highway": "residential", "access": "customers"}) is False
    assert pg.gated({"highway": "residential", "surface": "sand"}) is True
    assert pg.gated({"highway": "residential", "surface": "asphalt"}) is False
    assert pg.gated({"highway": "track", "surface": "asphalt"}) is True
    assert pg.gated({"highway": "motorway"}) is False

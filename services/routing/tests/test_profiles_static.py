"""The shipped base profile and config, read as files - no container, no graph, no docker.

test_lambda_monotone.py's routed tests SKIP wherever docker is absent, which is every CI runner this repo
has, and they cannot see these properties even when they run:

  - The safety gates live in car_scenic_base.json, which the Dockerfile bakes into the image; no routed test
    mounts it, so the routed suite ran 9 passed with `priority: []` (PR #105 rv2 R2). The whole priority list is
    compared here to a typed literal (T-0190, P-SAFE-01's JSON half).
  - The CLAUDE.md invariant "motorway/trunk are PENALIZED, not hard-excluded" is guarded on the Vermont pair
    only by the route disappearing (ConnectionNotFoundException). On a fixture that stayed routable, a hard
    gate would pass unnoticed.

The per-request models are not a profile here any more: they are the Worker's recorded bytes, checked by
test_request_models_static.py and services/api/test/customModelGolden.test.ts (T-0190).

Anchors are the files' own identifiers - JSON keys, expression strings, the `import.osm.ignored_highways`
config key - never a comment, which gets stripped.
"""

import json
import re
from pathlib import Path

import pytest

from request_models import ORACLE_LAMBDAS, recorded

ROUTING = Path(__file__).resolve().parents[1]
BASE = ROUTING / "profiles" / "car_scenic_base.json"
CONFIG = ROUTING / "config.yml"

# Typed out, not read from anywhere: the base profile's nine zero clauses (plan :98-110, T-0381), in order. A
# gate deleted, relaxed, reordered or turned into a penalty is red by name; so is a tenth clause, which is the
# only place a motorway or trunk hard gate could be added.
EXPECTED_BASE_PRIORITY = [
    {"if": "!car_access", "multiply_by": "0"},
    {"if": "road_access == PRIVATE || road_access == NO || road_access == DESTINATION", "multiply_by": "0"},
    {"if": "surface == GRAVEL || surface == DIRT || surface == GROUND || surface == SAND || surface == UNPAVED "
           "|| surface == COMPACTED || surface == FINE_GRAVEL", "multiply_by": "0"},
    {"if": "road_class == TRACK", "multiply_by": "0"},
    {"if": "track_type == GRADE3 || track_type == GRADE4 || track_type == GRADE5", "multiply_by": "0"},
    {"if": "smoothness == BAD || smoothness == VERY_BAD || smoothness == HORRIBLE || smoothness == VERY_HORRIBLE "
           "|| smoothness == IMPASSABLE", "multiply_by": "0"},
    {"if": "gate_locked_barrier", "multiply_by": "0"},
    {"if": "gate_ford", "multiply_by": "0"},
    {"if": "gate_service_way", "multiply_by": "0"},
]

HARD_GATE = re.compile(r"\b(MOTORWAY|TRUNK)\b")
MODEL_KEYS = {"speed", "priority", "distance_influence"}
CLAUSE_KINDS = ("if", "else_if", "else")
SPEED_VALUE_KEYS = ("limit_to", "multiply_by")
SPEED_NAMES = {"car_average_speed"}
IGNORED_HIGHWAYS = re.compile(r"^\s*import\.osm\.ignored_highways\s*:(.*)$", re.MULTILINE)


def _priority(path):
    return json.loads(path.read_text(encoding="utf-8"))["priority"]


def _condition(rule):
    """The rule's condition under whichever ONE of if / else_if / else it carries ("" for else)."""
    kinds = [kind for kind in CLAUSE_KINDS if kind in rule]
    assert len(kinds) == 1, f"rule {rule!r} carries {kinds}, not exactly one of {CLAUSE_KINDS}"
    return rule[kinds[0]]


def test_base_profile_priority_is_the_nine_safety_gates():
    """P-SAFE-01's JSON half, compared WHOLE: no routed test can see this file (the image bakes it in)."""
    priority = _priority(BASE)
    assert priority == EXPECTED_BASE_PRIORITY, (
        f"{BASE.name} priority is not the nine safety gates.\nexpected: {EXPECTED_BASE_PRIORITY}\n"
        f"actual:   {priority}"
    )


def _positive_speed(value):
    if value in SPEED_NAMES:
        return True
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def test_no_profile_hard_excludes_motorway_or_trunk():
    """CLAUDE.md: motorway/trunk carry scenic_score 0 and are PENALIZED, never hard-excluded (freeway
    shoulders, scenic middle). Hard gates are safety only: unpaved, private/no access, track. GraphHopper
    never routes an edge of speed 0 either, so the WHOLE model is read (T-0012 rv1 B1): no key this test
    cannot read, and every speed rule's value a positive number or an encoded speed - the gates live in
    priority, never in speed. Read over the base profile AND every recorded per-request model."""
    for path in (BASE, *(recorded(value) for value in ORACLE_LAMBDAS)):
        model = json.loads(path.read_text(encoding="utf-8"))
        unread = sorted(set(model) - MODEL_KEYS)
        assert not unread, f"{path.name} carries {unread}: a key this test cannot read could exclude a road"
        for rule in model.get("speed", []):
            values = [rule[key] for key in SPEED_VALUE_KEYS if key in rule]
            assert len(values) == 1 and _positive_speed(values[0]), (
                f"{path.name} speed rule {rule!r} can set a speed of 0 (or is unreadable): a zero speed is "
                f"a hard exclusion, and motorway and trunk are penalized, never hard-excluded"
            )
        for rule in model["priority"]:
            condition = _condition(rule)
            assert not HARD_GATE.search(condition), (
                f"{path.name} gates on {condition!r}: motorway and trunk are penalized by the band model, "
                f"never hard-excluded. Hard gates are safety only - unpaved, private/no access, track."
            )


def test_ignored_highways_keeps_motorway_and_trunk():
    """GraphHopper drops the named highway classes from the graph entirely - an edge that is not imported
    can never be penalized back in."""
    match = IGNORED_HIGHWAYS.search(CONFIG.read_text(encoding="utf-8"))
    if match is None:
        pytest.skip("config.yml sets no import.osm.ignored_highways, so nothing is dropped at import")
    named = [value.strip().lower() for value in match.group(1).split(",") if value.strip()]
    offenders = [value for value in named if value.startswith(("motorway", "trunk"))]
    assert not offenders, (
        f"config.yml drops {offenders} at import: motorway and trunk must reach the graph and be "
        f"penalized there (scenic_score 0), never hard-excluded. ignored_highways reads {named}."
    )


ENCODED_VALUES = re.compile(r"^\s*graph\.encoded_values:\s*(.+?)\s*$", re.MULTILINE)
IDENTIFIER = re.compile(r"\b[a-z][a-z0-9_]*\b")
LITERALS = {"true", "false"}
# T-0381: the five gates the profile learned, each an encoded value GraphHopper must be told to build.
T0381_GATE_VALUES = {"track_type", "smoothness", "gate_locked_barrier", "gate_ford", "gate_service_way"}


def _configured():
    found = ENCODED_VALUES.findall(CONFIG.read_text(encoding="utf-8"))
    assert len(found) == 1, f"{CONFIG.name} must carry graph.encoded_values exactly once, found {found}"
    return {name.strip() for name in found[0].split(",")}


def _read_by(path):
    model = json.loads(path.read_text(encoding="utf-8"))
    names = set()
    for block in ("speed", "priority"):
        for rule in model.get(block, []):
            for key, value in rule.items():
                names |= set(IDENTIFIER.findall(str(value))) - LITERALS
    return names


def test_every_encoded_value_the_base_profile_reads_is_configured():
    """GraphHopper refuses to load a profile naming an encoded value the import did not build (T-0381)."""
    missing = sorted(_read_by(BASE) - _configured())
    assert not missing, f"{BASE.name} reads {missing}, which config.yml graph.encoded_values does not build"


def test_the_t0381_gates_are_read_and_built():
    assert T0381_GATE_VALUES <= _read_by(BASE), sorted(T0381_GATE_VALUES - _read_by(BASE))
    assert T0381_GATE_VALUES <= _configured(), sorted(T0381_GATE_VALUES - _configured())
    assert "road_environment" not in _read_by(BASE) | _configured()

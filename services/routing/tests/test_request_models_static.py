"""The per-request models the routing oracle sends, read as files - no container, no graph, no docker.

T-0190. The models are the Worker's recorded bytes (request_models.py); their EQUALITY to the shipped builder is
services/api/test/customModelGolden.test.ts's job, which ops/test runs. This file asserts what the router needs of
them and a byte comparison does not say, each property read off the records and the routing files, never typed
from the Worker's arithmetic (a second copy of the band table is the defect T-0190 removed):

  - The clause chain is one `if`, then only `else_if`, then one `else`, read by KEY. A band written `if` starts
    a second chain: GraphHopper multiplies every matching `if` together, so the minor clause and a band both
    fire and a three-band model silently becomes another one. The old _condition() read `if` and `else_if`
    alike, so this passed the container-free half (PR #105 rv2).
  - The ladder's thresholds strictly descend: an `else_if scenic_score >= s` after a lower threshold can never
    fire, and a band that never fires is a dead penalty no routed order property sees.
  - At lambda 0 every multiplier is "1" (lambda 0 is car_fast, the bisection's feasible end), and no clause's
    multiplier grows with lambda (a penalty pointing the wrong way keeps T(lambda) non-decreasing).
  - Every encoded value a model reads is one config.yml builds (GraphHopper refuses the request otherwise), and
    none is one the base profile's zero gates read, road_class aside (a request model naming a gate value could
    relax it - T-0382's refusal, seen from the router's side).
"""

import json
import re
from pathlib import Path

from request_models import ORACLE_LAMBDAS, recorded

ROUTING = Path(__file__).resolve().parents[1]
BASE = ROUTING / "profiles" / "car_scenic_base.json"
CONFIG = ROUTING / "config.yml"

CLAUSE_KINDS = ("if", "else_if", "else")
THRESHOLD = re.compile(r"^scenic_score >= (\d+)$")
ENCODED_VALUES = re.compile(r"^\s*graph\.encoded_values:\s*(.+?)\s*$", re.MULTILINE)
IDENTIFIER = re.compile(r"\b[a-z][a-z0-9_]*\b")
# The base profile's gates may branch on road_class (TRACK); the request model's minor clause reads it too.
SHARED_WITH_THE_BASE = {"road_class"}


def _model(value):
    return json.loads(recorded(value).read_text(encoding="utf-8"))


def _kind(rule):
    kinds = [kind for kind in CLAUSE_KINDS if kind in rule]
    assert len(kinds) == 1 and set(rule) == {kinds[0], "multiply_by"}, (
        f"clause {rule!r} must carry exactly one of {CLAUSE_KINDS} and multiply_by"
    )
    return kinds[0]


def _identifiers(model):
    return {name for rule in model["priority"] for name in IDENTIFIER.findall(rule[_kind(rule)])}


def test_the_clause_chain_is_one_if_then_else_ifs_then_one_else():
    for value in ORACLE_LAMBDAS:
        kinds = [_kind(rule) for rule in _model(value)["priority"]]
        expected = ["if"] + ["else_if"] * (len(kinds) - 2) + ["else"]
        assert len(kinds) >= 3 and kinds == expected, (
            f"lambda-{value}.json clause chain is {kinds}, not one `if`, then `else_if` only, then one `else`: "
            f"a clause written `if` mid-chain fires alongside the clause before it"
        )


def test_the_band_thresholds_strictly_descend():
    for value in ORACLE_LAMBDAS:
        conditions = [rule["else_if"] for rule in _model(value)["priority"] if "else_if" in rule]
        thresholds = []
        for condition in conditions:
            match = THRESHOLD.match(condition)
            assert match, f"lambda-{value}.json else_if {condition!r} is not a scenic_score threshold"
            thresholds.append(int(match.group(1)))
        assert thresholds == sorted(set(thresholds), reverse=True), (
            f"lambda-{value}.json band thresholds {thresholds} do not strictly descend: a band after a lower "
            f"threshold never fires"
        )


def test_lambda_zero_multiplies_by_one_everywhere():
    multipliers = [rule["multiply_by"] for rule in _model(0)["priority"]]
    assert multipliers == ["1"] * len(multipliers), (
        f"lambda-0.json multiplies by {multipliers}: lambda 0 must be the car_fast route"
    )


def test_no_clause_multiplier_grows_with_lambda():
    models = {value: _model(value)["priority"] for value in ORACLE_LAMBDAS}
    shapes = {value: [(_kind(rule), rule[_kind(rule)]) for rule in rules] for value, rules in models.items()}
    assert all(shape == shapes[0] for shape in shapes.values()), (
        f"the oracle models do not share one clause list across lambdas: {shapes}"
    )
    for position in range(len(models[0])):
        series = [float(models[value][position]["multiply_by"]) for value in ORACLE_LAMBDAS]
        assert all(0 < multiplier <= 1 for multiplier in series), f"clause {position} leaves (0, 1]: {series}"
        assert series == sorted(series, reverse=True), (
            f"clause {position} ({shapes[0][position]}) multiplier GREW with lambda over {list(ORACLE_LAMBDAS)}: "
            f"{series}"
        )


def _configured():
    found = ENCODED_VALUES.findall(CONFIG.read_text(encoding="utf-8"))
    assert len(found) == 1, f"{CONFIG.name} must carry graph.encoded_values exactly once, found {found}"
    return {name.strip() for name in found[0].split(",")}


def _base_gate_values():
    base = json.loads(BASE.read_text(encoding="utf-8"))["priority"]
    return {name for rule in base if rule["multiply_by"] == "0" for name in IDENTIFIER.findall(rule["if"])}


def test_every_value_a_model_reads_is_built_and_none_is_a_gate_value():
    gates = _base_gate_values() - SHARED_WITH_THE_BASE
    assert gates, f"{BASE.name} has no zero gate this test could read"
    for value in ORACLE_LAMBDAS:
        read = _identifiers(_model(value))
        assert read and read <= _configured(), (
            f"lambda-{value}.json reads {sorted(read - _configured())}, which config.yml does not build"
        )
        assert not read & gates, (
            f"lambda-{value}.json reads the base profile's gate values {sorted(read & gates)}: a request model "
            f"that names a gate value could relax it"
        )

"""The shipped profiles and config, read as files - no container, no graph, no docker.

test_lambda_monotone.py's routed tests SKIP wherever docker is absent, which is every CI runner this repo
has, and they cannot see these properties even when they run:

  - The band THRESHOLDS in car_scenic_request.json are load-bearing and invisible to a routed assertion.
    `scenic_score >= 7` -> `scenic_score >= 0` puts every edge in the `high` band, whose multiplier is 1 at
    every lambda; the per-request model becomes a no-op, T(lambda) is constant, and a constant is
    non-decreasing and equals car_fast everywhere.
  - The band TABLE can be inverted - mid 1, 1.5, 2, 3, 5 and low 1, 2, 3, 5, 9, a penalty that grows with
    lambda instead of shrinking - and T(lambda) stays non-decreasing. The routed property tells neither a
    dead model nor an inverted one from the plan's.
  - The CLAUDE.md invariant "motorway/trunk are PENALIZED, not hard-excluded" is guarded on the Vermont pair
    only by the route disappearing (ConnectionNotFoundException). On a fixture that stayed routable, a hard
    gate would pass unnoticed.

Anchors are the files' own identifiers - JSON keys, expression strings, the `import.osm.ignored_highways`
config key - never a comment, which gets stripped.
"""

import json
import re
from pathlib import Path

import pytest

LAMBDAS = ("0", "1", "2", "4", "8")

# Typed literals, not a re-computation of the formula: the plan's bands (:105-107) are high = 1,
# mid = 1/(1+0.5*lambda), low = 1/(1+lambda), written to the six decimals the file carries with trailing
# zeros dropped. test_lambda_monotone.py checks the same table against the formula; this checks the digits.
EXPECTED_BANDS = {
    "0": {"high": "1", "mid": "1", "low": "1"},
    "1": {"high": "1", "mid": "0.666667", "low": "0.5"},
    "2": {"high": "1", "mid": "0.5", "low": "0.333333"},
    "4": {"high": "1", "mid": "0.333333", "low": "0.2"},
    "8": {"high": "1", "mid": "0.2", "low": "0.111111"},
}

EXPECTED_THRESHOLDS = [7, 4]

ROUTING = Path(__file__).resolve().parents[1]
REQUEST = ROUTING / "profiles" / "car_scenic_request.json"
BASE = ROUTING / "profiles" / "car_scenic_base.json"
BANDS = ROUTING / "profiles" / "scenic_lambda_bands.json"
CONFIG = ROUTING / "config.yml"

THRESHOLD = re.compile(r"^scenic_score\s*>=\s*(\d+)$")
HARD_GATE = re.compile(r"\b(MOTORWAY|TRUNK)\b")
IGNORED_HIGHWAYS = re.compile(r"^\s*import\.osm\.ignored_highways\s*:(.*)$", re.MULTILINE)


def _priority(path):
    return json.loads(path.read_text(encoding="utf-8"))["priority"]


def _condition(rule):
    for key in ("if", "else_if"):
        value = rule.get(key)
        if value:
            return value
    return ""


def test_request_model_bands_are_the_plan_thresholds():
    """Three rules: scenic_score >= 7 -> high, scenic_score >= 4 -> mid, everything else -> low."""
    rules = _priority(REQUEST)
    assert len(rules) == 3, f"{REQUEST.name} has {len(rules)} priority rules, expected the plan's 3: {rules}"
    thresholds = []
    for rule, placeholder in zip(rules, ("${high}", "${mid}")):
        condition = _condition(rule)
        match = THRESHOLD.match(condition.strip())
        assert match, (
            f"{REQUEST.name}: band condition {condition!r} is not a scenic_score threshold - the three "
            f"bands are what the per-request lambda model acts on"
        )
        thresholds.append(int(match.group(1)))
        assert rule["multiply_by"] == placeholder, (
            f"{REQUEST.name}: band {condition!r} multiplies by {rule['multiply_by']!r}, expected "
            f"{placeholder!r} so scenic_lambda_bands.json's value reaches it"
        )
    assert thresholds == EXPECTED_THRESHOLDS, (
        f"{REQUEST.name}: band thresholds are {thresholds}, the plan's are {EXPECTED_THRESHOLDS}. A first "
        f"threshold of 0 puts every edge in the never-penalized band and the whole per-request model dies "
        f"with every routed test still green."
    )
    assert "else" in rules[2] and rules[2]["multiply_by"] == "${low}", (
        f"{REQUEST.name}: the third rule must be the else band multiplying by ${{low}}: {rules[2]}"
    )


def test_band_table_matches_the_plan_literals():
    bands = json.loads(BANDS.read_text(encoding="utf-8"))
    assert sorted(bands, key=int) == sorted(LAMBDAS, key=int), (
        f"{BANDS.name} carries lambdas {sorted(bands, key=int)}, the plan's five are {list(LAMBDAS)}"
    )
    for value in LAMBDAS:
        assert bands[value] == EXPECTED_BANDS[value], (
            f"{BANDS.name} at lambda={value}: {bands[value]} is not the plan's {EXPECTED_BANDS[value]} "
            f"(high 1, mid 1/(1+0.5*lambda), low 1/(1+lambda))"
        )


def test_band_multipliers_never_grow_with_lambda():
    """A multiplier that GROWS with lambda is a penalty pointing the wrong way. Inverting both penalized
    bands leaves T(lambda) non-decreasing, so no routed assertion catches it."""
    bands = json.loads(BANDS.read_text(encoding="utf-8"))
    for name in ("high", "mid", "low"):
        series = [float(bands[value][name]) for value in LAMBDAS]
        for index in range(len(LAMBDAS) - 1):
            assert series[index + 1] <= series[index], (
                f"{BANDS.name}: the {name} band's multiplier GREW from lambda={LAMBDAS[index]} "
                f"({series[index]}) to lambda={LAMBDAS[index + 1]} ({series[index + 1]}) - a larger lambda "
                f"must never make a band cheaper"
            )


def test_no_profile_hard_excludes_motorway_or_trunk():
    """CLAUDE.md: motorway/trunk carry scenic_score 0 and are PENALIZED, never hard-excluded (freeway
    shoulders, scenic middle). Hard gates are safety only: unpaved, private/no access, track."""
    for path in (BASE, REQUEST):
        for rule in _priority(path):
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

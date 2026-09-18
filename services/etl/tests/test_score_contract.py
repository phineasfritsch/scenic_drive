"""The ETL half of the scorer contract: `etl.score` against the shared fixture.

The expectations in `Tests/Fixtures/scoring/segment_terms.json` were computed by neither implementation -
they come from a hand transcription of the plan's formula inside `Tests/Fixtures/scoring/generate.py`. The
Swift half, `Tests/ScenicKitTests/SegmentScoreContractTests.swift`, reads the SAME file and asserts the same
tolerance, so the two scorers are pinned to one oracle rather than to each other.

Tolerance is 1e-6, which is the plan's own number (line 219: "ScenicKit SegmentScore differential vs corpus
on 1,000 sampled segments < 1e-6"). Failures are reported BY ROW ID: "47 rows disagree" tells the next agent
nothing, and the ids in this fixture say what kind of row it was.

If the fixture file is missing this module FAILS at collection rather than skipping. A skipped contract is
not a kept one.
"""
from __future__ import annotations

import json
import math
import pathlib

import pytest

from etl import byways, score

FIXTURE = (pathlib.Path(__file__).resolve().parents[3]
           / "Tests" / "Fixtures" / "scoring" / "segment_terms.json")

TOLERANCE = 1e-6

# The fixture's tier vocabulary is implementation-neutral on purpose - neither side's spelling. Here it
# becomes Caltrans's own status code, which is what `byways.status_bonus` reads.
STATUS_FOR_TIER = {"none": None, "eligible": byways.ELIGIBLE, "designated": byways.DESIGNATED}


def _load() -> dict:
    if not FIXTURE.exists():
        raise AssertionError("fixture missing: %s - run python Tests/Fixtures/scoring/generate.py" % FIXTURE)
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


DOC = _load()
ROWS = DOC["rows"]


def _metres(value) -> float:
    """The fixture spells infinity as a string, because JSON has no literal for it."""
    return math.inf if value == "Infinity" else float(value)


def scored(row: dict):
    """`etl.score.score` fed one fixture row. Every input the score depends on comes from the row."""
    return score.score(curvature=row["curvature"],
                       elevation_gain=row["elevationGain"],
                       speed_fit=row["speedFit"],
                       sinuosity=row["sinuosity"],
                       canopy=row["canopy"],
                       relief=row["relief"],
                       impervious=row["impervious"],
                       points_of_interest=row["pointsOfInterest"],
                       water=row["water"],
                       furniture=row["furniture"],
                       highway=row["highway"],
                       byway_status=STATUS_FOR_TIER[row["bywayTier"]],
                       surface=row["surface"],
                       tunnel_meters=row["tunnelMeters"],
                       meters_to_nearest_motorway=_metres(row["metersToNearestMotorway"]))


def test_fixture_is_the_whole_population_it_claims():
    """A truncated or emptied fixture must not read as a kept contract."""
    assert DOC["rowCount"] == len(ROWS), "rowCount %s but %d rows" % (DOC["rowCount"], len(ROWS))
    assert len(ROWS) >= 1000, "the plan's differential is over 1,000 segments, got %d" % len(ROWS)
    ids = [r["id"] for r in ROWS]
    assert len(set(ids)) == len(ids), "duplicate row ids - a failure could not be named"


def test_fixture_covers_the_properties_this_contract_exists_for():
    """Coverage asserted, not assumed: a regenerated fixture that dropped a tier would pass everything else."""
    tiers = {r["bywayTier"] for r in ROWS}
    assert tiers == {"none", "eligible", "designated"}, tiers
    classes = {r["highway"] for r in ROWS}
    assert byways.SCENIC_ZERO_CLASSES <= classes, "missing zero class(es): %s" % (
        sorted(byways.SCENIC_ZERO_CLASSES - classes),)
    for tier in ("eligible", "designated"):
        scorable = [r for r in ROWS
                    if r["bywayTier"] == tier and r["highway"] not in byways.SCENIC_ZERO_CLASSES
                    and r["expected"] > 0.0]
        assert len(scorable) >= 50, "%s: only %d rows can show the bonus at all" % (tier, len(scorable))
    assert any(r["tunnelMeters"] > 300.0 for r in ROWS)
    assert any(r["tunnelMeters"] == 300.0 for r in ROWS)
    assert any(_metres(r["metersToNearestMotorway"]) < 150.0 for r in ROWS)
    assert any(_metres(r["metersToNearestMotorway"]) == 150.0 for r in ROWS)
    assert any(r["surface"] is None and r["highway"] in score.UNSURVEYED_CLASSES for r in ROWS)
    for term in ("curvature", "canopy", "furniture"):
        assert any(r[term] == 0.0 for r in ROWS) and any(r[term] == 1.0 for r in ROWS), term


def test_every_fixture_row_scores_within_1e_6_of_the_oracle():
    """The contract itself. Reports the worst offenders by id, not a count."""
    failures = []
    worst = (0.0, None)
    for row in ROWS:
        got = scored(row)
        if got is None:
            failures.append("%s: score returned None on an in-range row" % row["id"])
            continue
        delta = abs(got - row["expected"])
        if delta > worst[0]:
            worst = (delta, row["id"])
        if not delta < TOLERANCE:
            failures.append("%s: got %r, oracle %r, delta %.3e (tier=%s highway=%s)"
                            % (row["id"], got, row["expected"], delta, row["bywayTier"], row["highway"]))
    assert not failures, ("%d of %d rows disagree with the oracle by >= %g; worst delta %.3e at %s\n%s"
                          % (len(failures), len(ROWS), TOLERANCE, worst[0], worst[1],
                             "\n".join(failures[:20])))


def test_the_two_byway_tiers_are_not_the_same_number():
    """Guards the differential itself: if the fixture could not tell the tiers apart it would prove nothing.

    Every eligible row would then agree with a scorer that pays 0.15 for both, which is exactly the defect
    this contract was written to catch.
    """
    assert byways.ELIGIBLE_BONUS != byways.DESIGNATED_BONUS
    base = dict(curvature=0.5, elevation_gain=0.5, speed_fit=0.5, sinuosity=0.5, canopy=0.5, relief=0.5,
                impervious=0.5, points_of_interest=0.5, water=0.5, furniture=0.5, highway="residential",
                surface="asphalt")
    plain = score.score(byway_status=None, **base)
    eligible = score.score(byway_status=byways.ELIGIBLE, **base)
    designated = score.score(byway_status=byways.DESIGNATED, **base)
    assert plain < eligible < designated, (plain, eligible, designated)
    gap = byways.DESIGNATED_BONUS - byways.ELIGIBLE_BONUS
    assert gap > TOLERANCE * 1000, "a tier gap of %r would hide inside the tolerance" % gap


def test_a_zero_class_scores_zero_however_pretty_it_is():
    """plan:83. Penalised, never gated: the score is 0 and the router is still allowed to use it."""
    for highway in sorted(byways.SCENIC_ZERO_CLASSES):
        value = score.score(curvature=1.0, elevation_gain=1.0, speed_fit=1.0, sinuosity=1.0, canopy=1.0,
                            relief=1.0, impervious=0.0, points_of_interest=1.0, water=1.0, furniture=0.0,
                            highway=highway, byway_status=byways.DESIGNATED, surface="asphalt")
        assert value == 0.0, "%s scored %r" % (highway, value)


@pytest.mark.parametrize("term", score.UNIT_TERMS)
def test_a_term_outside_zero_to_one_is_refused_rather_than_clamped(term):
    """A plausible score from a wrong input is the hardest error to find later, so None rather than a clamp."""
    base = {name: 0.5 for name in score.UNIT_TERMS}
    for bad in (-0.0001, 1.0001, float("nan")):
        terms = dict(base)
        terms[term] = bad
        assert score.score(highway="residential", **terms) is None, (term, bad)

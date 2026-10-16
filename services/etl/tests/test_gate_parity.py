"""P-PROD-01: ONE fixture of ways, three consumers, one expected verdict per row (T-0012).

tests/fixtures/gate_parity.json is read here by the ETL's shipping row function (`assemble.scored_row`, which
`assemble.assemble` maps every way through) and by `etl.profilegate` over the SHIPPED
services/routing/profiles/car_scenic_base.json; Tests/ScenicKitTests/GateParityFixtureTests.swift reads the
same file through `Gates.decide` and `SegmentScore`. Every failure names the layer that disagreed and what the
other layers answer for that row - never a bare "mismatch".

`verdict` is the product's answer and ScenicKit's. A row may carry `divergent` - what the ETL and the profile
answer TODAY where they cannot yet agree (T-0012 ruling R1; the profile only since T-0188) - and only the
five typed classes may.
"""
from __future__ import annotations

import json
import math
import pathlib

import pytest

from etl import assemble, profilegate, surface
from etl.way_record import NORMALISED, WayRecord

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "gate_parity.json"
ROWS = json.loads(FIXTURE.read_text(encoding="utf-8"))["rows"]
IDS = [row["class"] for row in ROWS]

GATED, ZERO, PAVED, X08, NOT_GATED = "GATED", "ZERO_NOT_GATED", "PAVED", "UNKNOWN_X08", "NOT_GATED"
VERDICTS = (GATED, ZERO, PAVED, X08)
PAVED_SURFACE = "asphalt"
NEUTRAL = 0.5
X08_FACTOR = 0.8

# The Brief's classes, typed. A class dropped from the fixture is a class nobody checks any more.
CORE_CLASSES = (
    ["motorway", "motorway_link", "trunk", "trunk_link"]
    + ["surface=" + s for s in ("gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel")]
    + ["highway=track"] + ["highway=track+tracktype=grade%d" % g for g in (3, 4, 5)]
    + ["access=" + a for a in ("private", "no", "permit", "destination")] + ["motor_vehicle=no"]
    + ["no surface on " + h for h in ("primary", "secondary", "tertiary", "unclassified", "residential")]
)
# R1: ScenicKit refuses these; T-0188 ported them into the ETL and the profile has no encoded value for them.
DIVERGENT_CLASSES = ("tracktype=grade3 on tertiary", "barrier=gate+locked=yes", "ford=yes", "service=driveway",
                     "service=parking_aisle")
# T-0188 rv1 B1/B2: Gates.verdict compares ford and locked to "yes" ONLY, so every layer routes these.
NEAR_MISS_CLASSES = ("ford=stepping_stones", "barrier=gate+locked=true", "ford=Yes")
EXPECTED_VERDICT = {**{c: ZERO for c in CORE_CLASSES[:4]}, **{c: GATED for c in CORE_CLASSES[4:20]},
                    **{c: PAVED for c in CORE_CLASSES[20:23]}, **{c: X08 for c in CORE_CLASSES[23:]},
                    **{c: GATED for c in DIVERGENT_CLASSES}, **{c: PAVED for c in NEAR_MISS_CLASSES}}


def record(tags: dict, surface_value) -> WayRecord:
    """One way with every term at 0.5, so its score is decided by the class and surface rules alone."""
    return WayRecord(way_id=1, highway=tags["highway"], curvature=NEUTRAL, elevation_gain=NEUTRAL,
                     relief=NEUTRAL, sinuosity=NEUTRAL, furniture=NEUTRAL, canopy=NEUTRAL, impervious=NEUTRAL,
                     water=NEUTRAL, speed_fit=NEUTRAL, points_of_interest=NEUTRAL, surface=surface_value,
                     terms_state=NORMALISED)


def classify(score: float, paved: float, flagged: bool) -> str:
    """The verdict from a score, the same way's score on a paved surface, and the surface_unknown flag."""
    if not flagged and score == 0.0 and paved == 0.0:
        return ZERO
    if not flagged and score > 0.0 and score == paved:
        return PAVED
    if flagged and score > 0.0 and math.isclose(score, X08_FACTOR * paved, rel_tol=1e-12):
        return X08
    return "INCONSISTENT(score=%r paved=%r surface_unknown=%r)" % (score, paved, flagged)


def etl_verdict(tags: dict) -> str:
    row = assemble.scored_row(record(tags, tags.get("surface")), tags)
    if row["gate_reason"] is not None:
        return GATED
    paved_tags = {**tags, "surface": PAVED_SURFACE}
    paved = assemble.scored_row(record(paved_tags, PAVED_SURFACE), paved_tags)
    flagged = surface.surface_state(highway=tags["highway"], surface=tags.get("surface")) == surface.SURFACE_UNKNOWN
    return classify(row["score"], paved["score"], flagged)


def profile_verdict(tags: dict) -> str:
    return GATED if profilegate.gated(tags) else NOT_GATED


def as_gate(verdict: str) -> str:
    return GATED if verdict == GATED else NOT_GATED


def expected(row: dict, layer: str) -> str:
    return (row.get("divergent") or {}).get(layer, row["verdict"])


def disagreement(row: dict, layer: str, got: str, others: dict) -> str:
    said = ", ".join("%s says %s" % (name, value) for name, value in others.items())
    return ("%s (way %s): %s says %s, expected %s; %s"
            % (row["class"], row["way_id"], layer, got, expected(row, layer.split()[0].lower()), said))


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_etl_gives_the_fixture_verdict(row):
    got = etl_verdict(row["tags"])
    want = expected(row, "etl")
    assert got == want, disagreement(row, "ETL (assemble.scored_row)", got, {
        "profile (car_scenic_base.json)": profile_verdict(row["tags"]), "ScenicKit (the fixture)": row["verdict"]})


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_profile_gives_the_fixture_verdict(row):
    got = profile_verdict(row["tags"])
    want = as_gate(expected(row, "profile")) if "profile" not in (row.get("divergent") or {}) \
        else row["divergent"]["profile"]
    assert got == want, disagreement(row, "PROFILE (car_scenic_base.json)", got, {
        "ETL (assemble.scored_row)": etl_verdict(row["tags"]), "ScenicKit (the fixture)": row["verdict"]})


def test_etl_and_profile_agree_on_every_gate():
    """The direct ETL-vs-profile comparison, outside the divergent rows: a disagreement names both."""
    bad = ["%s (way %s): ETL says %s, profile says %s"
           % (r["class"], r["way_id"], as_gate(etl_verdict(r["tags"])), profile_verdict(r["tags"]))
           for r in ROWS if "divergent" not in r
           and as_gate(etl_verdict(r["tags"])) != profile_verdict(r["tags"])]
    assert not bad, "the ETL and the profile disagree: " + "; ".join(bad)


def test_motorway_and_trunk_score_zero_and_are_routable_in_every_layer():
    """CLAUDE.md: penalized, never excluded. ZERO in the ETL, NOT_GATED in the profile, ZERO in the fixture."""
    rows = [r for r in ROWS if r["class"] in CORE_CLASSES[:4]]
    assert [r["class"] for r in rows] == CORE_CLASSES[:4]
    for r in rows:
        assert (r["verdict"], etl_verdict(r["tags"]), profile_verdict(r["tags"])) == (ZERO, ZERO, NOT_GATED), r


def test_the_fixture_is_the_briefs_table():
    """Every class once, in order, with its typed verdict; real rows carry an id, synthetic rows say so."""
    assert IDS == (list(CORE_CLASSES[:20]) + list(DIVERGENT_CLASSES) + list(CORE_CLASSES[20:])
                   + list(NEAR_MISS_CLASSES))
    assert len(IDS) == len(set(IDS)) == len(CORE_CLASSES) + len(DIVERGENT_CLASSES) + len(NEAR_MISS_CLASSES) == 33
    for row in ROWS:
        assert row["verdict"] == EXPECTED_VERDICT[row["class"]], row["class"]
        if row["way_id"] is None:
            assert row["source"].startswith("synthetic: 0 isolated ways"), row["class"]
        else:
            assert isinstance(row["way_id"], int) and row["source"].startswith("la canyon window"), row["class"]
    real = [r["way_id"] for r in ROWS if r["way_id"] is not None]
    assert len(real) == len(set(real)) == 23


def test_only_the_typed_classes_diverge():
    """R1: a divergent record anywhere else would be a way for a core gate to drift with the test green."""
    divergent = {r["class"]: r["divergent"] for r in ROWS if "divergent" in r}
    assert sorted(divergent) == sorted(DIVERGENT_CLASSES)
    for name, record_ in divergent.items():
        assert record_["profile"] == NOT_GATED and "etl" not in record_, name
        assert "T-0188" in record_["tracked_by"], name


def test_the_profile_read_is_the_shipped_file():
    shipped = pathlib.Path(__file__).resolve().parents[2] / "routing" / "profiles" / "car_scenic_base.json"
    assert profilegate.PROFILE == shipped and shipped.is_file()

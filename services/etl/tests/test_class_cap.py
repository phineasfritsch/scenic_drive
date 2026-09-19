"""T-0207: no residential, living_street or service way reaches the router's high band - on real rows.

THE DEFECT, measured (the task Log, 2026-09-19T11:38:11Z). Over the three real scored tables - canyon
11,740, grid-a 11,239, grid-b 23,474 ways - 131 residential and 109 service ways quantise to `scenic_score`
7 or more. The plan's anti-rat-run clause is `road_class == RESIDENTIAL && scenic_score < 7 -> 0.5`
(`services/api/src/customModel.ts:219`), so a residential way that REACHES 7 collects the high band and the
demotion never fires on it. The owner's bar is zero rat-runs.

WHAT THIS FILE BINDS TO. The shipping path production runs and nothing else: `assemble.scored_row` - the
symbol `assemble.assemble` calls for every way of a region - and then `tagwriter.tags_for_row`, the symbol
that puts the bytes on the way. Not `score.score` (the ceiling is deliberately NOT there: it would break the
`SegmentScore.swift` parity gate, task Log R1), not a helper, not a re-implementation of the quantiser: the
integer read below is the one `tagwriter` writes, parsed back out of the tag dict it returns.

THE ROWS ARE REAL. `fixtures/class_cap_rows.json` carries the nine real ways' own terms, recorded from the
three windows, plus ONE synthetic row (way 999999999999) whose reason is written in its own `why` field: no real
living_street in 46,453 ways reaches 6, so the class's ceiling would never be exercised by real data. Every
recorded score is re-derived here through `assemble.score_record`, so the fixture cannot drift into claiming
a number the scorer disowns.

THE CONTROLS ARE THE POINT. Mulholland Drive (secondary), Topanga Canyon Boulevard (primary, an ELIGIBLE
byway) and Franklin Canyon Drive (unclassified, ruled NOT capped) are asserted UNCHANGED, to the byte of
their unit tag. A cap that also moved them would be a cap on scenery instead of a cap on rat-runs.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from etl import assemble, tagwriter, way_record

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "class_cap_rows.json"

# The band the profile reads (`customModel.ts:215`, `scenic_score >= 7`). A capped class must stay below it.
ROUTER_HIGH_BAND = 7
CAPPED_CLASSES = ("residential", "living_street", "service")
EXACT = 1e-12

# The five real offenders T-0204's run put in the grid window's top ten, by id AND by name.
OFFENDERS = {13419334: "Crescent Drive", 632613339: "Sullivan Fire Road",
             13290126: "Sullivan Ridge Fire Road", 13379402: "Scenario Lane", 121304178: "Oakmont Street"}
# The ways that MUST NOT MOVE: id -> (integer score, unit tag as it ships).
UNCHANGED = {518410361: (7, "0.7361"), 74344132: (8, "0.7722"), 13292286: (7, "0.7203")}
# The R2 boundary row: an unrounded score a hair under a .x5 fourth decimal.
SYNTHETIC_WAY = 999999999999
BOUNDARY_WAY = 13332407
BOUNDARY_UNIT = "0.5500"


def rows() -> list:
    with FIXTURE.open(encoding="utf-8") as handle:
        return json.load(handle)["rows"]


def by_id() -> dict:
    return {row["way_id"]: row for row in rows()}


def record_for(row: dict) -> way_record.WayRecord:
    """The fixture row as the record `assemble` hands the scorer - its own terms, its own class."""
    return way_record.WayRecord(way_id=row["way_id"], highway=row["highway"],
                                terms_state=way_record.NORMALISED, surface=row["surface"],
                                byway_status=row["byway_status"], **row["terms"])


def tags_of(row: dict) -> dict:
    tags = {"highway": row["highway"]}
    if row["surface"] is not None:
        tags["surface"] = row["surface"]
    return tags


def shipped(row: dict) -> dict:
    """SHIPPING PATH: record -> `assemble.scored_row` -> `tagwriter.tags_for_row` -> the tags on the way."""
    return tagwriter.tags_for_row(assemble.scored_row(record_for(row), tags_of(row)))


def integer_of(tags: dict) -> int:
    return int(tags[tagwriter.KEY_SCORE])


def described(row: dict, tags: dict) -> str:
    return "%s (%s, way %d) ships %s=%s beside %s" % (
        row["name"] or "<unnamed>", row["highway"], row["way_id"], tagwriter.KEY_SCORE,
        tags[tagwriter.KEY_SCORE], tags[tagwriter.KEY_UNIT])


def test_the_fixture_rows_are_the_scores_the_shipping_scorer_still_produces():
    """The fixture is a RECORDING, so it is re-derived before anything is read off it."""
    checked = 0
    for row in rows():
        if row["recorded_score"] is None:
            continue
        got = assemble.score_record(record_for(row))
        assert got is not None and abs(got - row["recorded_score"]) < EXACT, (
            "way %d: the scorer now says %r, the fixture recorded %r" % (row["way_id"], got,
                                                                         row["recorded_score"]))
        checked += 1
    assert checked == 9, checked


def test_no_capped_class_way_reaches_the_routers_high_band():
    """THE DEFECT, by name. Red before the ceiling: five real ways ship 7."""
    escaped = []
    for row in rows():
        if row["highway"] not in CAPPED_CLASSES:
            continue
        tags = shipped(row)
        if integer_of(tags) >= ROUTER_HIGH_BAND:
            escaped.append(described(row, tags))
    assert escaped == [], (
        "%d %s way(s) reach scenic_score %d, so `road_class == RESIDENTIAL && scenic_score < 7 -> 0.5` "
        "never fires on them: %s" % (len(escaped), "/".join(CAPPED_CLASSES), ROUTER_HIGH_BAND,
                                     "; ".join(escaped)))


@pytest.mark.parametrize("way_id", sorted(OFFENDERS), ids=[OFFENDERS[k] for k in sorted(OFFENDERS)])
def test_each_measured_offender_was_a_seven_and_now_is_not(way_id):
    """Each of the five, one at a time: it really did reach 7, and it does not any more."""
    row = by_id()[way_id]
    assert row["name"] == OFFENDERS[way_id]
    assert row["highway"] in CAPPED_CLASSES
    assert tagwriter.quantise(row["recorded_score"]) >= ROUTER_HIGH_BAND, (
        "way %d no longer reaches %d before the ceiling - this row stopped being the defect's witness"
        % (way_id, ROUTER_HIGH_BAND))
    tags = shipped(row)
    assert integer_of(tags) < ROUTER_HIGH_BAND, described(row, tags)


def test_a_service_way_scores_zero_like_a_motorway_and_is_not_excluded():
    """The service ruling: 0 is a real score and the way is still in the table, still routable."""
    for way_id in (632613339, 13290126):
        row = by_id()[way_id]
        table_row = assemble.scored_row(record_for(row), tags_of(row))
        assert table_row["score"] == 0.0, table_row
        assert table_row["gate_reason"] is None, "a service way is not GATED - it is scored 0"
        tags = shipped(row)
        assert integer_of(tags) == 0 and tags[tagwriter.KEY_UNIT] == "0.0000", described(row, tags)


def test_a_living_street_is_capped_although_no_real_one_reaches_six():
    """The synthetic row, whose reason is in the fixture: the class is the only input that changed."""
    row = by_id()[SYNTHETIC_WAY]
    assert row["highway"] == "living_street"
    tags = shipped(row)
    assert integer_of(tags) < ROUTER_HIGH_BAND, described(row, tags)


@pytest.mark.parametrize("way_id", sorted(UNCHANGED))
def test_the_scenic_roads_do_not_move(way_id):
    """Mulholland, Topanga and Franklin Canyon Drive, to the byte of the unit tag."""
    row = by_id()[way_id]
    integer, unit = UNCHANGED[way_id]
    tags = shipped(row)
    assert (integer_of(tags), tags[tagwriter.KEY_UNIT]) == (integer, unit), described(row, tags)


def test_the_cap_is_class_aware_and_not_a_cap_on_the_terms():
    """Not vacuous: Crescent Drive's own terms, with the class changed to secondary, still ship a 7."""
    row = dict(by_id()[13419334], highway="secondary")
    tags = shipped(row)
    assert integer_of(tags) >= ROUTER_HIGH_BAND, described(row, tags)


def test_the_ceiling_is_the_boundary_of_the_high_band_read_through_the_shipping_quantiser():
    """The number is bound to `tagwriter.quantise` and to the band literal, never to prose."""
    ceiling = assemble.CLASS_SCORE_CEILING["residential"]
    assert tagwriter.quantise(float(tagwriter.fixed(ceiling))) == ROUTER_HIGH_BAND - 1
    assert tagwriter.quantise(ceiling + 0.0001) == ROUTER_HIGH_BAND, (
        "the ceiling is not AT the boundary: one step of the tag's own precision must cross into the band")
    assert set(assemble.CLASS_SCORE_CEILING) == set(CAPPED_CLASSES), assemble.CLASS_SCORE_CEILING
    assert assemble.CLASS_SCORE_CEILING["service"] == 0.0
    assert "unclassified" not in assemble.CLASS_SCORE_CEILING, (
        "unclassified is ruled NOT capped (task Log R1): Franklin Canyon Drive is a real drive")


def test_the_integer_and_the_unit_are_one_number_on_the_boundary_row():
    """R2, by name: way 13332407's 0.5499510668 rounds to 0.5500, which quantises to 6, not 5."""
    row = by_id()[BOUNDARY_WAY]
    tags = shipped(row)
    assert tags[tagwriter.KEY_UNIT] == BOUNDARY_UNIT, described(row, tags)
    assert integer_of(tags) == tagwriter.quantise(float(BOUNDARY_UNIT)), described(row, tags)
    assert integer_of(tags) == 6, described(row, tags)


def test_every_row_ships_an_integer_that_is_the_quantisation_of_the_unit_beside_it():
    """The hardened oracle's clause (`scenecheck.classify`), asserted at the writer instead of the read-back."""
    wrong = []
    for row in rows():
        tags = shipped(row)
        if tagwriter.quantise(float(tags[tagwriter.KEY_UNIT])) != integer_of(tags):
            wrong.append(described(row, tags))
    assert wrong == [], "; ".join(wrong)

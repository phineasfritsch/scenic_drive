"""The three-state surface rule, branch by branch, and the two places it has to agree with.

`test_corpus_schema.py` asserts the round trip - a residential way with no surface tag comes back as -1.
This file asserts the RULE, which is the part that can be wrong while the round trip is green: a rule that
answered PAVED for everything would round-trip perfectly.

Two agreements are asserted here rather than assumed:

  1. with score.py. `surface_state` must return UNKNOWN exactly when `score.raises_surface_unknown_flag` is
     true, for every (class, tag) pair in the cross product below. It is asserted rather than trusted even
     though surface.py calls that function, because the call could grow a condition around it.
  2. with the DDL. The CHECK constraint's domain is literal SQL text in schema.DDL (the DDL is an ordered
     tuple whose exact bytes are the artifact) and `SURFACE_STATES` is the same three values as data. A test
     is the only thing that can hold them together.

The unpaved set is the third agreement and it is the one this task cannot close: it is a copy of
Sources/ScenicKit/Gates/Gates.swift:80-82 across a language boundary, so it is asserted against seven values
typed out here - a third copy, deliberately, so a widening on either side has to pass a human.
"""
from __future__ import annotations

import pytest

from etl import schema, score, surface
from etl.extractway import way_from_json

# plan:80. The same seven values as Sources/ScenicKit/Gates/Gates.swift:80-82 `Gates.unpavedSurfaces`.
PLAN_UNPAVED = {"gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel"}

# Values that are NOT positive evidence of an unpaved road. `cobblestone` and `sett` are the interesting
# ones: they are rough, they are not smooth asphalt, and they are still paved roads a sedan may drive.
PAVED_VALUES = ("asphalt", "concrete", "paved", "cobblestone", "sett", "paving_stones", "chipseal")


def test_the_unpaved_set_is_the_plans_seven_values_and_nothing_else():
    assert surface.UNPAVED_SURFACES == PLAN_UNPAVED
    assert len(surface.UNPAVED_SURFACES) == 7


@pytest.mark.parametrize("highway", sorted(score.UNSURVEYED_CLASSES))
def test_an_absent_tag_on_an_unsurveyed_class_is_unknown(highway):
    assert surface.surface_state(highway=highway, surface=None) == surface.SURFACE_UNKNOWN


@pytest.mark.parametrize("highway", ("primary", "secondary", "tertiary", "motorway", "trunk", "service"))
def test_an_absent_tag_anywhere_else_is_paved(highway):
    """score.py:67-68: the plan's other half is this set's complement, 'expressed by omission'. A motorway
    scores 0 and is still PAVED - the score and the surface are different questions (CLAUDE.md)."""
    assert highway not in score.UNSURVEYED_CLASSES
    assert surface.surface_state(highway=highway, surface=None) == surface.SURFACE_PAVED


@pytest.mark.parametrize("tag", sorted(PLAN_UNPAVED))
@pytest.mark.parametrize("highway", ("residential", "unclassified", "secondary", "tertiary"))
def test_positive_evidence_wins_on_every_class(highway, tag):
    """A tagged `surface=gravel` residential is UNPAVED, not UNKNOWN: the tag is there and it says
    something. Order of the two branches, asserted on the class where they would otherwise collide."""
    assert surface.surface_state(highway=highway, surface=tag) == surface.SURFACE_UNPAVED


@pytest.mark.parametrize("tag", PAVED_VALUES)
@pytest.mark.parametrize("highway", ("residential", "secondary"))
def test_a_present_tag_that_is_not_unpaved_is_paved(highway, tag):
    assert surface.surface_state(highway=highway, surface=tag) == surface.SURFACE_PAVED


def test_unknown_is_exactly_score_pys_flag_over_the_whole_cross_product():
    """Agreement 1. Not "surface.py calls it", which a later edit can make false while both files still
    read correctly - the property is stated over every pair."""
    classes = ("primary", "secondary", "tertiary", "unclassified", "residential", "motorway", "track")
    tags = (None, "asphalt", "gravel", "cobblestone", "unpaved")
    for highway in classes:
        for tag in tags:
            state = surface.surface_state(highway=highway, surface=tag)
            flag = score.raises_surface_unknown_flag(highway=highway, surface=tag)
            assert (state == surface.SURFACE_UNKNOWN) == flag, (highway, tag, state, flag)


def test_the_ddl_domain_is_the_three_states_the_module_defines():
    """Agreement 2. The CHECK is literal SQL text and SURFACE_STATES is data; nothing but this holds them
    together, and the DDL may not be assembled from an f-string (schema.py, top)."""
    create = next(s for s in schema.DDL if s.startswith("CREATE TABLE osm_features"))
    assert "surface     INTEGER NOT NULL CHECK (surface   IN (-1,0,1))" in create
    assert "paved" not in create
    assert surface.SURFACE_STATES == (-1, 0, 1)
    assert sorted(surface.SURFACE_STATE_NAMES) == sorted(surface.SURFACE_STATES)
    assert surface.SURFACE_STATE_NAMES[surface.SURFACE_UNKNOWN] == "unknown"


def _raw(**over):
    way = {"id": 1, "cls": "residential", "highway": "residential", "access_ok": 1, "oneway": 0,
           "nodes": [[37.9, -122.6], [37.9, -122.59]]}
    way.update(over)
    return way


def test_an_extract_that_still_carries_paved_is_refused_by_name():
    """The retired key is a refusal, not a leftover to ignore. A stale extract's `paved: 0` ways are exactly
    the unpaved ones, and ignoring the key would turn every one of them into state 1 (PAVED) - a safety
    regression that no other test in this repository could see."""
    with pytest.raises(ValueError, match="retired key"):
        way_from_json(_raw(paved=0), "fixture")
    with pytest.raises(ValueError, match="retired key"):
        way_from_json(_raw(paved=1, surface="gravel"), "fixture")


def test_the_reader_carries_the_raw_tag_and_derives_the_state():
    assert way_from_json(_raw(), "fixture").surface is None
    assert way_from_json(_raw(), "fixture").surface_state == surface.SURFACE_UNKNOWN
    tagged = way_from_json(_raw(surface="gravel"), "fixture")
    assert tagged.surface == "gravel"
    assert tagged.surface_state == surface.SURFACE_UNPAVED


@pytest.mark.parametrize("bad", (1, "", [], {}))
def test_the_reader_refuses_a_surface_that_is_not_an_osm_tag_value(bad):
    with pytest.raises(ValueError, match="surface must be"):
        way_from_json(_raw(surface=bad), "fixture")

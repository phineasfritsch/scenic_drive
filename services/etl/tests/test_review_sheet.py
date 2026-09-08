"""A review sheet that emits an empty page is worse than no sheet: it reads as a clean review."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl import review_sheet as rs  # noqa: E402

SEGS = [
    {"id": "w/12", "name": "Mulholland Dr", "score": 5.2, "terms": {"curv": 0.71},
     "geometry": [[34.1289, -118.4043], [34.1301, -118.3990], [34.1310, -118.3941]]},
    {"id": "w/13", "name": "Sepulveda Blvd", "score": 4.4, "terms": {"curv": 0.11},
     "geometry": [[34.0736, -118.4630], [34.0745, -118.4585]]},
    {"id": "w/14", "name": "PCH", "score": 9.1, "terms": {"curv": 0.20},
     "geometry": [[34.0392, -118.5810], [34.0405, -118.5760]]},
    {"id": "w/15", "name": "access rd", "score": 2.0, "terms": {"curv": 0.02},
     "geometry": [[34.05, -118.44], [34.051, -118.44]]},
]


# Four tightly spaced points and then one far away, so the three candidate answers are different NODES:
# index 0 (the junction at the start), index 2 (the middle BY INDEX), index 3 (the middle BY LENGTH).
# Hand arithmetic, not read off the implementation: at this latitude 0.001 deg of longitude is 92.3 m, so
# the cumulative lengths are [0, 92.3, 184.6, 276.9, 9228] and half is 4614. |276.9 - 4614| = 4337 beats
# |9228 - 4614| = 4614, so the length midpoint is index 3 while the index midpoint is 2.
SKEWED = {"id": "w/20", "name": "four tight points then one far", "score": 5.0, "terms": {"curv": 0.5},
          "geometry": [[34.0, -118.0], [34.0, -117.999], [34.0, -117.998],
                       [34.0, -117.997], [34.0, -117.90]]}


def test_the_default_reviews_the_middle_not_the_extremes():
    """The point of the tool. The top and bottom of a ranking mostly confirm what anyone would guess; the
    score earns its keep where it placed something in the middle."""
    picked = {s["id"] for s in rs.select(SEGS, top=0, bottom=0, band=rs.REVIEW_BAND)}
    assert picked == {"w/12", "w/13"}
    assert "w/14" not in picked and "w/15" not in picked


def test_top_and_bottom_add_the_extremes_without_duplicating():
    got = rs.select(SEGS, top=1, bottom=1, band=rs.REVIEW_BAND)
    assert [s["id"] for s in got] == ["w/13", "w/12", "w/14", "w/15"]
    assert len({s["id"] for s in got}) == len(got), "a segment must not appear twice"


def test_every_row_says_why_it_was_picked():
    for s in rs.select(SEGS, top=1, bottom=1, band=rs.REVIEW_BAND):
        assert s["why"]


def test_unscored_segments_still_get_reviewed():
    """There is no composite score yet (T-0029). Reviewing the TERMS is answerable from a photograph, so
    the absence of a score must not silently produce an empty sheet."""
    bare = [{"id": "w/1", "terms": {"canopy": 0.82}, "geometry": [[34.0, -118.0], [34.001, -118.0]]}]
    got = rs.select(bare, top=0, bottom=0, band=rs.REVIEW_BAND)
    assert [s["id"] for s in got] == ["w/1"]
    assert got[0]["why"] == "unscored"


def pieces_of_one_way(n: int, **extra) -> list[dict]:
    """`n` segments that all carry the SAME OSM way id - the shape a scored corridor arrives in."""
    return [{"id": "w/12", "name": f"Mulholland Dr piece {i}",
             "terms": {"curv": 0.5}, "geometry": SEGS[0]["geometry"], **extra} for i in range(n)]


def test_select_keeps_every_piece_of_a_way_that_shares_one_id():
    """Deduplication was keyed on `id`, and nothing makes `id` unique per SEGMENT. Six pieces of Mulholland
    all keyed w/12 came out as ONE row, rendered, exit 0, no refusal - a corpus reviewed one row deep while
    the docstring above `select` said "Never silently truncates"."""
    got = rs.select(pieces_of_one_way(6), top=0, bottom=0, band=rs.REVIEW_BAND)
    assert len(got) == 6, "every piece is its own segment to look at, whatever its id says"
    assert [s["name"] for s in got] == [f"Mulholland Dr piece {i}" for i in range(6)]

    scored = pieces_of_one_way(6, score=5.0)
    assert len(rs.select(scored, top=0, bottom=0, band=rs.REVIEW_BAND)) == 6, "same collapse when scored"


def test_select_reviews_every_segment_that_has_no_id_at_all():
    """`render` writes `s.get("id", "?")`, so a segment with no id is explicitly contemplated one function
    below - while `select` gave them all the key None and kept the first."""
    bare = [{"terms": {"canopy": 0.8}, "geometry": SEGS[0]["geometry"]} for _ in range(5)]
    assert len(rs.select(bare, top=0, bottom=0, band=rs.REVIEW_BAND)) == 5


def test_a_selection_that_loses_matched_segments_refuses_rather_than_shortening_the_sheet(monkeypatch):
    """The floor is the population the criteria MATCHED, not "at least one row".

    `if not rows: raise` catches 400 -> 0 and waves through 400 -> 1, which is the same defect one row up
    and the one a corpus actually hits. Put the exact key that shipped (`id`) back and the guard has to fire
    rather than let a six-segment corpus go out as a one-row sheet.
    """
    six = pieces_of_one_way(6)
    monkeypatch.setattr(rs, "_position_key", lambda i, s: s.get("id"))   # the collapse that shipped
    with pytest.raises(ValueError, match="matched 6 segment.s. but kept 1"):
        rs.select(six, top=0, bottom=0, band=rs.REVIEW_BAND)
    monkeypatch.undo()
    assert len(rs.select(six, top=0, bottom=0, band=rs.REVIEW_BAND)) == 6


def test_empty_input_refuses():
    with pytest.raises(ValueError, match="refusing to emit an empty sheet"):
        rs.render([])


def test_a_selection_that_matches_nothing_refuses():
    """4 segments in and 0 out is not a clean review; it is a sheet nobody should be handed."""
    with pytest.raises(ValueError, match="none selected"):
        rs.render(SEGS, band=(7.5, 8.5))


def test_the_sheet_links_along_the_road_and_carries_a_verdict_control():
    html = rs.render(SEGS, band=rs.REVIEW_BAND)
    assert "https://www.google.com/maps/@?api=1&amp;map_action=pano" in html
    assert "heading=" in html
    for v in ("right", "wrong", "unsure"):
        assert f'value="{v}"' in html


def test_each_row_gets_its_own_radio_group_even_when_the_ids_repeat():
    """A browser groups radios by NAME. Named `v_<id>`, six pieces of w/12 - or six segments with no id,
    every one of them rendering "?" - are one group, so answering row 6 silently un-answers row 1."""
    html = rs.render(pieces_of_one_way(6, score=5.0), band=rs.REVIEW_BAND)
    names = set(re.findall(r'<input type="radio" name="([^"]+)"', html))
    assert len(names) == 6, f"six rows must be six radio groups, got {sorted(names)}"


# Anything that could carry a verdict off the page. If none of these is present, nothing on the sheet
# records anything, and the sheet has to say so.
RECORDING_MECHANISMS = ("<form", "<script", "localstorage", "download=", 'type="submit"')


def test_the_sheet_does_not_pretend_to_record_the_verdict():
    """Three radios that go nowhere look exactly like three radios that save. This test passes either way -
    build a real sink and it goes green on the other branch - and fails only if the page starts lying by
    dropping the notice while still recording nothing. Recording them is T-0117."""
    html = rs.render(SEGS, band=rs.REVIEW_BAND)
    if not any(t in html.lower() for t in RECORDING_MECHANISMS):
        assert "not recorded anywhere" in html, "the sheet must admit the verdicts go nowhere"
        assert rs.NOT_RECORDED_NOTICE in html


def test_the_sheet_stands_on_the_length_midpoint_not_on_a_junction():
    """The whole point of the tool, and until now it was held up by a docstring and an HTML sentence.

    `render` called `look_along(pts, midpoint_index(pts))`; changing that to `look_along(pts, 0)` left all
    25 tests green while every link opened on the FIRST node of the way - a junction, which looks like every
    other junction. `midpoint_index` was pinned as a unit; the one place the property matters was not.

    w/12 is the only fixture with three points (the other three short-circuit to index 0 at two points).
    Its legs are ~506 m and ~463 m, so the middle node sits 22 m from the half-length and either end sits
    485 m from it: the middle node is the answer by a wide margin, and the ends are not.
    """
    html = rs.render(SEGS, band=rs.REVIEW_BAND)
    assert "viewpoint=34.130100,-118.399000" in html, "w/12 must be viewed from its middle node"
    assert "34.128900,-118.404300" not in html, "that is w/12's first node - the junction it starts at"
    assert "34.131000,-118.394100" not in html, "that is w/12's last node - the junction it ends at"


def test_the_sheet_uses_the_length_midpoint_and_not_the_index_midpoint():
    """A way whose nodes are bunched at one end: standing on the middle INDEX still stands in the bunch."""
    html = rs.render([SKEWED], band=rs.REVIEW_BAND)
    assert "viewpoint=34.000000,-117.997000" in html, "index 3 is the middle by length"
    assert "-117.998000" not in html, "index 2 is the middle by index, inside the bunched end"
    assert "-118.000000" not in html and "-117.900000" not in html, "neither end of the way"


def test_the_sheet_never_requests_an_image():
    """The licensing argument is that this emits a link a person opens, never an image request. Pinned as a
    test because 'just show the thumbnail' is the obvious next feature and it is the one that would make the
    app's map stack a licensing problem."""
    html = rs.render(SEGS, top=2, bottom=2)
    assert "streetview" not in html.lower()
    assert "key=" not in html
    assert "<img" not in html.lower()


def test_a_segment_without_geometry_says_so_rather_than_linking_nowhere():
    html = rs.render([{"id": "w/9", "score": 5.0}], band=rs.REVIEW_BAND)
    assert "no geometry" in html
    assert "maps/@" not in html


def test_html_is_escaped():
    html = rs.render([{"id": "w/1", "name": '<script>x</script>', "score": 5.0,
                       "geometry": [[34.0, -118.0], [34.001, -118.0]]}], band=rs.REVIEW_BAND)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_cli_rejects_an_unknown_argument_rather_than_ignoring_it():
    assert rs.main([str(Path(__file__)), "--nope"]) == 2


def test_cli_rejects_a_flag_with_no_value():
    assert rs.main([str(Path(__file__)), "--top"]) == 2

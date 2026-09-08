"""A review sheet that emits an empty page is worse than no sheet: it reads as a clean review."""
from __future__ import annotations

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

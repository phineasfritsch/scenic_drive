"""T-0438 (owner, 2026-11-24): trunk is scored like any other road; only motorway and motorway_link carry 0.

WHY. PCH is OSM `highway=trunk`. With trunk in the zero set Palisades Beach Rd (7.5 km) and Malibu PCH
(300 of 347 sampled points) scored 0 and no coastal plan could pass the honest-failure bar. US mappers use
trunk for regionally important highways, many two-lane and scenic: the tag says network importance, not
freeway-ness. Motorway is still 0 and still routable - penalised, never excluded (CLAUDE.md).

Each test binds to a shipping symbol: `score.score` (the scorer every row goes through), the record's
`is_zero_class` and `normalise.normalise_region` (the rank population), `assemble.assemble` (the table the
graph is built from), and `waydoc.build` (which decides what a way's motorway distance is measured to).
"""
from __future__ import annotations

import math
import pathlib
import tempfile

from etl import assemble, byways, normalise, score, waydoc, way_record as wr

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
CLIP = FIXTURES / "scenic_clip.osm.xml"
CANYON_WAY = 101      # shares node 14 with the clip's one motorway, way 102 (test_motorway_source.py)
CLIP_MOTORWAY = 102

TERMS = {"curvature": 0.5, "elevation_gain": 0.5, "speed_fit": 0.5, "sinuosity": 0.5, "canopy": 0.5,
         "relief": 0.5, "impervious": 0.5, "points_of_interest": 0.5, "water": 0.5, "furniture": 0.5}
RAW_TERMS = {"curvature": 640.0, "elevation_gain": 300.0, "relief": 180.0, "sinuosity": 1.4, "furniture": 0.1}
MAPPED = {"canopy": 0.5, "impervious": 0.25, "water": 0.1, "speed_fit": 0.6}


def raw(way_id: int, highway: str, **kw) -> wr.WayRecord:
    return wr.WayRecord(way_id=way_id, highway=highway, **{**RAW_TERMS, **MAPPED, **kw})


def test_the_zero_classes_are_the_two_motorway_classes():
    assert byways.SCENIC_ZERO_CLASSES == frozenset({"motorway", "motorway_link"})


def test_a_trunk_way_with_scenic_terms_scores_above_zero_and_a_motorway_does_not():
    """The same terms on every class: trunk equals the formula a secondary gets, motorway stays exactly 0."""
    secondary = score.score(highway="secondary", surface="asphalt", **TERMS)
    assert secondary > 0.0
    for highway in ("trunk", "trunk_link"):
        assert score.score(highway=highway, surface="asphalt", **TERMS) == secondary, highway
        assert score.score(highway=highway, surface="asphalt", byway_status=byways.DESIGNATED,
                           **TERMS) > secondary, highway
    for highway in ("motorway", "motorway_link"):
        assert score.score(highway=highway, surface="asphalt", byway_status=byways.DESIGNATED,
                           **TERMS) == 0.0, highway


def test_a_trunk_way_is_in_the_normalise_population():
    """A trunk way is ranked (NORMALISED) and moves the other ways' ranks; a motorway is EXCLUDED."""
    region = [raw(1, "secondary", curvature=100.0), raw(2, "trunk", curvature=300.0),
              raw(3, "trunk_link", curvature=200.0), raw(4, "motorway", curvature=900.0)]
    assert [r.is_zero_class for r in region] == [False, False, False, True]
    assert [r.way_id for r in normalise.population_of(region)] == [1, 2, 3]
    out = {r.way_id: r for r in normalise.normalise_region(region)}
    assert [out[i].terms_state for i in (1, 2, 3, 4)] == [wr.NORMALISED] * 3 + [wr.EXCLUDED]
    # n = 3, no ties: (0+0.5)/3, (1+0.5)/3, (2+0.5)/3. With trunk excluded way 1 would be alone at 0.5.
    assert [out[i].curvature for i in (1, 3, 2)] == [0.5 / 3, 1.5 / 3, 2.5 / 3]
    assert score.score(**out[2].score_kwargs()) > 0.0
    assert score.score(**out[4].score_kwargs()) == 0.0


def test_the_assembled_table_scores_a_trunk_way_and_counts_it_out_of_the_zero_classes():
    """Through `waydoc.build` -> `assemble.assemble`: the clip's motorway retagged trunk is scored and routable."""
    doc = _clip_doc(highway_of_102="trunk")
    rows = {row["way_id"]: row for row in assemble.assemble(doc)}
    assert rows[CLIP_MOTORWAY]["score"] > 0.0, rows[CLIP_MOTORWAY]
    assert rows[CLIP_MOTORWAY]["gate_reason"] is None
    assert rows[CLIP_MOTORWAY]["terms_state"] == wr.NORMALISED
    control = {row["way_id"]: row for row in assemble.assemble(_clip_doc(highway_of_102="motorway"))}
    assert control[CLIP_MOTORWAY]["score"] == 0.0 and control[CLIP_MOTORWAY]["gate_reason"] is None


def test_a_way_beside_a_trunk_is_not_near_a_motorway():
    """The x0.7 "within 150 m of a motorway" multiplier measures to motorways only, so PCH's own side
    streets - and PCH itself - are not penalised for being near a trunk. Control: the same clip with the
    shared-node neighbour tagged motorway answers exactly 0.0."""
    assert _distance(_clip_doc(highway_of_102="motorway"), CANYON_WAY) == 0.0
    assert _distance(_clip_doc(highway_of_102="trunk"), CANYON_WAY) == math.inf
    assert _distance(_clip_doc(highway_of_102="trunk_link"), CANYON_WAY) == math.inf


def _clip_doc(*, highway_of_102: str) -> dict:
    """scenic_clip.osm.xml with its one motorway (way 102) tagged `highway_of_102`, built by waydoc.build."""
    text = CLIP.read_bytes().decode("utf-8")
    assert text.count('<tag k="highway" v="motorway"/>') == 1
    with tempfile.TemporaryDirectory() as tmp:
        clip = pathlib.Path(tmp) / "clip.osm.xml"
        clip.write_bytes(text.replace('<tag k="highway" v="motorway"/>',
                                      '<tag k="highway" v="%s"/>' % highway_of_102).encode("utf-8"))
        return waydoc.build(clip, region_id="la", elevation=lambda pts: [100.0 + i for i, _ in enumerate(pts)],
                            landcover=lambda pts: [10] * len(pts))


def _distance(doc: dict, way_id: int) -> float:
    """The document spells "no motorway within the horizon" as the JSON string "Infinity"."""
    return float({row["way_id"]: row for row in doc["ways"]}[way_id]["meters_to_nearest_motorway"])

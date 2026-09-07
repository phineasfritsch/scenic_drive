"""The three conditions that decide which oracle ways are comparable, tested in isolation.

This file exists because it did not. `oracle_select.py`'s selection logic had no coverage of its own - the
only thing exercising it was the end-to-end 2%-agreement assertion, which passes or fails for a hundred
reasons and cannot tell you that a tag was excluded for a mechanism that could not apply to it. That is
exactly the shape of the `oneway` defect agent/reviewer-30 found: 77 of 264 exclusions made for a squash
processor that structurally cannot fire on a single-way collection, sitting in the tree with a green suite.

An exclusion condition is the easiest place in this repo to hide a cherry-pick, so each one gets a test that
names the mechanism it is standing in for.
"""
from __future__ import annotations

import json
import math

from etl import oracle_select as sel


def test_the_selection_constants_are_pinned_against_literals():
    """Same defect as MAX_RADIUS and RAD_EARTH_M, in this module: every other assertion about these derives
    its expected value from the constant itself, so sweeping one moves both sides and fails nothing.
    agent/reviewer-34 swept them - `SQUASH_RADIUS_M` changes 6 ways and `CELL_DEG` changes 0, neither enough
    to move the 2% agreement rate off its floor. Literals, therefore, and only literals.

    30 m is `--distance 30`, which every squash step in adams_default.sh uses. 1 m is "a node that moved less
    than a metre is the same node re-rounded". CELL_DEG is a grid cell of about 55 m of latitude, chosen so
    the proximity test is not O(ways x nodes) - it is an optimisation, and an optimisation that changes the
    answer is a bug, which is what `test_the_proximity_grid_finds_a_node_across_a_cell_boundary` guards.
    """
    assert sel.SQUASH_RADIUS_M == 30.0
    assert sel.GEOMETRY_TOL_M == 1.0
    assert sel.CELL_DEG == 0.0005
    # The grid cell must stay comfortably larger than the radius it accelerates, or the 3x3 neighbourhood
    # search stops covering the circle and starts missing tagged nodes.
    assert sel.CELL_DEG * 111320 > sel.SQUASH_RADIUS_M


def test_oneway_does_not_mark_a_way_as_squash_exposed():
    """The regression guard for the defect this file was written for.

    `squash_curvature_near_way_tag_change --tag oneway` squashes where the tag CHANGES BETWEEN ADJACENT WAYS
    in a collection. Condition 1 admits only single-way collections, so there is no adjacent way and the
    processor cannot fire. Excluding on the tag's mere presence dropped 77 of 264 exclusions - and dropped
    them from the population the headline agreement figure is computed over, which is how a selection bug
    turns into a wrong number rather than a missing one.
    """
    assert not sel.way_is_squash_tagged({"highway": "residential", "oneway": "yes"})
    assert not sel.way_is_squash_tagged({"oneway": "-1"})
    assert "oneway" not in sel.WAY_TAGS


def test_junction_is_matched_on_its_values_not_on_the_bare_key():
    """`squash_curvature_for_tagged_ways --tag junction --values roundabout,circular` is value-restricted.

    Matching the bare key excludes junction=yes, junction=jughandle and anything else somebody tags, none of
    which that processor touches. Zero ways in the current Vermont set carry any junction tag, so this has no
    effect on today's number - it is here so that the module's stated principle, exclusions defined by the
    SOURCE of the squash, is actually enforced rather than merely written down.
    """
    assert sel.way_is_squash_tagged({"junction": "roundabout"})
    assert sel.way_is_squash_tagged({"junction": "circular"})
    assert not sel.way_is_squash_tagged({"junction": "yes"})
    assert not sel.way_is_squash_tagged({"junction": "jughandle"})


def test_traffic_calming_matches_any_value_because_its_processor_does():
    assert sel.way_is_squash_tagged({"traffic_calming": "table"})
    assert sel.way_is_squash_tagged({"traffic_calming": "anything_at_all"})


def test_parking_lane_matches_on_the_prefix():
    """Broader than the source's value-restricted regex, and deliberately so: it can only ever exclude MORE,
    never admit a way the published pipeline squashed. 0 ways affected in the current set."""
    assert sel.way_is_squash_tagged({"parking:lane:right": "parallel"})
    assert not sel.way_is_squash_tagged({"parking": "lane"})


def test_an_ordinary_road_is_not_squash_tagged():
    assert not sel.way_is_squash_tagged({"highway": "residential", "name": "Elm St", "surface": "asphalt"})


def _grid(points):
    return sel.node_grid(points)


def test_a_tagged_node_within_thirty_metres_excludes_the_way():
    lat, lon = 44.0, -72.8
    dlat = 25.0 / (6373000 * math.pi / 180)          # 25 m north, inside the 30 m radius
    assert sel.near_tagged_node([(lat, lon)], _grid([(lat + dlat, lon)]))


def test_a_tagged_node_beyond_thirty_metres_does_not():
    lat, lon = 44.0, -72.8
    dlat = 45.0 / (6373000 * math.pi / 180)
    assert not sel.near_tagged_node([(lat, lon)], _grid([(lat + dlat, lon)]))


def test_the_thirty_metre_radius_is_a_circle_and_not_an_ellipse():
    """Without cos(latitude) an east-west offset reads shorter than it is, so a node 25 m east of the way
    would be missed while one 25 m north is caught. At 44 N that is a 28% error - the tolerance would be an
    ellipse, and which ways got excluded would depend on their compass orientation."""
    lat, lon = 44.0, -72.8
    deg_lat = 25.0 / (6373000 * math.pi / 180)
    deg_lon = deg_lat / math.cos(math.radians(lat))   # the same 25 m, going east
    assert sel.near_tagged_node([(lat, lon)], _grid([(lat + deg_lat, lon)]))
    assert sel.near_tagged_node([(lat, lon)], _grid([(lat, lon + deg_lon)]))


def test_the_proximity_grid_finds_a_node_across_a_cell_boundary():
    """The grid is an optimisation, and an optimisation that changes the answer is a bug. A node just over a
    cell edge is still within 30 m and must still be found."""
    lat = math.floor(44.0 / sel.CELL_DEG) * sel.CELL_DEG   # exactly on a cell boundary
    lon = -72.8
    dlat = 10.0 / (6373000 * math.pi / 180)
    assert sel.near_tagged_node([(lat + dlat, lon)], _grid([(lat - dlat, lon)]))


def test_geometry_differing_by_more_than_a_metre_is_a_different_road():
    a = [(44.0, -72.8), (44.001, -72.8)]
    far = [(44.0, -72.8), (44.001 + 5.0 / (6373000 * math.pi / 180), -72.8)]
    near = [(44.0, -72.8), (44.001 + 0.5 / (6373000 * math.pi / 180), -72.8)]
    assert sel.same_geometry(a, near), "half a metre is the same node re-rounded"
    assert not sel.same_geometry(a, far)


def test_a_way_with_a_different_node_count_is_never_the_same_geometry():
    a = [(44.0, -72.8), (44.001, -72.8)]
    assert not sel.same_geometry(a, a + [(44.002, -72.8)])


def test_load_export_reads_lat_lon_in_the_right_order(tmp_path):
    """osmium writes [lon, lat]. Reading them the other way round silently halves every distance at this
    latitude, which would quietly shrink the 30 m radius to about 21 m and change the population."""
    path = tmp_path / "e.geojsonseq"
    path.write_text(json.dumps({
        "type": "Feature", "id": "w123",
        "geometry": {"type": "LineString", "coordinates": [[-72.8, 44.0], [-72.79, 44.01]]},
        "properties": {"highway": "residential"},
    }) + "\n", encoding="utf-8")
    ways, props, tagged = sel.load_export(path)
    assert ways[123][0] == (44.0, -72.8)
    assert props[123]["highway"] == "residential"
    assert tagged == []


def test_load_export_collects_only_nodes_carrying_a_squash_tag(tmp_path):
    path = tmp_path / "e.geojsonseq"
    rows = [
        {"type": "Feature", "id": "n1", "geometry": {"type": "Point", "coordinates": [-72.8, 44.0]},
         "properties": {"highway": "traffic_signals"}},
        {"type": "Feature", "id": "n2", "geometry": {"type": "Point", "coordinates": [-72.81, 44.01]},
         "properties": {"highway": "turning_circle"}},          # not in NODE_TAGS' value list
        {"type": "Feature", "id": "n3", "geometry": {"type": "Point", "coordinates": [-72.82, 44.02]},
         "properties": {"barrier": "gate"}},                    # any value
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    _, _, tagged = sel.load_export(path)
    assert tagged == [(44.0, -72.8), (44.02, -72.82)]

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

from etl import curvature as cv
from etl import oracle_select as sel
from tests import oracle_kmz as ok


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


def test_load_export_reads_a_plain_geojson_collection_and_the_shapes_the_format_allows(tmp_path):
    r"""`load_export`'s two opening guards and its three `or` defaults, none of which had been reached.

    The guards are why one reader takes `-f geojsonseq` AND `-f geojson`: a FeatureCollection's opening
    `{"type": "FeatureCollection", "features": [` starts with `{` and is not valid JSON on its own, so the
    `except json.JSONDecodeError: continue` skips it; its closing `]}` does not start with `{`; and each
    member line's trailing comma is what `rstrip(",")` removes. Every export the suite had written was a few
    clean objects with no commas, so all of that was dead code under test - `ops/etl-mutation` turned the
    JSONDecodeError guard into `pass` with the suite green.

    The `or {}` defaults are RFC 7946, not paranoia: a Feature's `geometry` MAY be null and its `properties`
    MAY be null, and an export produced without `--add-unique-id=type_id` carries no `id` at all. All three
    shapes are here, and a way is still read out of the file around them.

    The `or ""` on the id is the one this case does NOT kill, and the attempt is what showed why. The
    reasoning was that dropping it leaves an id-less feature as `str(None)`, and that `"None".startswith("n")`
    would then collect it as a tagged node - but `str(None)` is `"None"` with a capital N, so it begins with
    neither `"w"` nor `"n"` and both branches skip it exactly as the empty string does. Every id that reaches
    a branch is a string beginning `w` or `n`, whose `str()` is itself; every falsy one stringifies to
    something that reaches neither. That mutation is equivalent, and it is recorded as one rather than chased.
    """
    members = [
        json.dumps({"type": "Feature", "id": "w1", "geometry": None,
                    "properties": {"highway": "residential"}}),
        json.dumps({"type": "Feature", "id": "w2",
                    "geometry": {"type": "LineString", "coordinates": [[-72.8, 44.0], [-72.79, 44.01]]},
                    "properties": None}),
        json.dumps({"type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-72.8, 44.0]},
                    "properties": {"highway": "traffic_signals"}}),
    ]
    path = tmp_path / "e.geojson"
    path.write_text('{"type": "FeatureCollection", "features": [\n' + ",\n".join(members) + "\n]}\n",
                    encoding="utf-8")

    ways, props, tagged = sel.load_export(path)
    assert sorted(ways) == [2], "the only readable way is the one that has a LineString"
    assert ways[2][0] == (44.0, -72.8)
    assert props[2] == {}, "a null `properties` must arrive as an empty dict, not as None"
    assert tagged == [], "a feature with no id is not a node, whatever its geometry reads like"


# --------------------------------------------------------------------------- condition 0: is it comparable
# `eligible()` opens with the line that decides whether a published way can be looked at at all:
#
#     if not ours or not theirs or len(ours) < 3:
#         continue
#
# `ops/etl-mutation` dropped any ONE of those three operands, and flipped the `or` to `and`, with the suite
# green - four survivors at oracle_select.py:153, plus the `continue` itself at :154. This is E4's
# neighbourhood: E4, the first evasion that beat T-0074, was deleting `or near_tagged_node(ours, grid)` six
# lines further down, and it worked because every export the suite wrote made that operand a no-op. The same
# thing is true here for a different reason - every export the suite wrote contained every published way,
# with the KML's own geometry, three vertices long - so all three operands were dead code under test.
#
# Each operand therefore gets its own negative case, driven against a well-formed neighbour in the same KMZ.
# The neighbour is what makes the assertion sharp: `have_geometry == 1` says the probe was excluded HERE,
# where `kept == []` alone could not tell exclusion from a funnel that was empty to begin with.

GOOD_WAY = 111
PROBE_WAY = 222
GOOD_COORDS = [(44.0, -72.8), (44.001, -72.8), (44.002, -72.8)]
PROBE_COORDS = [(44.1, -72.8), (44.101, -72.8), (44.102, -72.8)]
TWO_VERTICES = [(44.1, -72.8), (44.101, -72.8)]


def _funnel_with_probe(tmp_path, probe_block, probe_export):
    """`eligible()` over one good collection plus one probe, and the probe is what the case is about."""
    kmz = ok.write_kmz(tmp_path / "probe.kmz",
                       ok.collection(GOOD_WAY, GOOD_COORDS), probe_block)
    export = ok.write_export(tmp_path / "probe.geojsonseq",
                             ways=[ok.road(GOOD_WAY, GOOD_COORDS)] + probe_export)
    return sel.eligible(export, kmz)


def _assert_only_the_good_way_survived(kept, stages):
    assert stages["single_way"] == 2, "both collections must be published, or the probe tests nothing"
    assert stages["have_geometry"] == 1, "the probe got past the comparability guard"
    assert [w["way_id"] for w in kept] == [GOOD_WAY]


def test_a_published_way_the_export_never_returned_is_not_comparable(tmp_path):
    """`not ours`, and it is the operand that handles the ORDINARY case, not a corrupt one.

    `osmium getid` exits 1 for ids that are not in the extract, after writing a complete file for every id it
    did find - 21 of 3318 for the pinned pair, because the KMZ was generated from an older OSM snapshot -
    and `ops/etl-curvature-fixture` deliberately carries on rather than treating that as failure. So
    `ways.get(way_id)` returning None happens on every real rebuild. Without this operand it is `len(None)`,
    and the rebuild dies on input it was designed to tolerate.
    """
    kept, stages = _funnel_with_probe(
        tmp_path, ok.collection(PROBE_WAY, PROBE_COORDS), [])
    _assert_only_the_good_way_survived(kept, stages)


def test_a_way_the_kml_carries_no_geometry_for_is_not_comparable(tmp_path):
    """`not theirs`. A Placemark can hold a constituent-ways table and no `<LineString>`, and
    `kml_geometry` skips it - so the way is published but the geometry Curvature computed over was not.

    Condition 2 is the comparison against THAT geometry: the module's own note is that 726 of 3297 ways
    differ from it and agree 29.6% of the time against 90.4% for unchanged geometry. With nothing to compare
    against there is no condition 2, and admitting the way anyway is admitting a way on two conditions out
    of three while the fixture goes on claiming three.
    """
    kept, stages = _funnel_with_probe(
        tmp_path,
        ok.placemark("Probe Road", ways=(PROBE_WAY,), coords=None),
        [ok.road(PROBE_WAY, PROBE_COORDS)])
    _assert_only_the_good_way_survived(kept, stages)


def test_a_way_of_fewer_than_three_vertices_is_not_comparable(tmp_path):
    """`len(ours) < 3`. A radius needs three points. `assign_radii` says so explicitly - a way with a single
    segment is given `MAX_RADIUS`, which is above every band in `LEVELS`, so its curvature is 0 by
    construction and not by measurement. Comparing there is agreeing that 0 == 0, and counting that into the
    headline percentage is counting a way that tested none of the five steps as evidence about all of them.
    """
    kept, stages = _funnel_with_probe(
        tmp_path,
        ok.collection(PROBE_WAY, TWO_VERTICES),
        [ok.road(PROBE_WAY, TWO_VERTICES)])
    _assert_only_the_good_way_survived(kept, stages)
    assert cv.way_curvature(TWO_VERTICES) == 0, "a single-segment way is MAX_RADIUS, which scores nothing"

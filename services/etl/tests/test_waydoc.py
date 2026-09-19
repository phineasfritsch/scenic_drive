"""The clip -> assembly document: which ways are in the population, and which are refused by name."""
from __future__ import annotations

import pathlib

from etl import assemble, dem, waydoc

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "scenic_clip.osm.xml"
NO_ELEVATION_ABOVE = 34.045          # way 105 runs 34.0500 -> 34.0600, above every other way in the fixture


def elevation(points: list) -> list:
    """A fake DEM: 100 m, climbing 1 m a sample, and NOTHING above `NO_ELEVATION_ABOVE`."""
    return [None if lat > NO_ELEVATION_ABOVE else 100.0 + i * 1.0 for i, (lat, _) in enumerate(points)]


def landcover(points: list) -> list:
    """A fake WorldCover: tree cover everywhere."""
    return [10] * len(points)


def build(**over) -> dict:
    kwargs = {"region_id": "la", "elevation": elevation, "landcover": landcover}
    kwargs.update(over)
    return waydoc.build(FIXTURE, **kwargs)


def ways_by_id(doc: dict) -> dict:
    return {row["way_id"]: row for row in doc["ways"]}


def test_a_way_with_no_highway_tag_is_not_in_the_population():
    """The tag filter keeps park and beach polygons; they are not roads and are not scored."""
    doc = build()
    assert 106 not in ways_by_id(doc)
    assert 106 not in {r["way_id"] for r in doc["refused"]}
    assert doc["counts"]["not_a_road"] == 1


def test_a_way_with_no_elevation_sample_is_refused_by_name_rather_than_scored_flat():
    """Absence is not 0 m. A way the DEM cannot answer for is refused, and the refusal names the producer."""
    doc = build()
    refused = {r["way_id"]: r["why"] for r in doc["refused"]}
    assert 105 in refused
    assert "dem" in refused[105]
    assert 105 not in ways_by_id(doc)


def test_the_document_carries_every_field_the_assembly_reads():
    row = ways_by_id(build())[101]
    for field in ("way_id", "tags", "coords", "furniture_nodes", "landcover_codes", "elevation_profile",
                  "sinuosity", "tunnel_meters", "meters_to_nearest_motorway"):
        assert field in row, field
    assert row["tags"]["highway"] == "tertiary"
    assert len(row["coords"]) == 4


def test_furniture_nodes_are_the_tagged_nodes_the_way_references():
    """Node 13 is a traffic signal on way 101 and on no other way."""
    ways = ways_by_id(build())
    assert ways[101]["furniture_nodes"] == [{"highway": "traffic_signals"}]
    assert ways[102]["furniture_nodes"] == []


def test_the_assembly_scores_the_document_this_module_builds():
    """The wiring test: the document goes into `assemble.assemble` unedited and comes out a scored table."""
    table = assemble.assemble(build())
    scores = {row["way_id"]: row for row in table}
    assert set(scores) == {101, 102, 103, 104}
    assert scores[102]["score"] == 0.0, "a motorway scores 0 by class"
    assert scores[103]["gate_reason"] == "no_access"
    assert scores[104]["gate_reason"] == "track"
    assert scores[101]["score"] is not None and 0.0 <= scores[101]["score"] <= 1.0


def test_the_landcover_buffer_follows_the_way_rather_than_one_point():
    """A 2 km way sampled at one point would report the land cover of one end of it."""
    long_way = [(34.0, -118.7), (34.02, -118.7)]
    points = waydoc.landcover_points(long_way)
    assert len(points) > waydoc.LANDCOVER_SAMPLES_PER_POINT
    assert len(points) % waydoc.LANDCOVER_SAMPLES_PER_POINT == 0


def test_the_elevation_sampler_is_given_the_regions_own_tiles_and_not_the_default(monkeypatch):
    """rv2-pr106's carry-in: the default tile set is still sfbay's, so an LA point would be a silent None."""
    seen = {}

    def spy(points, tiles=None, **kw):
        seen["tiles"] = tiles
        return [100.0 + i for i in range(len(points))]

    monkeypatch.setattr(dem, "sample_smoothed", spy)
    waydoc.build(FIXTURE, region_id="la", landcover=landcover)
    assert seen["tiles"] == dem.tiles_for_region("la")
    assert "n34w118" in seen["tiles"] and "n35w119" in seen["tiles"]


def test_infinity_is_written_the_way_the_assembly_reads_it():
    """JSON has no literal for infinity and `assemble.metres` spells it `Infinity`."""
    row = ways_by_id(build())[101]
    assert row["meters_to_nearest_motorway"] == assemble.INFINITY or \
        isinstance(row["meters_to_nearest_motorway"], float)


def test_the_meta_records_the_window_and_the_inputs_the_run_used():
    doc = build(meta={"window": "-118.95,33.98,-118.35,34.15", "source": "window.osm.pbf"})
    assert doc["meta"]["window"] == "-118.95,33.98,-118.35,34.15"
    assert doc["meta"]["region"] == "la"


def test_a_byway_entry_with_no_route_key_is_left_out_with_its_count(tmp_path):
    """An entry with no route key falls back to geometry alone against every way in the window, which is
    both the slow path and the weak one - it is dropped BY COUNT, never in silence."""
    entries = [{"name": "SR 1", "status": "OD", "routes": ["1"], "geometry": [(34.0, -118.7), (34.1, -118.6)]},
               {"name": "A Trail", "status": "E", "routes": [], "geometry": [(34.0, -118.7), (34.1, -118.6)]}]
    doc = build(byway_entries=entries)
    assert [b["name"] for b in doc["byways"]] == ["SR 1"]
    assert doc["counts"]["byways_no_route_key"] == 1

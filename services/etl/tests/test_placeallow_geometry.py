"""R6's missing-geometry rule over EVERY position, through the SHIPPING entry point (T-0266, rv1 B1).

`python -m etl.extractadapter --places-osm` (its `main`) runs over a small OSM XML written per row: a control
viewpoint node that is always kept, member ways 10/11/12 (nodes 1-3, 4-6, 7-9) and one subject - relation
r/500 (beach) or way w/600 (park) - with the row's nodes and ways LEFT OUT of the stream. Each row asserts the
WHOLE `places` array and the WHOLE PLACES count line by exact equality to typed literals: a missing member way
or node at the first, middle or last position, every one missing, a member way whose own node is missing, an
empty relation, an inner-only relation, an absent INNER way (inner is ignored, so that relation is KEPT), and
the complete controls. A node is its own point: OSM XML gives every node its lat/lon, so the node path has no
missing case (ruled in the task Log).
"""
from __future__ import annotations

import json

import pytest

from etl import extractadapter

WAYDOC = {"region": "la", "ways": [{"way_id": 1, "tags": {"highway": "residential", "name": "Fixture Rd"},
                                    "coords": [[34.0, -118.0], [34.001, -118.001]]}]}
NODES = {1: (34.01, -118.01), 2: (34.02, -118.02), 3: (34.03, -118.03), 4: (34.04, -118.04),
         5: (34.05, -118.05), 6: (34.06, -118.06), 7: (34.07, -118.07), 8: (34.08, -118.08),
         9: (34.09, -118.09), 100: (34.5, -118.5)}
WAYS = {10: (1, 2, 3), 11: (4, 5, 6), 12: (7, 8, 9), 13: (1, 5, 9)}
CONTROL_TAGS = (("tourism", "viewpoint"), ("name", "Control Point"))
BEACH_TAGS = (("type", "multipolygon"), ("natural", "beach"), ("name", "Partial Beach"))
PARK_TAGS = (("leisure", "park"), ("name", "Partial Park"))
OUTER3 = (("way", 10, "outer"), ("way", 11, "outer"), ("way", 12, "outer"))

CONTROL = {"osm_type": "n", "osm_id": 100, "cls": "viewpoint", "name": "Control Point",
           "lat": 34.5, "lon": -118.5}
BEACH = {"osm_type": "r", "osm_id": 500, "cls": "beach", "name": "Partial Beach", "lat": 34.05, "lon": -118.05}
PARK = {"osm_type": "w", "osm_id": 600, "cls": "park", "name": "Partial Park", "lat": 34.02, "lon": -118.02}

SKIPPED = ("PLACES places=1 unnamed=0 refused_access=0 chain=0 skipped_geometry=1 deduped=0 viewpoint=1 "
           "peak=0 waterfall=0 beach=0 trailhead=0 museum=0 cafe=0 garden=0 park=0 town=0")
KEPT_BEACH = ("PLACES places=2 unnamed=0 refused_access=0 chain=0 skipped_geometry=0 deduped=0 viewpoint=1 "
              "peak=0 waterfall=0 beach=1 trailhead=0 museum=0 cafe=0 garden=0 park=0 town=0")
KEPT_PARK = ("PLACES places=2 unnamed=0 refused_access=0 chain=0 skipped_geometry=0 deduped=0 viewpoint=1 "
             "peak=0 waterfall=0 beach=0 trailhead=0 museum=0 cafe=0 garden=0 park=1 town=0")

# id: (nodes left out, ways left out, relation r/500 members | None, way w/600 node refs | None,
#      the whole places array, the whole count line)
ROWS = {
    "relation-complete": ((), (), OUTER3, None, [CONTROL, BEACH], KEPT_BEACH),
    "relation-first-member-way-absent": ((), (10,), OUTER3, None, [CONTROL], SKIPPED),
    "relation-middle-member-way-absent": ((), (11,), OUTER3, None, [CONTROL], SKIPPED),
    "relation-last-member-way-absent": ((), (12,), OUTER3, None, [CONTROL], SKIPPED),
    "relation-every-member-way-absent": ((), (10, 11, 12), OUTER3, None, [CONTROL], SKIPPED),
    "relation-member-way-node-absent": ((5,), (), OUTER3, None, [CONTROL], SKIPPED),
    "relation-empty": ((), (), (), None, [CONTROL], SKIPPED),
    "relation-inner-only": ((), (), (("way", 13, "inner"),), None, [CONTROL], SKIPPED),
    "relation-inner-way-absent-is-ignored": ((), (13,), OUTER3 + (("way", 13, "inner"),), None,
                                             [CONTROL, BEACH], KEPT_BEACH),
    "way-complete": ((), (), None, (1, 2, 3), [CONTROL, PARK], KEPT_PARK),
    "way-first-node-absent": ((1,), (), None, (1, 2, 3), [CONTROL], SKIPPED),
    "way-middle-node-absent": ((2,), (), None, (1, 2, 3), [CONTROL], SKIPPED),
    "way-last-node-absent": ((3,), (), None, (1, 2, 3), [CONTROL], SKIPPED),
    "way-every-node-absent": ((1, 2, 3), (), None, (1, 2, 3), [CONTROL], SKIPPED),
    "way-no-nodes": ((), (), None, (), [CONTROL], SKIPPED),
}


def tags_xml(tags) -> str:
    return "".join('<tag k="%s" v="%s"/>' % kv for kv in tags)


def stream(omit_nodes, omit_ways, members, refs) -> str:
    parts = ["<?xml version='1.0' encoding='UTF-8'?>\n<osm version=\"0.6\">"]
    for nid, (lat, lon) in NODES.items():
        if nid not in omit_nodes:
            body = tags_xml(CONTROL_TAGS) if nid == 100 else ""
            parts.append('<node id="%d" lat="%r" lon="%r">%s</node>' % (nid, lat, lon, body))
    for wid, nds in WAYS.items():
        if wid not in omit_ways:
            parts.append('<way id="%d">%s</way>' % (wid, "".join('<nd ref="%d"/>' % n for n in nds)))
    if refs is not None:
        parts.append('<way id="600">%s%s</way>' % ("".join('<nd ref="%d"/>' % n for n in refs),
                                                   tags_xml(PARK_TAGS)))
    if members is not None:
        parts.append('<relation id="500">%s%s</relation>' % (
            "".join('<member type="%s" ref="%d" role="%s"/>' % m for m in members), tags_xml(BEACH_TAGS)))
    return "".join(parts) + "</osm>\n"


@pytest.mark.parametrize("row", list(ROWS), ids=list(ROWS))
def test_missing_geometry_at_every_position_is_skipped_and_counted(tmp_path, capsys, row):
    omit_nodes, omit_ways, members, refs, places, line = ROWS[row]
    osm = tmp_path / "places.osm.xml"
    osm.write_text(stream(omit_nodes, omit_ways, members, refs), encoding="utf-8")
    waydoc = tmp_path / "doc.json"
    waydoc.write_text(json.dumps(WAYDOC), encoding="utf-8")
    out = tmp_path / "extract.json"
    assert extractadapter.main(["--input", str(waydoc), "--places-osm", str(osm), "--out", str(out)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert json.loads(out.read_text(encoding="utf-8"))["places"] == places
    assert lines[-1] == line

"""T-0241 A2/A3: landmarks.select over the whole input cross product, and landmarks.elevation_m at every bound.

Every row's expected output is a FUNCTION of its variant (expected() below), compared by full equality, and
test_every_dimension_moves_an_output proves no dimension of the product is ignored by that function.
"""
from __future__ import annotations

import itertools
import math

import pytest

from etl import landmarks, placeallow

OSM_TYPES = ("n", "w", "r")
TAGS = {"viewpoint": {"tourism": "viewpoint"}, "peak": {"natural": "peak"}, "other": {"amenity": "bench"}}
NAMES = ("present", "missing", "blank")
ELES = {"absent": None, "851": 851.0, "1234 m": 1234.0, "4000 ft": 1219.2, "garbage": None}
ACCESS = ("open", "private")
DIMENSIONS = (OSM_TYPES, tuple(TAGS), NAMES, tuple(ELES), ACCESS)
VARIANTS = list(itertools.product(*DIMENSIONS))
# R3, written as the literal it is: a viewpoint is a node or a way, a peak only a node, nothing a relation.
LANDMARK_TYPES = {"viewpoint": "nw", "peak": "n"}
WAY_NODES = 3


def origin(index: int) -> tuple:
    """A point per variant with 7 decimals, so the 5-dp rounding is visible in every row."""
    return (34.0 + index * 0.001 + 0.0000037, -118.6 - index * 0.001 - 0.0000064)


def way_points(index: int) -> list:
    lat, lon = origin(index)
    return [(lat + k * 0.00002, lon + k * 0.00003) for k in range(WAY_NODES)]


def object_id(index: int) -> int:
    return 1000 + index


def tags_of(index: int, variant: tuple) -> dict:
    _osm_type, tag, name, ele, access = variant
    tags = dict(TAGS[tag])
    if name == "present":
        tags["name"] = "Place %d" % index
    elif name == "blank":
        tags["name"] = " \t "
    if ele != "absent":
        tags["ele"] = ele
    if access == "private":
        tags["access"] = "private"
    return tags


def tag_xml(tags: dict) -> str:
    return "".join('<tag k="%s" v="%s"/>' % (k, v) for k, v in tags.items())


def write_osm(tmp_path, variants: list) -> str:
    nodes, ways, relations = [], [], []
    for index, variant in enumerate(variants):
        osm_type = variant[0]
        tags = tag_xml(tags_of(index, variant))
        oid = object_id(index)
        if osm_type == "n":
            lat, lon = origin(index)
            nodes.append('<node id="%d" lat="%.7f" lon="%.7f">%s</node>' % (oid, lat, lon, tags))
            continue
        refs = []
        for k, (lat, lon) in enumerate(way_points(index)):
            ref = 900000 + index * 10 + k
            refs.append(ref)
            nodes.append('<node id="%d" lat="%.7f" lon="%.7f"/>' % (ref, lat, lon))
        nds = "".join('<nd ref="%d"/>' % r for r in refs + refs[:1])
        if osm_type == "w":
            ways.append('<way id="%d">%s%s</way>' % (oid, nds, tags))
        else:
            ways.append('<way id="%d">%s</way>' % (800000 + index, nds))
            relations.append('<relation id="%d"><member type="way" ref="%d" role="outer"/>%s</relation>'
                             % (oid, 800000 + index, tags))
    path = tmp_path / "landmarks.osm.xml"
    path.write_text('<osm version="0.6">%s</osm>' % "".join(nodes + ways + relations), encoding="utf-8")
    return str(path)


def expected_point(index: int, osm_type: str) -> tuple:
    if osm_type == "n":
        lat, lon = origin(index)
        lat, lon = float("%.7f" % lat), float("%.7f" % lon)
    else:
        points = [(float("%.7f" % a), float("%.7f" % b)) for a, b in way_points(index)]
        lat = round(sum(p[0] for p in points) / WAY_NODES, 7)
        lon = round(sum(p[1] for p in points) / WAY_NODES, 7)
    return round(lat, 5), round(lon, 5)


def landmark_kind(variant: tuple):
    osm_type, tag = variant[0], variant[1]
    return tag if osm_type in LANDMARK_TYPES.get(tag, "") else None


def expected(index: int, variant: tuple):
    """The one landmark this variant becomes, or the count it lands in."""
    osm_type, _tag, name, ele, access = variant
    kind = landmark_kind(variant)
    if kind is None:
        return None
    if access == "private":
        return "refused_access"
    lat, lon = expected_point(index, osm_type)
    return {"osm_type": osm_type, "osm_id": object_id(index), "kind": kind,
            "name": "Place %d" % index if name == "present" else None, "ele_m": ELES[ele], "lat": lat, "lon": lon}


def test_select_equals_the_cross_product_oracle(tmp_path):
    got, counts = landmarks.select(write_osm(tmp_path, VARIANTS))
    rows = [expected(i, v) for i, v in enumerate(VARIANTS)]
    want = sorted((r for r in rows if isinstance(r, dict)), key=lambda r: ("nwr".index(r["osm_type"]), r["osm_id"]))
    assert got == want
    assert counts == {"landmarks": len(want), "named": sum(1 for r in want if r["name"] is not None),
                      "refused_access": rows.count("refused_access"), "skipped_geometry": 0}
    assert len(want) == 3 * 5 * 3  # nv, wv, np x 5 eles x 3 names, open access only


def test_every_dimension_moves_an_output():
    for dim, values in enumerate(DIMENSIONS):
        moved = False
        for index, variant in enumerate(VARIANTS):
            for value in values:
                other = variant[:dim] + (value,) + variant[dim + 1:]
                if expected(index, other) != expected(index, variant):
                    moved = True
        assert moved, "dimension %d never changes an expected row" % dim


def test_landmark_types_are_placeallows_rows():
    rows = {row.cls: row.types for row in placeallow.ALLOWLIST if row.cls in landmarks.KINDS}
    assert rows == LANDMARK_TYPES
    assert landmarks.KINDS == ("viewpoint", "peak")


@pytest.mark.parametrize("osm_type,tags,kind", [
    ("n", {"tourism": "viewpoint", "natural": "peak"}, "viewpoint"),
    ("n", {"natural": "peak", "amenity": "cafe"}, "peak"),
    ("w", {"tourism": "viewpoint", "leisure": "park"}, "viewpoint"),
    ("w", {"natural": "peak", "leisure": "park"}, None),
    ("n", {"waterway": "waterfall"}, None),
    ("n", {"tourism": "museum"}, None),
    ("r", {"tourism": "viewpoint"}, None),
    ("n", {"tourism": "Viewpoint"}, None),
    ("n", {}, None),
])
def test_kind_of_first_row_decides(osm_type, tags, kind):
    assert landmarks.kind_of(osm_type, tags) == kind


@pytest.mark.parametrize("access,kept", [("private", False), ("no", False), ("yes", True),
                                         ("permissive", True), ("customers", True), ("Private", True)])
def test_access_refusal_is_placeallows_set(tmp_path, access, kept):
    path = tmp_path / "a.osm.xml"
    path.write_text('<osm><node id="5" lat="34.1" lon="-118.6"><tag k="tourism" v="viewpoint"/>'
                    '<tag k="access" v="%s"/></node></osm>' % access, encoding="utf-8")
    got, counts = landmarks.select(str(path))
    assert (len(got), counts["refused_access"]) == ((1, 0) if kept else (0, 1))


def test_a_way_with_a_missing_node_is_skipped_and_counted(tmp_path):
    path = tmp_path / "s.osm.xml"
    path.write_text('<osm><node id="1" lat="34.1" lon="-118.6"/><node id="2" lat="34.2" lon="-118.7"/>'
                    '<way id="9"><nd ref="1"/><nd ref="2"/><nd ref="3"/><tag k="tourism" v="viewpoint"/></way>'
                    '<way id="8"><nd ref="1"/><nd ref="2"/><tag k="tourism" v="viewpoint"/></way></osm>',
                    encoding="utf-8")
    got, counts = landmarks.select(str(path))
    assert got == [{"osm_type": "w", "osm_id": 8, "kind": "viewpoint", "name": None, "ele_m": None,
                    "lat": 34.15, "lon": -118.65}]
    assert counts == {"landmarks": 1, "named": 0, "refused_access": 0, "skipped_geometry": 1}


def test_output_sorted_nodes_then_ways_then_by_id(tmp_path):
    path = tmp_path / "o.osm.xml"
    path.write_text('<osm><node id="7" lat="34.1" lon="-118.6"><tag k="natural" v="peak"/></node>'
                    '<node id="3" lat="34.2" lon="-118.6"><tag k="natural" v="peak"/></node>'
                    '<way id="1"><nd ref="7"/><nd ref="3"/><tag k="tourism" v="viewpoint"/></way></osm>',
                    encoding="utf-8")
    got, _ = landmarks.select(str(path))
    assert [(g["osm_type"], g["osm_id"]) for g in got] == [("n", 3), ("n", 7), ("w", 1)]


@pytest.mark.parametrize("raw,metres", [
    ("851", 851.0), ("851.26", 851.3), ("0", 0.0), ("-12", -12.0), ("-12.5 m", -12.5), (" 851 ", 851.0),
    ("1234 m", 1234.0), ("1234m", 1234.0), ("1234  m", 1234.0), ("4000 ft", 1219.2), ("4000ft", 1219.2),
    ("1 ft", 0.3), ("10 ft", 3.0), ("1000 ft", 304.8), ("2792 ft", 851.0),
    ("", None), ("   ", None), (None, None), (851, None), (851.0, None), ("garbage", None), ("m", None),
    ("ft", None), ("851 meters", None), ("851 M", None), ("851 FT", None), ("4000 feet", None),
    ("4000'", None), ("1,234", None), ("1.234,5", None), ("851;900", None), ("851 900", None),
    ("851-900", None), ("nan", None), ("NaN", None), ("inf", None), ("-inf", None), ("1e3", None),
    ("+851", None), (".5", None), ("5.", None), ("851 m m", None), ("851 km", None), ("~851", None),
    ("851\n", 851.0), ("\t851 ft", 259.4),
])
def test_elevation_m_every_bound(raw, metres):
    got = landmarks.elevation_m(raw)
    assert got == metres and (got is None or math.isfinite(got))
    assert (got is None) == (metres is None)

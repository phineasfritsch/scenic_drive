"""T-0241 A4/A5: landmarks.explain over the T1 recorded routes, the 300 m bound, nearest_way_id, and the
whitelist that keeps landmarks out of every scoring module.

The landmarks are REAL: fixtures/t1_landmarks.osm.xml is every LA viewpoint/peak node within 1 km of a T1 path,
cut from the clip measured in the task Log (generate_t1_landmarks.py). The paths are the recorded GraphHopper
replies under Tests/Fixtures/t0239/topanga-malibu, read as they are.
"""
from __future__ import annotations

import io
import json
import math
import pathlib
import tokenize

import pytest

from etl import geom, landmarks

ETL = pathlib.Path(__file__).resolve().parents[1]
ROOT = ETL.parents[1]
T1 = ROOT / "Tests" / "Fixtures" / "t0239" / "topanga-malibu"
FIXTURE = ETL / "tests" / "fixtures" / "t1_landmarks.osm.xml"
STUNT = "Stunt Road Viewpoint"
BROWN = "David M. Brown Overlook"
# Measured (task Log, 2026-10-16): what each recorded T1 geometry passes within 300 m, keyed by point count.
T1_EXPECTED = {478: [], 923: [], 866: [], 1145: [STUNT], 1215: [STUNT], 1393: [STUNT, BROWN]}
PER_M = 1.0 / (geom.DEG * geom.RAD_EARTH_M)


def t1_paths() -> list:
    out = []
    for name in sorted(T1.glob("*.json")):
        for index, path in enumerate(json.loads(name.read_text(encoding="utf-8"))["paths"]):
            out.append((name.name, index, [(lat, lon) for lon, lat in path["points"]["coordinates"]]))
    return out


def lm(name, lat, lon, osm_id=1, kind="viewpoint"):
    return {"osm_type": "n", "osm_id": osm_id, "kind": kind, "name": name, "ele_m": None, "lat": lat, "lon": lon}


LINE = [(34.0, -118.6), (34.0, -118.5)]


def test_t1_every_recorded_path_names_what_it_passes():
    selected, counts = landmarks.select(str(FIXTURE))
    assert counts == {"landmarks": 25, "named": 7, "refused_access": 0, "skipped_geometry": 0}
    paths = t1_paths()
    assert len(paths) == 25
    got = {(name, index): landmarks.explain(route, selected) for name, index, route in paths}
    want = {(name, index): T1_EXPECTED[len(route)] for name, index, route in paths}
    assert got == want


def test_t1_stunt_road_names_stunt_road_viewpoint_and_the_fastest_names_nothing():
    selected, _ = landmarks.select(str(FIXTURE))
    fastest = json.loads((T1 / "fastest.json").read_text(encoding="utf-8"))["paths"][0]["points"]["coordinates"]
    stunt = json.loads((T1 / "alternatives-lambda-4.json").read_text(encoding="utf-8"))["paths"][2]
    stunt = stunt["points"]["coordinates"]
    assert landmarks.explain([(b, a) for a, b in stunt], selected) == [STUNT]
    assert landmarks.explain([(b, a) for a, b in fastest], selected) == []


def test_saddle_peak_is_beyond_300_m_of_t1_r8():
    selected, _ = landmarks.select(str(FIXTURE))
    saddle = [s for s in selected if s["name"] == "Saddle Peak"]
    assert [(s["kind"], s["ele_m"]) for s in saddle] == [("peak", 851.0)]
    nearest = min(geom.point_to_polyline_m((saddle[0]["lat"], saddle[0]["lon"]), route) for _, _, route in t1_paths())
    assert 400.0 < nearest < 500.0


def test_near_m_is_300_and_299_in_301_out():
    assert landmarks.NEAR_M == 300.0 and landmarks.MAX_NAMED == 2
    near, far = lm("Near", 34.0 + 299 * PER_M, -118.55, 1), lm("Far", 34.0 + 301 * PER_M, -118.55, 2)
    assert landmarks.explain(LINE, [near, far]) == ["Near"]
    assert landmarks.explain(LINE, [lm("South", 34.0 - 299 * PER_M, -118.55)]) == ["South"]


@pytest.mark.parametrize("delta_m", [0.0, 37.5, 299.9])
def test_explain_bound_is_inclusive(monkeypatch, delta_m):
    place = lm("Edge", 34.0 + delta_m * PER_M, -118.55)
    distance = geom.point_to_segment_m((place["lat"], place["lon"]), LINE[0], LINE[1])
    monkeypatch.setattr(landmarks, "NEAR_M", distance)
    assert landmarks.explain(LINE, [place]) == ["Edge"]
    monkeypatch.setattr(landmarks, "NEAR_M", math.nextafter(distance, -math.inf))
    assert landmarks.explain(LINE, [place]) == []


def test_explain_orders_by_route_position_caps_at_two_and_says_a_name_once():
    route = [(34.0, -118.60), (34.0, -118.58), (34.0, -118.56), (34.0, -118.54)]
    late_close = lm("Late", 34.0 + 5 * PER_M, -118.545, 1)
    early_far = lm("Early", 34.0 + 250 * PER_M, -118.595, 2)
    middle = lm("Middle", 34.0 + 100 * PER_M, -118.57, 3)
    again = lm("EARLY", 34.0 + 10 * PER_M, -118.57, 4)
    unnamed = lm(None, 34.0, -118.599, 5)
    assert landmarks.explain(route, [late_close, early_far]) == ["Early", "Late"]
    assert landmarks.explain(route, [late_close, middle, early_far]) == ["Early", "Middle"]
    assert landmarks.explain(route, [late_close, again, early_far]) == ["Early", "Late"]
    assert landmarks.explain(route, [unnamed, late_close]) == ["Late"]
    assert landmarks.explain(route, [late_close, middle, early_far, again, unnamed]) == ["Early", "Middle"]


def test_explain_same_leg_breaks_on_distance_then_id():
    a, b = lm("A", 34.0 + 50 * PER_M, -118.55, 9), lm("B", 34.0 + 20 * PER_M, -118.55, 8)
    assert landmarks.explain(LINE, [a, b]) == ["B", "A"]
    c, d = lm("C", 34.0 + 20 * PER_M, -118.55, 9), lm("D", 34.0 + 20 * PER_M, -118.55, 8)
    assert landmarks.explain(LINE, [c, d]) == ["D", "C"]


def test_explain_degenerate_routes():
    assert landmarks.explain([], [lm("X", 34.0, -118.55)]) == []
    assert landmarks.explain([(34.0, -118.55)], [lm("X", 34.0 + 10 * PER_M, -118.55)]) == ["X"]
    assert landmarks.explain([(34.0, -118.55)], [lm("X", 34.0 + 301 * PER_M, -118.55)]) == []
    assert landmarks.explain(LINE, []) == []


def test_nearest_way_id_bound_ties_and_none(monkeypatch):
    point = (34.0 + 120 * PER_M, -118.55)
    far = [(34.0 + 450 * PER_M, -118.6), (34.0 + 450 * PER_M, -118.5)]
    assert landmarks.nearest_way_id(point, []) is None
    assert landmarks.nearest_way_id(point, [(5, far)]) is None
    assert landmarks.nearest_way_id(point, [(7, LINE), (3, LINE), (5, far)]) == 3
    assert landmarks.nearest_way_id(point, [(3, far), (7, LINE)]) == 7
    closer = [(34.0 + 100 * PER_M, -118.6), (34.0 + 100 * PER_M, -118.5)]
    assert landmarks.nearest_way_id(point, [(1, LINE), (9, closer)]) == 9
    assert landmarks.nearest_way_id((34.0 + 299 * PER_M, -118.55), [(4, LINE)]) == 4
    assert landmarks.nearest_way_id((34.0 + 301 * PER_M, -118.55), [(4, LINE)]) is None
    distance = geom.point_to_polyline_m(point, LINE)
    monkeypatch.setattr(landmarks, "NEAR_M", distance)
    assert landmarks.nearest_way_id(point, [(4, LINE)]) == 4
    monkeypatch.setattr(landmarks, "NEAR_M", math.nextafter(distance, -math.inf))
    assert landmarks.nearest_way_id(point, [(4, LINE)]) is None


def code_mentions(path: pathlib.Path) -> bool:
    """True when an identifier or a string literal in `path` names a landmark. Comments never count."""
    text = path.read_text(encoding="utf-8")
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type in (tokenize.NAME, tokenize.STRING) and "landmark" in token.string.lower():
            return True
    return False


def test_no_module_but_landmarks_names_a_landmark():
    """A5 / R10, a WHITELIST: score.py and every module that builds its terms stay blind to landmarks."""
    modules = sorted((ETL / "etl").rglob("*.py"))
    assert len(modules) > 40
    named = [p.relative_to(ETL).as_posix() for p in modules if code_mentions(p)]
    assert named == ["etl/landmarks.py"]

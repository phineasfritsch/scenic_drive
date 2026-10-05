#!/usr/bin/env python3
"""Writes T-0263's shared reach fixtures (R5, R6). Run from anywhere: python Tests/Fixtures/t0263/make-fixture.py

isochrone.json + points.json: the parity fixture. A body as the Worker's /isochrone handler emits it (T-0262 R7):
minutes 90, buckets 15/30/45 one way with round_trip_minutes 30/60/90, on a grid of 1/64 degree from
(34.0, -118.5) so every vertex is an exact binary decimal. Each point's expected minutes is HAND-RULED from even-odd
ray casting's edge semantics (a crossing counts when exactly one endpoint lies strictly above the point and the point
lies strictly left of the crossing): a left or bottom edge is in, a right or top edge is out. The d06-d08 points sit
on a diagonal edge at a coordinate that is not exact, so their answer is whatever the last ulp gives - ruled by the
TS reference (services/api/src/surpriseReach.ts), which the Swift port must then match.

la-reach.json: R6's end-to-end body over T-0253's candidates (Tests/Fixtures/surprise/candidates.tsv).
"""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def at(i: float, j: float) -> list:
    """Grid units -> GeoJSON [lon, lat]."""
    return [-118.5 + i / 64, 34.0 + j / 64]


def ring(units) -> list:
    return [at(i, j) for i, j in units]


B15 = [[(4, 4), (8, 4), (8, 8), (4, 8), (4, 4)]]
B30 = [[(1, 2), (11, 1), (12, 10), (6, 13), (0, 9), (1, 2)],
       [(9, 4), (10, 4), (10, 6), (9, 6), (9, 4)],
       [(7, 7), (10, 8), (7, 10), (7, 7)]]
B45 = [[(-2, -2), (15, -1), (16, 8), (13, 16), (2, 15), (-3, 6), (-2, -2)]]
# The 45's hole is NOT on the grid: 5-decimal vertices, as GraphHopper writes them, so the crossing's rounding
# depends on the IEEE expression order - the d09+ points sit where `a * b / c` and `a * (b / c)` round apart.
HOLE45 = [[-118.29843, 34.16719], [-118.27771, 34.17342], [-118.27618, 34.20633], [-118.29766, 34.20155],
          [-118.29843, 34.16719]]


def bucket(minutes: int, rings) -> dict:
    return {"minutes": minutes, "round_trip_minutes": 2 * minutes,
            "polygon": {"type": "Polygon", "coordinates": [ring(r) for r in rings]}}


# (name, i, j, expected round-trip minutes or None, why) - i is east, j is north, in grid units.
GRID = [
    ("p01", 6, 6, 30, "inside the 15 square"),
    ("p02", 5, 5, 30, "inside the 15 square"),
    ("p03", 4.5, 7.5, 30, "inside the 15 square near its top-left corner"),
    ("p04", 7.5, 7.5, 30, "in the 15 AND in the 30's triangular hole: the smallest containing bucket wins"),
    ("p05", 2, 5, 60, "in the 30 outer ring, outside the 15"),
    ("p06", 10, 2, 60, "in the 30 near its slanted bottom and right edges"),
    ("p07", 3, 10, 60, "in the 30 above the 15; the ray meets the (12,10) vertex once"),
    ("p08", 9.5, 5, 90, "in the 30's square hole: the 45 holds it"),
    ("p09", 8, 8.5, 90, "in the 30's triangular hole above the 15: the 45 holds it"),
    ("p10", 14, 4, 90, "in the 45 only"),
    ("p11", 13.5, 12, None, "in the 45's hole and no other bucket"),
    ("p12", 20, 5, None, "east of every bucket"),
    ("p13", -5, 0, None, "west of every bucket"),
    ("p14", 6, 20, None, "north of every bucket"),
    ("p15", 6, -5, None, "south of every bucket"),
    ("p16", 1, 14, None, "just west of the 45's slanted north-west edge"),
    ("p17", 2, 14, 90, "just inside the 45's slanted north-west edge, above the 30"),
    ("p18", 0, 3, 90, "west of the 30's slanted west edge, inside the 45"),
    ("p19", 11, 12, 90, "north-east of the 30, inside the 45"),
    ("e01", 4, 6, 30, "on the 15's west edge: a left edge is in"),
    ("e02", 8, 6, 60, "on the 15's east edge: a right edge is out, the 30 holds it"),
    ("e03", 6, 4, 30, "on the 15's south edge: a bottom edge is in"),
    ("e04", 6, 8, 60, "on the 15's north edge: a top edge is out, the 30 holds it"),
    ("v01", 4, 4, 30, "the 15's south-west vertex is in"),
    ("v02", 8, 8, 90, "the 15's north-east vertex is out, and it is in the 30's triangular hole"),
    ("v03", 4, 8, 60, "the 15's north-west vertex is out"),
    ("v04", 8, 4, 60, "the 15's south-east vertex is out"),
    ("v05", 11, 1, 90, "the 30's lowest vertex is out"),
    ("v06", 12, 10, 90, "the 30's eastmost vertex is out"),
    ("v07", 6, 13, 90, "the 30's northmost vertex is out"),
    ("v08", 0, 9, 60, "the 30's westmost vertex is in: the east edge crosses the ray"),
    ("v09", 1, 2, 60, "the 30's south-west vertex is in"),
    ("h01", 9, 5, 90, "on the square hole's west edge: in the hole, so out of the 30"),
    ("h02", 10, 5, 60, "on the square hole's east edge: not in the hole"),
    ("h03", 9.5, 4, 90, "on the square hole's south edge: in the hole"),
    ("h04", 9.5, 6, 60, "on the square hole's north edge: not in the hole"),
    ("h05", 9, 4, 90, "the square hole's south-west vertex: in the hole"),
    ("h06", 10, 6, 60, "the square hole's north-east vertex: not in the hole"),
    ("h07", 13, 12, None, "just east of the 45 hole's slanted west edge (12.93 at this latitude): no bucket"),
    ("h08", 14, 12, None, "just west of the 45 hole's slanted east edge (14.27 at this latitude): no bucket"),
    ("o01", -2, -2, None, "the 45's south-west vertex is out"),
    ("o02", 16, 8, None, "the 45's eastmost vertex is out"),
    ("o03", 13, 16, None, "the 45's northmost vertex is out"),
    ("d01", 6.5, -1.5, None, "on the 45's slanted south edge where it is the east boundary: exact, out"),
    ("d02", 6, 1.5, 60, "on the 30's slanted south edge where it is the west boundary: exact, in"),
    ("d03", 11.5, 5.5, 90, "on the 30's slanted east edge: exact, out of the 30"),
    ("d04", 8.5, 9, 60, "on the triangular hole's hypotenuse, its east boundary: not in the hole"),
    ("d05", -0.5, 10.5, 90, "on the 45's slanted north-west edge, its west boundary: exact, in"),
    ("d06", 11 + 2 / 9, 3, 90, "on the 30's slanted east edge at an inexact coordinate: the reference's last ulp"),
    ("d07", -3 + 5 / 9, 7, 90, "on the 45's slanted north-west edge at an inexact coordinate: the reference's last ulp"),
    ("d08", 4 / 7, 5, 60, "on the 30's slanted west edge at an inexact coordinate: the reference's last ulp"),
]

# (name, lat, lon, expected, why) - decimal literals as a client would see them, not on the grid.
DECIMAL = [
    ("r01", 34.0522, -118.4437, 60, "grid (3.60, 3.34): in the 30, west of the 15"),
    ("r02", 34.1, -118.4, 30, "grid (6.4, 6.4): in the 15"),
    ("r03", 34.2, -118.3, 90, "grid (12.8, 12.8): just west of the 45's hole (13..14), inside the 45"),
    ("r08", 34.19, -118.29, None, "grid (13.44, 12.16): in the 45's hole and no other bucket"),
    ("d09", 34.1706021, -118.28708189213482, None, "ON the 45 hole's south edge where (xj-xi)*(lat-yi)/(yj-yi) and "
     "(xj-xi)*((lat-yi)/(yj-yi)) round apart: the reference's order puts it in the hole"),
    ("d10", 34.2045883, -118.28400671882846, None, "ON the 45 hole's north edge where the two orders round apart: "
     "the reference's order leaves it in the hole"),
    ("d11", 34.1956847, -118.29779144007567, 90, "ON the 45 hole's west edge where the two orders round apart: "
     "the reference's order puts it outside the hole, inside the 45"),
    ("r04", 33.99, -118.45, 90, "grid (3.2, -0.64): below the 30, inside the 45"),
    ("r05", 34.13, -118.37, 90, "grid (8.32, 8.32): in the 30's triangular hole, above the 15"),
    ("r06", 34.0, -118.5, 90, "grid (0, 0): the origin, below the 30's west vertex, inside the 45"),
    ("r07", 34.25, -118.25, None, "grid (16, 16): north-east of every bucket"),
]

LA_BOXES = [  # (one-way minutes, south, west, north, east)
    (15, 34.05, -118.45, 34.16, -118.35),
    (30, 34.00, -118.55, 34.20, -118.25),
    (45, 33.95, -118.65, 34.25, -118.10),
    (60, 33.80, -118.75, 34.30, -118.05),
    (75, 33.75, -118.80, 34.40, -117.95),
    (90, 33.70, -118.90, 34.45, -117.80),
]
LA_HOLE_30 = (34.10, -118.30, 34.15, -118.26)  # over griffith-09 (34.1126, -118.2822)


def box(s: float, w: float, n: float, e: float) -> list:
    """A ring around the box, each side moved 0.00005 deg so no 4-decimal candidate lies on an edge."""
    s, w, n, e = (round(v + 0.00005, 5) for v in (s, w, n, e))
    return [[w, s], [e, s], [e, n], [w, n], [w, s]]


def la_bucket(minutes, s, w, n, e) -> dict:
    rings = [box(s, w, n, e)] + ([box(*LA_HOLE_30)] if minutes == 30 else [])
    return {"minutes": minutes, "round_trip_minutes": 2 * minutes, "polygon": {"type": "Polygon", "coordinates": rings}}


def main() -> None:
    body = {"minutes": 90, "buckets": [bucket(15, B15), bucket(30, B30), bucket(45, B45)]}
    body["buckets"][2]["polygon"]["coordinates"].append(HOLE45)
    points = [{"name": n, "why": w, "lat": at(i, j)[1], "lon": at(i, j)[0], "round_trip_minutes": x}
              for n, i, j, x, w in GRID]
    points += [{"name": n, "why": w, "lat": lat, "lon": lon, "round_trip_minutes": x} for n, lat, lon, x, w in DECIMAL]
    la = {"minutes": 180, "buckets": [la_bucket(*b) for b in LA_BOXES]}
    (HERE / "isochrone.json").write_text(json.dumps(body) + "\n", encoding="utf-8", newline="\n")
    (HERE / "points.json").write_text(json.dumps({"body": "isochrone.json", "points": points}, indent=1) + "\n",
                                      encoding="utf-8", newline="\n")
    (HERE / "la-reach.json").write_text(json.dumps(la) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

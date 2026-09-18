"""--previous: carry segment ids forward across a rebuild, so saved drives survive an OSM edit.

The plan's Saved drives row stores segment ids on the device and re-resolves them against the new corpus
"nearest within 25 m". A way that is split in two gets two NEW way ids, so every derived segment id on it
changes and every saved drive over that road would break. This module is what stops that: for each previous
segment whose id did not survive naturally, it finds the new segment that actually covers the same tarmac and
writes `segment_alias(old_segment_id -> segment_id, cover_pct)`.

Three decisions worth stating:

  * Candidates come out of `segments_rtree`, not out of a full scan. That is the R*Tree earning its place in
    the schema rather than being a column nobody queries.
  * Coverage, not centroid distance. A previous 100 m segment sitting on a new 100 m segment offset by 60 m
    has a near-identical midpoint to one offset by 0 m; coverage tells them apart. `geom.covered_fraction`
    is the one distance primitive, sampled every SAMPLE_STEP_M.
  * Ties are broken by the smaller new segment_id. Two new segments can cover a previous one equally when a
    way was split exactly at its midpoint, and "whichever the rtree returned first" is a mapping that can
    change between sqlite builds while every test stays green.
"""
from __future__ import annotations

import math
import sqlite3

from . import geom

MATCH_RADIUS_M = 25.0
SAMPLE_STEP_M = 10.0
MIN_COVER_PCT = 40  # segment_alias.cover_pct's own CHECK floor
# 0.00025 deg of latitude = 2_500 in e7 = 27.8 m at 111_320 m/deg, so the box pad is MATCH_RADIUS_M with
# slack. The pad only has to be >= the radius: it selects candidates, it does not decide any match.
PAD_LAT_E7 = 2_500


def _pad_lon_e7(lat_e7: int) -> int:
    """The same pad in longitude at this latitude. cos is floored at 85 deg so a polar coordinate cannot
    produce an absurd pad; nothing in a drivable region is near it."""
    lat = min(abs(lat_e7) / 1e7, 85.0)
    return int(PAD_LAT_E7 / max(math.cos(lat * math.pi / 180.0), 0.05)) + 1


def previous_segments(path) -> list:
    """[(segment_id, [(lat, lon), ...])] from a previous corpus, ordered by segment_id."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT segment_id, geometry FROM segments ORDER BY segment_id").fetchall()
    finally:
        conn.close()
    return [(sid, geom.unpack(blob)) for sid, blob in rows]


def previous_way_digests(path) -> dict:
    """{way_id: geom_sha256} from a previous corpus. A way whose digest is unchanged cannot have moved a
    node, so it cannot have moved a bucket, so none of its ids can have changed."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT way_id, geom_sha256 FROM osm_features").fetchall()
    finally:
        conn.close()
    return {wid: bytes(blob) for wid, blob in rows}


def previous_content_sha256(path) -> str:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'content_sha256'").fetchone()
    finally:
        conn.close()
    return row[0] if row else ""


def candidates(conn: sqlite3.Connection, coords: list) -> list:
    """New segment ids whose box is within MATCH_RADIUS_M of this polyline's box, via segments_rtree."""
    lons = [geom.to_e7(c[1]) for c in coords]
    lats = [geom.to_e7(c[0]) for c in coords]
    lat_pad = PAD_LAT_E7
    lon_pad = _pad_lon_e7(max(abs(min(lats)), abs(max(lats))))
    rows = conn.execute(
        "SELECT id FROM segments_rtree WHERE max_lon >= ? AND min_lon <= ? AND max_lat >= ? AND min_lat <= ?"
        " ORDER BY id",
        ((min(lons) - lon_pad) / 1e7, (max(lons) + lon_pad) / 1e7,
         (min(lats) - lat_pad) / 1e7, (max(lats) + lat_pad) / 1e7)).fetchall()
    return [r[0] for r in rows]


def best_cover(conn: sqlite3.Connection, coords: list, new_geometry: dict) -> tuple:
    """(segment_id, cover_pct) of the new segment that best covers `coords`, or (None, 0)."""
    best_id = None
    best_pct = 0
    for sid in candidates(conn, coords):
        cover = geom.covered_fraction(coords, new_geometry[sid], MATCH_RADIUS_M, SAMPLE_STEP_M)
        pct = min(int(cover * 100.0), 100)
        if pct < MIN_COVER_PCT:
            continue
        if best_id is None or pct > best_pct or (pct == best_pct and sid < best_id):
            best_id, best_pct = sid, pct
    return best_id, best_pct


def carry_forward(conn: sqlite3.Connection, previous_path, new_ids: set, new_geometry: dict) -> dict:
    """Resolve every previous segment id against the new build.

    Returns {'aliases': [(old_id, new_id, cover_pct)], 'previous': n, 'carried': n, 'aliased': n,
    'lost': n, 'matched': n}. `carried` counts ids that survived with no alias needed - the common case,
    and most of what the >= 98% floor is made of; `aliased` counts the ones this module saved; `matched` is
    how many previous ids had to go through the geometry at all.
    """
    previous = previous_segments(previous_path)
    aliases = []
    carried = 0
    lost = 0
    matched = 0
    for old_id, coords in previous:
        if old_id in new_ids:
            carried += 1
            continue
        matched += 1
        new_id, pct = best_cover(conn, coords, new_geometry)
        if new_id is None:
            lost += 1
        else:
            aliases.append((old_id, new_id, pct))
    return {
        "aliases": sorted(aliases),
        "previous": len(previous),
        "carried": carried,
        "aliased": len(aliases),
        "lost": lost,
        "matched": matched,
    }


def carry_rate_bp(result: dict) -> int:
    """Resolved ids per 10 000. Integer arithmetic: a float here would be a stored float (task Log, R7)."""
    total = result["previous"]
    if total == 0:
        return 10_000
    return ((result["carried"] + result["aliased"]) * 10_000) // total

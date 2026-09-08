"""meta.content_sha256: a digest of what the corpus SAYS, independent of the sqlite that wrote it.

Two digests exist and one cannot do both jobs.

  file sha256          the artifact's bytes. Bound to the toolchain (the sqlite library version is stamped
                       at header bytes 96-99). Used for the same-process rebuild test and as a download
                       integrity sidecar. NEVER committed as a golden.
  meta.content_sha256  this. A canonical serialisation of every row from a fixed set of SELECT ... ORDER BY
                       statements. Version independent, so it IS committed as a golden, and a human can
                       diff two corpora by table.

Anyone who later "simplifies" this into one committed file checksum re-breaks the host runs permanently:
ops/test runs this pytest tier on the Windows dev box, whose sqlite is 3.40.1, not the image's 3.45.1.

The rtree tables are deliberately not in the digest. They are derived from `segments` and `places` by an
INSERT ... SELECT, they store float32, and hashing them would make a content digest depend on the rtree
implementation. corpusverify asserts rtree parity against the integer boxes instead, which is stronger.
"""
from __future__ import annotations

import hashlib
import sqlite3

from .schema import DIGEST_EXCLUDED_META

FIELD_SEP = "\x1f"
ROW_SEP = "\n"
TABLE_SEP = "\x1e"
NULL = "\x00"

# One SELECT per table, tables in DDL order. Every one is ordered by its primary key.
SELECTS = (
    ("osm_features",
     "SELECT way_id, cls, highway, name, paved, access_ok, oneway, node_count, length_mm, geom_sha256 "
     "FROM osm_features ORDER BY way_id"),
    ("segments",
     "SELECT segment_id, way_id, bucket, offset_mm, length_mm, min_lon_e7, min_lat_e7, max_lon_e7, "
     "max_lat_e7, mid_lon_e7, mid_lat_e7, geometry FROM segments ORDER BY segment_id"),
    ("terms_osm",
     "SELECT segment_id, term_id, value FROM terms_osm ORDER BY segment_id, term_id"),
    ("places",
     "SELECT place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7 FROM places ORDER BY place_id"),
    ("terms_raster",
     "SELECT segment_id, term_id, value FROM terms_raster ORDER BY segment_id, term_id"),
    ("term_defs", "SELECT term_id, name, family FROM term_defs ORDER BY term_id"),
    ("curated",
     "SELECT drive_id, seq, osm_way_id, payload FROM curated ORDER BY drive_id, seq"),
    ("segment_alias",
     "SELECT old_segment_id, segment_id, cover_pct FROM segment_alias ORDER BY old_segment_id"),
    ("id_collisions",
     "SELECT segment_id, way_id, bucket, probe FROM id_collisions ORDER BY segment_id"),
    ("meta", "SELECT key, value FROM meta ORDER BY key"),
)


def render_field(value) -> str:
    if value is None:
        return NULL
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    if isinstance(value, bool):  # never stored, but bool is an int subclass and would render as True
        raise TypeError("bool is not a corpus value type")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".9g")
    return str(value)


def serialise(conn: sqlite3.Connection) -> str:
    parts = []
    for table, sql in SELECTS:
        parts.append(TABLE_SEP + table + ROW_SEP)
        rows = conn.execute(sql).fetchall()
        if table == "meta":
            rows = [r for r in rows if r[0] not in DIGEST_EXCLUDED_META]
        for row in rows:
            parts.append(FIELD_SEP.join(render_field(f) for f in row) + ROW_SEP)
    return "".join(parts)


def content_sha256(conn: sqlite3.Connection) -> str:
    return hashlib.sha256(serialise(conn).encode("utf-8")).hexdigest()


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

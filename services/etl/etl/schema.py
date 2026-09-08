"""corpus.sqlite: the shape of the artifact, and the version that gates an OTA update.

The DDL is an ORDERED TUPLE OF STATEMENTS, appended to and never reordered. That is not style. Statement
order fixes the rootpage numbers in sqlite_schema, which fixes the file bytes, and P-DATA-01's whole claim
is that the same extract rebuilds to the same bytes. Treat this tuple as data, not as a script.

Eight rules the DDL obeys, each of which a later "tidy-up" would break:

  1. `meta` is key/value. Adding a meta key must NOT be a DDL change, because a DDL change forces a
     schema_version bump, which invalidates every device's corpus over the air. Recording a build statistic
     must never be an OTA-breaking migration. REQUIRED_META_KEYS and `build_complete` recover the integrity
     a wide CHECK-constrained row would have bought.
  2. No inline UNIQUE. Inline UNIQUE emits sqlite_autoindex_<table>_<n>, whose name and rootpage come from
     the declaration order of UNIQUE constraints INSIDE the table - invisible in the DDL text, so swapping
     two constraints renumbers indexes and moves every rootpage. Every uniqueness constraint is a named
     CREATE UNIQUE INDEX and a built corpus contains zero sqlite_autoindex_* rows.
  3. No AUTOINCREMENT. It materialises sqlite_sequence, whose stored value depends on the build's history
     rather than on its content.
  4. Every table is either INTEGER PRIMARY KEY with a value we compute, or WITHOUT ROWID. An implicit rowid
     is handed out by insertion order.
  5. No FOREIGN KEY, no view, no trigger. A FK from terms_raster into segments would make DROP TABLE
     segments either fail or leave a broken schema, turning the tested ODbL-separability property into a
     false one. Referential integrity is asserted as a query in corpusverify instead.
  6. No scenic_score column and no score view. A combined score fuses the ODbL layer and our layer into one
     row, which is exactly what the separation exists to prevent. Score is computed from terms_* at query
     time.
  7. Every stored value is an integer or a short string; only terms_*.value is REAL. No stored value is
     produced by a transcendental function, so the committed content digest cannot drift on a platform whose
     libm rounds acos in the last ulp. This is concrete: ops/test runs this pytest tier on the HOST
     interpreter, which on the Windows dev box is not the pinned image's python/sqlite.
  8. Geometry is a BLOB of little-endian int32 (lon_e7, lat_e7) pairs. struct.pack("<ii") is host
     independent; little-endian and (lon, lat) let Swift read a native Int32 array with no byte-swapping and
     match the rtree column order. The `% 8 = 0` CHECK is an integrity anchor a varint encoding could not
     have.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3

SCHEMA_VERSION = 1
MIN_APP_BUILD = 1
# Derived, never typed as a decimal: three independent designs each typed a DIFFERENT wrong literal for it.
APPLICATION_ID = int.from_bytes(b"SCNC", "big")
PINNED_SQLITE_VERSION = "3.45.1"  # services/etl/Dockerfile's ubuntu:24.04 digest. --release refuses others.

ATTRIBUTION = "© OpenStreetMap contributors · Protomaps"
ODBL_NOTICE = ("Contains information from OpenStreetMap, available under the Open Database License. "
               "https://www.openstreetmap.org/copyright")
# Our own content: curated drives, build metadata, and weights sampled from non-OSM rasters. Not an open
# licence. See manifest.KNOWN_LICENSES, where it is declared.
OWN_LICENSE = "LicenseRef-ScenicDrive-1.0"
ODBL_LICENSE = "ODbL-1.0"

# All PRAGMAs are set explicitly even where they match the pinned image's measured default (4096 / UTF-8 /
# NONE). Relying on a default is how a toolchain bump rewrites the artifact with no source diff. page_size
# and encoding are silently ignored after the first CREATE, so these run before the DDL.
PRAGMAS = (
    "PRAGMA page_size    = 4096",
    "PRAGMA encoding     = 'UTF-8'",
    "PRAGMA auto_vacuum  = NONE",
    "PRAGMA journal_mode = OFF",
    "PRAGMA temp_store   = MEMORY",
    "PRAGMA foreign_keys = OFF",
    f"PRAGMA application_id = {APPLICATION_ID}",
    f"PRAGMA user_version   = {SCHEMA_VERSION}",
)

DDL = (
    # 1 --------------------------------------------------------------------------- ODbL group
    """CREATE TABLE osm_features (
  way_id      INTEGER PRIMARY KEY NOT NULL,
  cls         TEXT    NOT NULL,
  highway     TEXT    NOT NULL,
  name        TEXT,
  paved       INTEGER NOT NULL CHECK (paved     IN (0,1)),
  access_ok   INTEGER NOT NULL CHECK (access_ok IN (0,1)),
  oneway      INTEGER NOT NULL CHECK (oneway    IN (-1,0,1)),
  node_count  INTEGER NOT NULL CHECK (node_count >= 2),
  length_mm   INTEGER NOT NULL CHECK (length_mm > 0),
  geom_sha256 BLOB    NOT NULL CHECK (length(geom_sha256) = 32)
)""",
    # 2
    "CREATE INDEX osm_features_by_cls ON osm_features (cls, way_id)",
    # 3
    """CREATE TABLE segments (
  segment_id  INTEGER PRIMARY KEY NOT NULL,
  way_id      INTEGER NOT NULL,
  bucket      INTEGER NOT NULL CHECK (bucket >= 0 AND bucket <= 65535),
  offset_mm   INTEGER NOT NULL CHECK (offset_mm >= 0),
  length_mm   INTEGER NOT NULL CHECK (length_mm > 0),
  min_lon_e7  INTEGER NOT NULL CHECK (min_lon_e7 BETWEEN -1800000000 AND 1800000000),
  min_lat_e7  INTEGER NOT NULL CHECK (min_lat_e7 BETWEEN  -900000000 AND  900000000),
  max_lon_e7  INTEGER NOT NULL CHECK (max_lon_e7 BETWEEN -1800000000 AND 1800000000),
  max_lat_e7  INTEGER NOT NULL CHECK (max_lat_e7 BETWEEN  -900000000 AND  900000000),
  mid_lon_e7  INTEGER NOT NULL,
  mid_lat_e7  INTEGER NOT NULL,
  geometry    BLOB    NOT NULL CHECK (length(geometry) >= 16 AND length(geometry) % 8 = 0),
  CHECK (min_lon_e7 <= max_lon_e7 AND min_lat_e7 <= max_lat_e7),
  CHECK (mid_lon_e7 BETWEEN min_lon_e7 AND max_lon_e7),
  CHECK (mid_lat_e7 BETWEEN min_lat_e7 AND max_lat_e7)
)""",
    # 4  the derivation invariant, engine-enforced, as a NAMED index (rule 2)
    "CREATE UNIQUE INDEX segments_by_way ON segments (way_id, bucket)",
    # 5
    "CREATE VIRTUAL TABLE segments_rtree USING rtree (id, min_lon, max_lon, min_lat, max_lat)",
    # 6
    """CREATE TABLE terms_osm (
  segment_id INTEGER NOT NULL,
  term_id    INTEGER NOT NULL,
  value      REAL    NOT NULL CHECK (value = value),
  PRIMARY KEY (segment_id, term_id)
) WITHOUT ROWID""",
    # 7
    """CREATE TABLE places (
  place_id INTEGER PRIMARY KEY NOT NULL,
  osm_type TEXT    NOT NULL CHECK (osm_type IN ('n','w','r')),
  osm_id   INTEGER NOT NULL CHECK (osm_id > 0),
  cls      TEXT    NOT NULL,
  name     TEXT,
  lon_e7   INTEGER NOT NULL CHECK (lon_e7 BETWEEN -1800000000 AND 1800000000),
  lat_e7   INTEGER NOT NULL CHECK (lat_e7 BETWEEN  -900000000 AND  900000000)
)""",
    # 8
    "CREATE UNIQUE INDEX places_by_osm ON places (osm_type, osm_id)",
    # 9
    "CREATE INDEX places_by_cls ON places (cls, place_id)",
    # 10
    "CREATE VIRTUAL TABLE places_rtree USING rtree (id, min_lon, max_lon, min_lat, max_lat)",
    # 11 ------------------------------------------------------------------------------ our group
    """CREATE TABLE terms_raster (
  segment_id INTEGER NOT NULL,
  term_id    INTEGER NOT NULL,
  value      REAL    NOT NULL CHECK (value = value),
  PRIMARY KEY (segment_id, term_id)
) WITHOUT ROWID""",
    # 12  shipped into BOTH halves on a split: a vocabulary is ours, and the ODbL half is unusable without it
    """CREATE TABLE term_defs (
  term_id INTEGER PRIMARY KEY NOT NULL,
  name    TEXT NOT NULL,
  family  TEXT NOT NULL CHECK (family IN ('osm','raster'))
)""",
    # 13  keyed on way_id, NOT segment_id: curation must not churn when a way is re-segmented
    """CREATE TABLE curated (
  drive_id   TEXT    NOT NULL,
  seq        INTEGER NOT NULL CHECK (seq >= 0),
  osm_way_id INTEGER NOT NULL,
  payload    TEXT    NOT NULL,
  PRIMARY KEY (drive_id, seq)
) WITHOUT ROWID""",
    # 14  a retired previous id that still redraws a saved drive
    """CREATE TABLE segment_alias (
  old_segment_id INTEGER PRIMARY KEY NOT NULL,
  segment_id     INTEGER NOT NULL,
  cover_pct      INTEGER NOT NULL CHECK (cover_pct BETWEEN 40 AND 100)
) WITHOUT ROWID""",
    # 15
    "CREATE INDEX segment_alias_by_new ON segment_alias (segment_id)",
    # 16  every id that did NOT come out of the pure derivation. Empty is normal and asserted.
    """CREATE TABLE id_collisions (
  segment_id INTEGER PRIMARY KEY NOT NULL,
  way_id     INTEGER NOT NULL,
  bucket     INTEGER NOT NULL,
  probe      INTEGER NOT NULL CHECK (probe > 0)
) WITHOUT ROWID""",
    # 17
    """CREATE TABLE meta (
  key   TEXT NOT NULL PRIMARY KEY,
  value TEXT NOT NULL
) WITHOUT ROWID""",
)

# Derived from the DDL text, so a virtual table added without a licence entry cannot hide behind a shadow
# name. rtree materialises <name>_node, <name>_rowid and <name>_parent.
VIRTUAL_TABLES = tuple(re.findall(r"CREATE VIRTUAL TABLE (\w+) USING", "\n".join(DDL)))
SHADOW_TABLES = frozenset(f"{v}_{s}" for v in VIRTUAL_TABLES for s in ("node", "rowid", "parent"))

# 8.2's split, as data. ODbL obligations attach to an identifiable SET OF TABLES rather than smearing across
# the artifact; corpusverify proves the two halves can be dropped independently.
ODBL_TABLES = ("osm_features", "segments", "segments_rtree", "terms_osm", "places", "places_rtree")
OWN_TABLES = ("terms_raster", "curated", "segment_alias", "id_collisions")
BOTH_TABLES = ("meta", "term_defs")
TABLE_LICENSES = {t: ODBL_LICENSE for t in ODBL_TABLES}
TABLE_LICENSES.update({t: OWN_LICENSE for t in OWN_TABLES})
TABLE_LICENSES.update({t: OWN_LICENSE for t in BOTH_TABLES})

# Term ids. The two frozensets are DISJOINT and CorpusWriter.add_term refuses a term_id outside its family:
# a family appearing in both sets is exactly how the ODbL separation quietly dies.
# T-0030 ships ZERO rows in both tables. The producers are a follow-up (T-C); landcover and byways were in
# review with constants moving on the day this was written, and importing them would have been half-wiring.
TERM_NAMES = {
    1: "curvature",     # etl/curvature.py, T-0025. Computed from OSM geometry alone -> ODbL.
    101: "elev_gain",   # 3DEP, T-0026
    102: "relief",      # 3DEP, T-0026
    103: "canopy",      # USFS/MRLC tree canopy - RESERVED, producer not written
    104: "impervious",  # MRLC NLCD impervious  - RESERVED, producer not written
    105: "byway",       # FHWA/Caltrans overlay - RESERVED, producer not written
}
OSM_TERM_IDS = frozenset(k for k in TERM_NAMES if k < 100)
RASTER_TERM_IDS = frozenset(k for k in TERM_NAMES if k >= 100)
TERM_FAMILIES = {"osm": OSM_TERM_IDS, "raster": RASTER_TERM_IDS}

COUNT_KEYS = (
    "osm_features", "segments", "places", "terms_osm", "terms_raster", "term_defs", "curated",
    "segment_alias", "id_collisions", "closed_ways", "changed_ways", "matcher_ways",
    "ids_carried", "ids_lost", "ids_aliased",
)
REQUIRED_COUNT_KEYS = frozenset(f"count.{k}" for k in COUNT_KEYS)
REQUIRED_META_KEYS = frozenset({
    "schema_version", "min_app_build", "corpus_version", "region", "bbox", "built_at",
    "attribution", "odbl_notice", "table_licenses", "sqlite_version", "content_sha256",
    "build_complete", "carry_rate", "previous_content_sha256", "carry_override",
}) | REQUIRED_COUNT_KEYS

# Excluded from meta.content_sha256: everything that is a property of THIS build rather than of its content.
# content_sha256 must be version independent so it can be committed as a golden and diffed by a human.
DIGEST_EXCLUDED_META = frozenset({"built_at", "content_sha256", "build_complete", "sqlite_version"})

_WS = re.compile(r"\s+")


def ddl_sha256(conn: sqlite3.Connection) -> str:
    """sha256 of a normalised read-back of sqlite_schema.

    Read back rather than hashed off this file's source, because the read-back catches the invisible things:
    an autoindex row has a name and a NULL sql, so adding an inline UNIQUE constraint moves this hash even
    though it adds no CREATE INDEX line to the tuple above.

    The caller takes it immediately after the DDL executes and BEFORE any INSERT or ANALYZE, which keeps
    sqlite_stat1 out of it with no carve-out.
    """
    rows = conn.execute(
        "SELECT type, name, tbl_name, ifnull(sql,'') FROM sqlite_schema ORDER BY type, name"
    ).fetchall()
    body = "\n".join("\x1f".join(_WS.sub(" ", str(f)).strip() for f in row) for row in rows)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def apply_schema(conn: sqlite3.Connection) -> str:
    """PRAGMAs, then the DDL tuple, once, in order. Returns ddl_sha256 taken before any row exists."""
    for pragma in PRAGMAS:
        conn.execute(pragma)
    for statement in DDL:
        conn.execute(statement)
    return ddl_sha256(conn)

"""CorpusWriter: the only thing that writes corpus.sqlite.

Everything here exists to make two builds of the same extract byte-identical (P-DATA-01). Three rules:

  1. Nothing is read from the environment. No clock, no random, no os.urandom, no dict iteration order that
     was not sorted first. `built_at` arrives as an argument (see the task Log, R8).
  2. Every INSERT set is sorted by its primary key before it is executed. sqlite hands out pages in insertion
     order, so an unsorted insert of the same rows produces a different file with the same content.
  3. One explicit transaction, `isolation_level=None`. Python's default implicit-BEGIN wraps statements
     according to what kind of statement it thinks it saw, which is a rule that has changed between
     interpreter versions; the file layout must not depend on that.

`add_term` refuses a term_id outside its family. A raster term written into `terms_osm` is not a typo, it is
the ODbL Collective-Database posture quietly becoming false, and nothing downstream would ever notice.
"""
from __future__ import annotations

import os
import sqlite3

from . import contentdigest, schema
from .segid import MAX_PROBES, natural_id, probe

E7 = 1e7

# The COUNT_KEYS that name a real table. The rest (closed_ways, changed_ways, matcher_ways, ids_*) are
# properties of the BUILD, not of a table, and the build has to hand them over or the corpus is refused.
TABLE_COUNT_KEYS = frozenset((
    "osm_features", "segments", "places", "terms_osm", "terms_raster", "term_defs", "curated",
    "segment_alias", "id_collisions",
))


class CorpusWriter:
    def __init__(self, path):
        self.path = str(path)
        if os.path.exists(self.path):
            os.remove(self.path)
        self.conn = sqlite3.connect(self.path, isolation_level=None)
        self.ddl_sha256 = schema.apply_schema(self.conn)
        self.collisions = 0
        self.conn.execute("BEGIN")

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # ---------------------------------------------------------------- the ODbL group

    def write_features(self, ways: list) -> None:
        rows = sorted(
            (w.way_id, w.cls, w.highway, w.name, w.paved, w.access_ok, w.oneway,
             w.node_count, w.length_mm, w.geom_sha256)
            for w in ways
        )
        self.conn.executemany(
            "INSERT INTO osm_features (way_id, cls, highway, name, paved, access_ok, oneway, node_count, "
            "length_mm, geom_sha256) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)

    def assign_id(self, segment, taken: set) -> int:
        """The segment's natural id, or its first free probe. A silent probe is the one failure that must
        never be silent: two segments swapping identities redraws every saved drive over the wrong road."""
        sid = natural_id(segment.way_id, segment.bucket)
        if sid not in taken:
            taken.add(sid)
            return sid
        for n in range(1, MAX_PROBES + 1):
            alt = probe(sid, n)
            if alt not in taken:
                taken.add(alt)
                self.conn.execute(
                    "INSERT INTO id_collisions (segment_id, way_id, bucket, probe) VALUES (?,?,?,?)",
                    (alt, segment.way_id, segment.bucket, n))
                self.collisions += 1
                return alt
        raise RuntimeError(
            f"way {segment.way_id} bucket {segment.bucket}: {MAX_PROBES} probes all collided")

    def write_segments(self, segments: list) -> list:
        """Assigns ids in (way_id, bucket) order and writes `segments` + `segments_rtree`.

        Returns [(segment_id, segment)] sorted by segment_id, which is the order every later pass uses.
        """
        from .segmenter import midpoint

        ordered = sorted(segments, key=lambda s: (s.way_id, s.bucket))
        taken: set = set()
        assigned = [(self.assign_id(s, taken), s) for s in ordered]
        rows = []
        boxes = []
        for sid, seg in assigned:
            min_lon, min_lat, max_lon, max_lat = seg.box_e7
            mid_lon, mid_lat = seg.mid_e7(midpoint(seg))
            rows.append((sid, seg.way_id, seg.bucket, seg.offset_mm, seg.length_mm,
                         min_lon, min_lat, max_lon, max_lat, mid_lon, mid_lat, seg.geometry))
            boxes.append((sid, min_lon / E7, max_lon / E7, min_lat / E7, max_lat / E7))
        rows.sort()
        boxes.sort()
        self.conn.executemany(
            "INSERT INTO segments (segment_id, way_id, bucket, offset_mm, length_mm, min_lon_e7, "
            "min_lat_e7, max_lon_e7, max_lat_e7, mid_lon_e7, mid_lat_e7, geometry) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        self.conn.executemany(
            "INSERT INTO segments_rtree (id, min_lon, max_lon, min_lat, max_lat) VALUES (?,?,?,?,?)", boxes)
        return sorted(assigned, key=lambda pair: pair[0])

    def write_places(self, places: list) -> None:
        """Empty this slice (task Log, R12). Written as a loop rather than skipped so that the day a POI
        array appears in the extract, `places_rtree` is populated by the same call that populates `places`."""
        rows = sorted(places)
        self.conn.executemany(
            "INSERT INTO places (place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7) "
            "VALUES (?,?,?,?,?,?,?)", rows)
        self.conn.executemany(
            "INSERT INTO places_rtree (id, min_lon, max_lon, min_lat, max_lat) VALUES (?,?,?,?,?)",
            sorted((r[0], r[5] / E7, r[5] / E7, r[6] / E7, r[6] / E7) for r in rows))

    def add_term(self, family: str, segment_id: int, term_id: int, value: float) -> None:
        if family not in schema.TERM_FAMILIES:
            raise ValueError(f"unknown term family {family!r}")
        if term_id not in schema.TERM_FAMILIES[family]:
            raise ValueError(
                f"term_id {term_id} ({schema.TERM_NAMES.get(term_id, 'unknown')}) is not in family "
                f"{family!r}: writing it there would put a raster term in the ODbL half")
        table = "terms_osm" if family == "osm" else "terms_raster"
        self.conn.execute(
            f"INSERT INTO {table} (segment_id, term_id, value) VALUES (?,?,?)",
            (segment_id, term_id, float(value)))

    # ---------------------------------------------------------------- our group

    def write_term_defs(self) -> None:
        rows = sorted(
            (tid, name, "osm" if tid in schema.OSM_TERM_IDS else "raster")
            for tid, name in schema.TERM_NAMES.items())
        self.conn.executemany(
            "INSERT INTO term_defs (term_id, name, family) VALUES (?,?,?)", rows)

    def write_curated(self, rows: list) -> None:
        self.conn.executemany(
            "INSERT INTO curated (drive_id, seq, osm_way_id, payload) VALUES (?,?,?,?)", sorted(rows))

    def write_aliases(self, rows: list) -> None:
        self.conn.executemany(
            "INSERT INTO segment_alias (old_segment_id, segment_id, cover_pct) VALUES (?,?,?)", sorted(rows))

    # ---------------------------------------------------------------- meta and finish

    def set_meta(self, key: str, value) -> None:
        self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?,?)", (key, str(value)))

    def table_count(self, table: str) -> int:
        return int(self.conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])

    def write_counts(self, extra: dict) -> None:
        """One count.<name> per COUNT_KEYS. A table count is measured off the table, never carried in a
        variable that a later refactor can forget to update; the rest arrive from the build."""
        for key in schema.COUNT_KEYS:
            if key in extra:
                self.set_meta(f"count.{key}", int(extra[key]))
            elif key in TABLE_COUNT_KEYS:
                self.set_meta(f"count.{key}", self.table_count(key))
            else:
                raise RuntimeError(f"count.{key} is not a table and was not supplied by the build")

    def bbox_e7(self) -> str:
        row = self.conn.execute(
            "SELECT min(min_lon_e7), min(min_lat_e7), max(max_lon_e7), max(max_lat_e7) FROM segments"
        ).fetchone()
        if row is None or row[0] is None:
            return ""
        return ",".join(str(int(v)) for v in row)

    def finalize(self) -> str:
        """content_sha256, then build_complete, then COMMIT. Returns the content digest.

        `build_complete` is written last and only here, so a corpus killed mid-build is detectable as a file
        whose meta says nothing rather than as a plausible corpus missing a third of its segments.
        """
        missing = schema.REQUIRED_META_KEYS - {
            r[0] for r in self.conn.execute("SELECT key FROM meta")} - {"content_sha256", "build_complete"}
        if missing:
            raise RuntimeError(f"meta is missing required keys: {', '.join(sorted(missing))}")
        digest = contentdigest.content_sha256(self.conn)
        self.set_meta("content_sha256", digest)
        self.set_meta("build_complete", "1")
        self.conn.execute("COMMIT")
        return digest

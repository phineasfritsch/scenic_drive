"""The corpus `places` table -> idempotent, chunked SQL for the Worker's D1 `places` (T-0393).

    ops/seed-places [--corpus PATH] (--dry-run | --out DIR) [--chunk N]

The Worker resolves a /plan or /trip destination id with `SELECT lat, lon FROM places WHERE id = ?1`
(services/api/src/placeResolver.ts; DDL in services/api/migrations/0001_places.sql). The id the app sends is the
decimal of the corpus place_id (PlanRequestBody encodes `String(place)`), so a D1 row is
`(id = str(place_id), lat = lat_e7 / 1e7, lon = lon_e7 / 1e7)`.

Rulings (T-0393 Log): R1 the corpus must carry this ETL's schema_version and build_complete "1" and at least one
place; R2 every statement is an upsert and nothing is deleted; R3 coordinates are written as `<e7> / 10000000.0` so
SQLite divides to the same double JS and Python do, with no decimal rendering to round; R4 one statement per file,
at most `CHUNK_MAX` rows - whose widest statement test_seedplaces.py holds under D1's 100000 bytes; R5 one summary line with the sha256 of the canonical
rows; R6 every row re-validated. This module never runs wrangler: it prints the command for the orchestrator.

EXITS. 0 written (or dry-run). 2 refused - nothing is written.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sqlite3
import sys

from etl import schema

CHUNK_DEFAULT = 500
CHUNK_MAX = 1000
PLACE_ID_MAX = 2 ** 63 - 1
LAT_E7_MAX = 900000000
LON_E7_MAX = 1800000000
D1_DATABASE = "scenic"
REFUSED = 2

HEAD = "INSERT INTO places (id, lat, lon) VALUES\n"
TAIL = "\nON CONFLICT (id) DO UPDATE SET lat = excluded.lat, lon = excluded.lon;\n"


class Refusal(Exception):
    """A corpus or an argument this exporter will not turn into SQL."""


def is_int(value: object) -> bool:
    return type(value) is int


def read_corpus(path: pathlib.Path) -> tuple[dict, list]:
    """The corpus's meta and its places as (place_id, lat_e7, lon_e7), ascending place_id, every row validated."""
    if not path.is_file():
        raise Refusal(f"no corpus at {path}")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        meta = dict(connection.execute("SELECT key, value FROM meta").fetchall())
        rows = connection.execute("SELECT place_id, lat_e7, lon_e7 FROM places ORDER BY place_id").fetchall()
    except sqlite3.Error as error:
        raise Refusal(f"{path} is not a readable corpus: {error}") from error
    finally:
        connection.close()
    if meta.get("schema_version") != str(schema.SCHEMA_VERSION):
        raise Refusal(f"corpus schema_version {meta.get('schema_version')!r} is not this ETL's {schema.SCHEMA_VERSION}")
    if meta.get("build_complete") != "1":
        raise Refusal(f"corpus build_complete is {meta.get('build_complete')!r}, not '1'")
    if not rows:
        raise Refusal("corpus has no places")
    for place_id, lat_e7, lon_e7 in rows:
        if not is_int(place_id) or not 1 <= place_id <= PLACE_ID_MAX:
            raise Refusal(f"place_id {place_id!r} is not in [1, 2^63-1]")
        if not is_int(lat_e7) or not -LAT_E7_MAX <= lat_e7 <= LAT_E7_MAX:
            raise Refusal(f"place {place_id}: lat_e7 {lat_e7!r} is not an integer in range")
        if not is_int(lon_e7) or not -LON_E7_MAX <= lon_e7 <= LON_E7_MAX:
            raise Refusal(f"place {place_id}: lon_e7 {lon_e7!r} is not an integer in range")
    return meta, rows


def canonical_sha256(rows: list) -> str:
    """sha256 over one "<place_id>\\t<lat_e7>\\t<lon_e7>\\n" line per place, ascending place_id."""
    digest = hashlib.sha256()
    for place_id, lat_e7, lon_e7 in sorted(rows):
        digest.update(f"{place_id}\t{lat_e7}\t{lon_e7}\n".encode("ascii"))
    return digest.hexdigest()


def value_row(place_id: int, lat_e7: int, lon_e7: int) -> str:
    return f"('{place_id}', {lat_e7} / 10000000.0, {lon_e7} / 10000000.0)"


def statements(rows: list, chunk: int) -> list:
    """One upsert statement per `chunk` rows, in order."""
    return [HEAD + ",\n".join(value_row(*row) for row in rows[start:start + chunk]) + TAIL
            for start in range(0, len(rows), chunk)]


def summary(meta: dict, rows: list, chunks: int) -> str:
    return (f"seed-places: schema_version={meta['schema_version']} region={meta.get('region')} "
            f"corpus_version={meta.get('corpus_version')} rows={len(rows)} chunks={chunks} "
            f"sha256={canonical_sha256(rows)}")


def run(corpus: pathlib.Path, out: pathlib.Path | None, chunk: int, dry_run: bool) -> list:
    """The lines to print; the chunk files written under `out` unless `dry_run`. Raises Refusal before any write."""
    if not 1 <= chunk <= CHUNK_MAX:
        raise Refusal(f"--chunk must be in [1, {CHUNK_MAX}], got {chunk}")
    if dry_run == (out is not None):
        raise Refusal("give exactly one of --dry-run and --out DIR")
    if out is not None and out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refusal(f"--out {out} exists and is not an empty directory")
    meta, rows = read_corpus(corpus)
    texts = statements(rows, chunk)
    lines = [summary(meta, rows, len(texts))]
    if dry_run:
        return lines
    out.mkdir(parents=True, exist_ok=True)
    for index, text in enumerate(texts, start=1):
        path = out / f"places-{index:04d}.sql"
        path.write_bytes(text.encode("ascii"))
        lines.append(f"npx wrangler d1 execute {D1_DATABASE} --remote --file {path}")
    return lines


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops/seed-places", allow_abbrev=False,
                                     description="corpus places -> chunked upsert SQL for D1 places")
    parser.add_argument("--corpus", required=True, type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--chunk", type=int, default=CHUNK_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        lines = run(args.corpus, args.out, args.chunk, args.dry_run)
    except Refusal as refusal:
        print(f"seed-places: REFUSED: {refusal}", file=sys.stderr)
        return REFUSED
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

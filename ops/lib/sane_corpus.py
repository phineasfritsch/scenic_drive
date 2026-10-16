"""sane_corpus: ops/sane exit 4's corpus invariants over a BUILT corpus.sqlite (T-0372). Reads; never writes.

    python ops/lib/sane_corpus.py                  SANE_CORPUS, else $SCENIC_REGION_WORK/<region>-corpus.sqlite
    python ops/lib/sane_corpus.py --corpus PATH    exactly that file

One line per predicate per corpus, TAB-separated "<status>\\t<row>\\t<message>" with status ok|FAIL|skip, which
ops/sane turns into its own rows. Exit 0 when no row FAILed, 4 when one did (ops/sane's code), 2 on bad arguments.

WHAT IS CHECKED, AND WHAT IS NOT (T-0372 rulings R1-R5, measured on both LA corpora first):
  corpus-open        the file opens READ-ONLY, carries meta, schema_version == schema.py's, build_complete == "1".
                     Anything else is "cannot tell", and cannot-tell is 4, never ok.
  corpus-terms       no terms_osm / terms_raster value outside 0..1. score.score returns None (a NULL score) for a
                     unit term outside 0..1 or not finite; that is the corpus-visible half of "no NULL scores".
  corpus-viewpoints  places of class viewpoint >= the region's MEASURED floor. LA's corpus holds 102; the floor is
                     int(102 * 0.75) = 76 (T-0205 R3's margin). A region with no measured floor is refused by name.
  corpus-surface     surfacecoverage.verdict over meta.surface_coverage - the one definition, never a recount.
  corpus-score       SKIP, always: the corpus stores no score (schema.py rule 6). Motorway/trunk = 0 and the gates
                     are P-PROD-01's (score.py, the router profile, ScenicKit.Gates); scenic_score is the graph's.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "etl"))
from etl import schema, surfacecoverage  # noqa: E402

PREDICATES = ("corpus-open", "corpus-terms", "corpus-viewpoints", "corpus-surface")
SCORE_ROW = "corpus-score"
DISCOVERY_ROW = "corpus-db"
SCORE_SKIP = ("the corpus stores no score (schema.py rule 6): motorway/trunk = 0 and the gates are P-PROD-01's, "
              "scenic_score is the graph's (T-0008)")
TERM_TABLES = ("terms_osm", "terms_raster")
VIEWPOINT_CLASS = "viewpoint"
VIEWPOINT_FLOORS = {"la": 76}
REFUSE = 4


class Refused(Exception):
    """One predicate's FAIL message."""


def open_read_only(path: pathlib.Path) -> sqlite3.Connection:
    if not path.is_file():
        raise Refused(f"{path}: no such file")
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def check_open(conn: sqlite3.Connection) -> tuple[str, dict]:
    try:
        meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    except sqlite3.DatabaseError as exc:
        raise Refused(f"cannot read meta: {exc}") from exc
    found = meta.get("schema_version")
    if found != str(schema.SCHEMA_VERSION):
        raise Refused(f"schema_version {found!r} != this checkout's {schema.SCHEMA_VERSION}")
    if meta.get("build_complete") != "1":
        raise Refused(f"build_complete {meta.get('build_complete')!r}, not '1' - a partial build")
    return f"schema_version {found}, build_complete 1, region {meta.get('region')!r}", meta


def check_terms(conn: sqlite3.Connection) -> str:
    total, bad = 0, []
    for table in TERM_TABLES:
        try:
            total += conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            rows = conn.execute(f"SELECT segment_id, term_id, value FROM {table} "
                                f"WHERE value IS NULL OR NOT (value >= 0.0 AND value <= 1.0) "
                                f"ORDER BY segment_id, term_id").fetchall()
        except sqlite3.DatabaseError as exc:
            raise Refused(f"cannot read {table}: {exc}") from exc
        bad += [f"{table} segment {s} term {t} value {v!r}" for s, t, v in rows]
    if bad:
        raise Refused(f"{len(bad)} term value(s) outside 0..1 (score.score would be None): " + "; ".join(bad[:3]))
    return f"{total} term rows, every value within 0..1"


def check_viewpoints(conn: sqlite3.Connection, region: object) -> str:
    floor = VIEWPOINT_FLOORS.get(region) if isinstance(region, str) else None
    if floor is None:
        raise Refused(f"no measured viewpoint floor for region {region!r} (measured: {sorted(VIEWPOINT_FLOORS)})")
    try:
        found = conn.execute("SELECT count(*) FROM places WHERE cls = ?", (VIEWPOINT_CLASS,)).fetchone()[0]
    except sqlite3.DatabaseError as exc:
        raise Refused(f"cannot read places: {exc}") from exc
    if found < floor:
        raise Refused(f"{found} viewpoints, below region {region}'s floor {floor}")
    return f"{found} viewpoints >= region {region}'s floor {floor}"


def check_surface(meta: dict) -> str:
    value = meta.get(surfacecoverage.META_KEY)
    if value is None:
        raise Refused(f"meta carries no {surfacecoverage.META_KEY}")
    try:
        table = surfacecoverage.decode(value)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise Refused(f"meta.{surfacecoverage.META_KEY} is malformed: {exc}") from exc
    bad = surfacecoverage.verdict(table)
    if bad:
        raise Refused("; ".join(bad))
    return f"{len(table)} classes, none below its baseline"


def check(path: pathlib.Path) -> list[tuple[str, str, str]]:
    """Every row for one corpus. corpus-open failing leaves nothing else to judge: the rest print skip."""
    out: list[tuple[str, str, str]] = []
    try:
        conn = open_read_only(path)
    except (Refused, sqlite3.Error) as exc:
        conn, opened = None, str(exc)
    else:
        opened = ""
    try:
        if conn is not None:
            try:
                said, meta = check_open(conn)
                out.append(("ok", "corpus-open", f"{path.name}: {said}"))
            except Refused as exc:
                opened = str(exc)
        if opened:
            out.append(("FAIL", "corpus-open", f"{path.name}: {opened}"))
            out += [("skip", row, "corpus-open failed") for row in PREDICATES[1:]]
        else:
            for row, run in (("corpus-terms", lambda: check_terms(conn)),
                             ("corpus-viewpoints", lambda: check_viewpoints(conn, meta.get("region"))),
                             ("corpus-surface", lambda: check_surface(meta))):
                try:
                    out.append(("ok", row, f"{path.name}: {run()}"))
                except Refused as exc:
                    out.append(("FAIL", row, f"{path.name}: {exc}"))
    finally:
        if conn is not None:
            conn.close()
    out.append(("skip", SCORE_ROW, SCORE_SKIP))
    return out


def discover(env: dict) -> list[pathlib.Path]:
    named = env.get("SANE_CORPUS", "")
    if named:
        return [pathlib.Path(named)]
    store = env.get("SCENIC_REGION_WORK", "")
    if not store:
        return []
    regions = sorted(p.name for p in (ROOT / "services" / "etl" / "regions").iterdir() if (p / "region.json").is_file())
    return [pathlib.Path(store) / f"{r}-corpus.sqlite" for r in regions
            if (pathlib.Path(store) / f"{r}-corpus.sqlite").is_file()]


def main(argv: list[str] | None = None, env: dict | None = None) -> int:
    sys.stdout.reconfigure(newline="\n")
    parser = argparse.ArgumentParser(prog="ops/lib/sane_corpus.py", description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", default=None, help="check exactly this corpus.sqlite")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2
    paths = [pathlib.Path(args.corpus)] if args.corpus else discover(os.environ if env is None else env)
    if not paths:
        print(f"skip\t{DISCOVERY_ROW}\tno corpus built here (SANE_CORPUS unset; no "
              f"$SCENIC_REGION_WORK/<region>-corpus.sqlite)")
        return 0
    rows = [r for path in paths for r in check(path)]
    for status, row, message in rows:
        print(f"{status}\t{row}\t{message}")
    return REFUSE if any(status == "FAIL" for status, _, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main())

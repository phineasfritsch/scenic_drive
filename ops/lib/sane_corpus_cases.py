"""check-sane-corpus's rows (T-0372): the fixture corpus each row builds and the rows ops/sane must print for it.

A row is (name, fixture, exit, rows). `fixture` is a dict of edits to the CLEAN corpus, which passes every
predicate while sitting ON each bound (exactly FLOOR_LA viewpoints, term values exactly 0.0 and 1.0, every
surface class exactly at its baseline). `rows` is a function of the fixture's verdict: every predicate ok and
corpus-score skip, except the one predicate the row breaks (FAIL) - or, when corpus-open breaks, the rest skip.

The floor and the term bounds are TYPED here, never read back through sane_corpus: a table that took its numbers
from the checker would compare the checker to itself. BASELINES are surfacecoverage's (the module sane_corpus
delegates to); the rows only place a class on, or one way under, its own baseline.
"""
from __future__ import annotations

import math
import pathlib
import sqlite3

FLOOR_LA = 76
TERM_TABLES = ("terms_osm", "terms_raster")
TERM_IDS = {"terms_osm": (1, 3), "terms_raster": (101, 103)}
PREDICATES = ("corpus-open", "corpus-terms", "corpus-viewpoints", "corpus-surface")
WAYS = 1000
# value variants for one extra term row: GREEN ones are inside 0..1, the rest must FAIL corpus-terms.
TERM_VARIANTS = {"zero": 0.0, "one": 1.0, "below-zero": math.nextafter(0.0, -1.0),
                 "above-one": math.nextafter(1.0, 2.0), "plus-inf": math.inf, "minus-inf": -math.inf,
                 "two": 2.0, "minus-one": -1.0, "text": "x"}
GREEN_TERMS = {"zero", "one"}


def coverage(baselines: dict, below: str | None = None, drop: str | None = None) -> dict:
    table = {}
    for cls, base in baselines.items():
        if cls == drop:
            continue
        known = round(base * WAYS) - (1 if cls == below else 0)
        table[cls] = {"known": known, "unknown": WAYS - known, "unpaved": 0, "total": WAYS}
    return table


def build(path: pathlib.Path, fx: dict, schema, surfacecoverage) -> None:
    """Write the fixture corpus `fx` describes at `path`, through the shipping schema.apply_schema."""
    if fx.get("missing"):
        return
    if "raw" in fx:
        path.write_bytes(fx["raw"])
        return
    conn = sqlite3.connect(str(path))
    schema.apply_schema(conn)
    meta = {"schema_version": str(schema.SCHEMA_VERSION), "build_complete": "1", "region": "la",
            surfacecoverage.META_KEY: surfacecoverage.encode(coverage(surfacecoverage.BASELINES,
                                                                      fx.get("below"), fx.get("drop_class")))}
    meta.update(fx.get("meta", {}))
    conn.executemany("INSERT INTO meta (key, value) VALUES (?, ?)",
                     [(k, v) for k, v in meta.items() if v is not None])
    places = [("viewpoint", i) for i in range(fx.get("viewpoints", FLOOR_LA))]
    places += [("park", 10_000 + i) for i in range(fx.get("parks", 1))]
    conn.executemany("INSERT INTO places (place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7) "
                     "VALUES (?, 'n', ?, ?, NULL, -1185000000, 341000000)",
                     [(n + 1, osm_id + 1, cls) for n, (cls, osm_id) in enumerate(places)])
    for table in TERM_TABLES:
        low, high = TERM_IDS[table]
        conn.executemany(f"INSERT INTO {table} (segment_id, term_id, value) VALUES (?, ?, ?)",
                         [(1, low, 0.0), (1, high, 1.0)])
    for table, value in fx.get("terms", ()):
        conn.execute(f"INSERT INTO {table} (segment_id, term_id, value) VALUES (2, ?, ?)",
                     (TERM_IDS[table][0], value))
    for table in fx.get("drop_tables", ()):
        conn.execute(f"DROP TABLE {table}")
    conn.commit()
    conn.close()


def want(broken: str | None) -> dict:
    """The rows ops/sane must print when `broken` (a predicate, or None) is the one that FAILs."""
    if broken == "corpus-open":
        out = {"corpus-open": "FAIL", **{p: "skip" for p in PREDICATES[1:]}}
    else:
        out = {p: ("FAIL" if p == broken else "ok") for p in PREDICATES}
    out["corpus-score"] = "skip"
    return out


def row(name: str, fx: dict, broken: str | None) -> tuple:
    return (name, fx, 4 if broken else 0, want(broken))


def cases(schema_version: int) -> list[tuple]:
    sv = schema_version
    out = [row("clean-on-every-bound", {}, None)]
    open_rows = {
        "open-missing-file": {"missing": True}, "open-not-sqlite": {"raw": b"not a corpus\n" * 64},
        "open-empty-file": {"raw": b""}, "open-no-meta": {"drop_tables": ("meta",)},
        "open-schema-older": {"meta": {"schema_version": str(sv - 1)}},
        "open-schema-newer": {"meta": {"schema_version": str(sv + 1)}},
        "open-schema-absent": {"meta": {"schema_version": None}},
        "open-schema-padded": {"meta": {"schema_version": f" {sv}"}},
        "open-incomplete-zero": {"meta": {"build_complete": "0"}},
        "open-incomplete-absent": {"meta": {"build_complete": None}},
        "open-incomplete-true": {"meta": {"build_complete": "true"}},
    }
    out += [row(n, fx, "corpus-open") for n, fx in open_rows.items()]
    for table in TERM_TABLES:
        for variant, value in TERM_VARIANTS.items():
            out.append(row(f"terms-{table}-{variant}", {"terms": ((table, value),)},
                           None if variant in GREEN_TERMS else "corpus-terms"))
        out.append(row(f"terms-{table}-missing", {"drop_tables": (table,)}, "corpus-terms"))
    out += [
        row("viewpoints-above-floor", {"viewpoints": FLOOR_LA + 1}, None),
        row("viewpoints-below-floor", {"viewpoints": FLOOR_LA - 1}, "corpus-viewpoints"),
        row("viewpoints-below-floor-many-parks", {"viewpoints": FLOOR_LA - 1, "parks": 500}, "corpus-viewpoints"),
        row("viewpoints-none", {"viewpoints": 0}, "corpus-viewpoints"),
        row("viewpoints-region-sfbay", {"meta": {"region": "sfbay"}, "viewpoints": 5000}, "corpus-viewpoints"),
        row("viewpoints-region-case", {"meta": {"region": "LA"}}, "corpus-viewpoints"),
        row("viewpoints-region-absent", {"meta": {"region": None}}, "corpus-viewpoints"),
        row("viewpoints-no-places-table", {"drop_tables": ("places_fts", "places")}, "corpus-viewpoints"),
        row("surface-motorway-one-under", {"below": "motorway"}, "corpus-surface"),
        row("surface-service-one-under", {"below": "service"}, "corpus-surface"),
        row("surface-class-missing", {"drop_class": "trunk"}, "corpus-surface"),
        row("surface-absent", {"meta": {"surface_coverage": None}}, "corpus-surface"),
        row("surface-malformed", {"meta": {"surface_coverage": "{"}}, "corpus-surface"),
        row("surface-empty-table", {"meta": {"surface_coverage": "{}"}}, "corpus-surface"),
    ]
    return out


def meta_problems(names: list[str], shipped) -> list[str]:
    """Refuse the table unless it covers what the shipped module claims to check."""
    out = []
    if tuple(shipped.PREDICATES) != PREDICATES:
        out.append(f"shipped PREDICATES {shipped.PREDICATES} != the table's {PREDICATES}")
    if tuple(shipped.TERM_TABLES) != TERM_TABLES:
        out.append(f"shipped TERM_TABLES {shipped.TERM_TABLES} != the table's {TERM_TABLES}")
    if shipped.VIEWPOINT_FLOORS != {"la": FLOOR_LA}:
        out.append(f"shipped VIEWPOINT_FLOORS {shipped.VIEWPOINT_FLOORS} != the measured {{'la': {FLOOR_LA}}}")
    reds = {p: [c[0] for c in cases(0) if c[3].get(p) == "FAIL"] for p in PREDICATES}
    out += [f"predicate {p} has no red row" for p, r in reds.items() if not r]
    for table in TERM_TABLES:
        out += [f"no row terms-{table}-{v}" for v in TERM_VARIANTS if f"terms-{table}-{v}" not in names]
    if len(set(names)) != len(names):
        out.append("duplicate case names")
    return out

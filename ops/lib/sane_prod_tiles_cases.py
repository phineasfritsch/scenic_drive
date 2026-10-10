"""check-sane-prod's tiles-manifest rows (T-0345): ops/sane --prod exit 8 over the published tiles manifest.

Three kinds of row, all against the LOCAL fake (never production):
  t-<name>          hand-written, through the SHIPPED ops/sane: every checkout disagreement, each side of every bound
                    (the clock bounds by a 10-minute margin, the body built when the case RUNS), precedence 7 > 6 > 8.
  xt-<field>-<v>    GENERATED, one per tiles field and every variant its kind requires; value and exit are functions
                    of the kind, as the corpus side's x- rows.
  b-<name>          the EXACT clock bounds, which a run that takes seconds cannot hit through ops/sane: the shipping
                    function sane_prod.tiles - the one ops/sane's `sane_prod.py tiles` calls - with a FIXED clock.

The expected region and file are typed here ("la", "la.pmtiles"), never read from region.json or BasemapResolver
with the checker's own reader: a table that read them back through the checker would compare the checker to itself.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

from sane_prod_fake import DEL, edited

TILES_PATH = "/tiles/manifest.json"
REGION_JSON = "services/etl/regions/la/region.json"
RESOLVER = "apps/ios/Packages/ScenicApp/Sources/MapAdapter/BasemapResolver.swift"
BYTES_MIN, BYTES_MAX = 1_048_576, 125_829_120
ZOOM_MIN, ZOOM_MAX = 14, 15
DAY, HOUR, MARGIN = timedelta(days=1), timedelta(hours=1), timedelta(minutes=10)


def stamp(delta: timedelta, now: datetime | None = None) -> str:
    return ((now or datetime.now(timezone.utc)) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def good(now: datetime | None = None) -> dict:
    return {"version": "20261008T000000Z", "region": "la", "file": "la.pmtiles", "built_at": stamp(-DAY, now),
            "maxzoom": 14, "min_app_build": 1, "sha256": "cd" * 32, "bytes": 63_520_949}


def t(**kw: object):
    """A tiles body built when the case runs; a callable value is called then too."""
    return lambda: edited(good(), kw)


TILES_KINDS = {"version": "str", "region": "eqstr", "file": "eqstr", "built_at": "stamp", "maxzoom": "zoom",
               "min_app_build": "int1", "sha256": "sha", "bytes": "bytes"}
UNIVERSAL = ("absent", "null", "true", "false", "string", "empty-string", "list", "object", "number")
INTS = UNIVERSAL + ("zero", "negative")
REGEXES = UNIVERSAL + ("over-long", "under-long", "garbage-suffix")
TILES_REQUIRED = {"str": UNIVERSAL, "eqstr": UNIVERSAL, "stamp": REGEXES, "sha": REGEXES, "zoom": INTS,
                  "int1": INTS, "bytes": INTS}
TILES_GREEN = {("version", "string")}


def variants(field: str, kind: str, g: dict) -> dict[str, object]:
    v = g[field]
    out: dict[str, object] = {"absent": DEL, "null": None, "true": True, "false": False, "empty-string": "",
                              "list": [v], "object": {"value": v}}
    if kind in ("zoom", "int1", "bytes"):
        out.update({"string": str(v), "number": float(v), "zero": 0, "negative": -1})
    elif kind in ("stamp", "sha"):
        out.update({"string": "yesterday" if kind == "stamp" else "g" * 64, "number": 202610,
                    "over-long": v + v[-1], "under-long": v[:-1], "garbage-suffix": v + "x"})
    else:
        out.update({"string": "x", "number": 0})
    return out


def variant_body(field: str, kind: str, variant: str):
    def body() -> dict:
        g = good()
        return edited(g, {field: variants(field, kind, g)[variant]})
    return body


def tiles_cases(health: object, manifest: object, ok: dict, h) -> list[tuple]:
    t8 = {**ok, "tiles": "FAIL"}

    def row(name: str, tiles: object, rc: int = 8, rows: dict | None = None, hl: object = None) -> tuple:
        return (name, hl or (200, health), (200, manifest), rc, rows or (ok if rc == 0 else t8), tiles)

    out = [
        row("t-green", (200, t()), 0),
        row("t-unset", "unset", 0, {**ok, "tiles": "skip"}),
        row("t-404", None),
        row("t-not-json", (200, b"<html>not json</html>")),
        row("t-not-object", (200, lambda: [good()])),
        row("t-missing-key", (200, t(bytes=DEL))),
        row("t-extra-key", (200, t(url="https://example.invalid/la.pmtiles"))),
        row("t-region-other", (200, t(region="bay"))),
        row("t-region-case", (200, t(region="LA"))),
        row("t-file-other", (200, t(file="sfbay.pmtiles"))),
        row("t-file-with-dir", (200, t(file="tiles/la.pmtiles"))),
        row("t-stale", (200, t(built_at=lambda: stamp(-(30 * DAY + MARGIN))))),
        row("t-age-inside", (200, t(built_at=lambda: stamp(-(30 * DAY - MARGIN)))), 0),
        row("t-future", (200, t(built_at=lambda: stamp(HOUR + MARGIN)))),
        row("t-future-inside", (200, t(built_at=lambda: stamp(HOUR - MARGIN))), 0),
        row("t-built-at-offset", (200, t(built_at=lambda: stamp(-DAY)[:-1] + "+00:00"))),
        row("t-built-at-no-such-day", (200, t(built_at="2026-02-30T00:00:00Z"))),
        row("t-maxzoom-below", (200, t(maxzoom=ZOOM_MIN - 1))),
        row("t-maxzoom-floor", (200, t(maxzoom=ZOOM_MIN)), 0),
        row("t-maxzoom-ceiling", (200, t(maxzoom=ZOOM_MAX)), 0),
        row("t-maxzoom-above", (200, t(maxzoom=ZOOM_MAX + 1))),
        row("t-bytes-floor", (200, t(bytes=BYTES_MIN)), 0),
        row("t-bytes-under", (200, t(bytes=BYTES_MIN - 1))),
        row("t-bytes-budget", (200, t(bytes=BYTES_MAX)), 0),
        row("t-bytes-over", (200, t(bytes=BYTES_MAX + 1))),
        row("t-sha-upper", (200, t(sha256="CD" * 32))),
        row("t-min-build-one", (200, t(min_app_build=1)), 0),
        row("p-6-over-tiles-8", (200, t(region="bay")), 6, {**ok, "quota": "FAIL", "tiles": "FAIL"},
            (200, h(kill_switch=True))),
        row("p-7-over-tiles-8", (200, t(region="bay")), 7,
            {"backend": "FAIL", "version": None, "quota": None, "tiles": "FAIL"},
            (503, h(ok=False, db="down", kill_switch=True))),
    ]
    for field, kind in TILES_KINDS.items():
        for variant in variants(field, kind, good()):
            green = (field, variant) in TILES_GREEN
            out.append(row(f"xt-{field}-{variant}", (200, variant_body(field, kind, variant)), 0 if green else 8))
    return out


NOW = datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc)
# (name, built_at offset from NOW, accepted?) - each clock bound exactly, and one second past it.
BOUNDS = [
    ("b-green", -DAY, True),
    ("b-age-exactly-30-days", -30 * DAY, True),
    ("b-age-30-days-and-1s", -(30 * DAY + timedelta(seconds=1)), False),
    ("b-future-exactly-1h", HOUR, True),
    ("b-future-1h-and-1s", HOUR + timedelta(seconds=1), False),
]


def bound_problems(root: str, sane_prod, only: set | None) -> tuple[int, list[str]]:
    """Run the selected b- rows through sane_prod.tiles at NOW; (rows run, failures)."""
    ran, failed = 0, []
    for name, delta, want in BOUNDS:
        if only is not None and name not in only:
            continue
        ran += 1
        body = json.dumps({**good(NOW), "built_at": stamp(delta, NOW)})
        got, line = sane_prod.tiles(body, os.path.join(root, REGION_JSON), os.path.join(root, RESOLVER), now=NOW)
        if got != want:
            failed.append(f"{name}: accepted={got}, want {want} ({line})")
    return ran, failed


def tiles_meta_problems(names: list[str], tiles_manifest) -> list[str]:
    out = []
    shipped = getattr(tiles_manifest, "FIELDS", ())
    if set(TILES_KINDS) != set(shipped) or set(TILES_KINDS) != set(good()):
        out.append(f"tiles fields {sorted(TILES_KINDS)} != shipped tiles_manifest.FIELDS {sorted(shipped)}")
    for field, kind in TILES_KINDS.items():
        missing = [v for v in TILES_REQUIRED[kind] if f"xt-{field}-{v}" not in names]
        if missing:
            out.append(f"tiles field {field} has no row for {missing}")
    return out

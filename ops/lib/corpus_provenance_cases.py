"""The population P-DATA-03's corpus half is decided over, built by the SHIPPING builder.

Imported by ops/lib/check-corpus-provenance.py (it moved here for CLAUDE.md's 300-line cap, T-0233 R10) and by
services/etl/tests, so the pin, its CI test and the bound table build one population.

THE EXTRACT IS MARIN (T-0233 R12). services/etl/tests/fixtures/corpus_extract.json is seven Marin roads - lat
37.8999804..37.9711326, lon -122.6..-122.5863186 - and until T-0233 every fixture stamped it `la` and the
"fresh region-la corpus" was ACCEPTED: the pin's own population was the defect it was filed for. A corpus that
must be accepted is now built from the same extract TRANSLATED into la by LA_SHIFT (lat 34.0999804..34.1711326,
lon -118.6..-118.5863186, the Malibu canyons), written to a temp file and handed to the same corpus.build. The
untranslated extract is the refused fixture `stamped la, content in Marin`. The committed file is not edited:
eight other test files read it as Marin.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

# (degrees of latitude, degrees of longitude) added to every node: Marin -> the Santa Monica Mountains.
LA_SHIFT = (-3.8, 4.0)
# la's own region.json bbox in e7, the box a lying meta.bbox claims (T-0233 R4).
LA_BOX_E7 = "-1190000000,337000000,-1178500000,344500000"


def stamp_days_ago(days: float) -> str:
    moment = datetime.now(timezone.utc) - timedelta(days=days)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def translated_extract(src: Path, out: Path, shift: tuple[float, float] = LA_SHIFT) -> Path:
    """The extract with every node moved by `shift`; every other field untouched."""
    doc = json.loads(Path(src).read_text(encoding="utf-8"))
    for way in doc["ways"]:
        way["nodes"] = [[lat + shift[0], lon + shift[1]] for lat, lon in way["nodes"]]
    Path(out).write_text(json.dumps(doc), encoding="utf-8")
    return Path(out)


def build_fixture(out: Path, corpus, extract: Path, *, region: str, built_at: str,
                  drop: str | None = None, sql: list | None = None) -> Path:
    """One corpus from the SHIPPING builder, then optionally one meta row deleted and/or statements run.

    CorpusWriter.finalize refuses a corpus missing any required meta key, so an absent key can only be made
    by deleting it afterwards (T-0219 R2); the same holds for a lying meta.bbox and an emptied segments table.
    """
    corpus.build(extract, out, built_at, region=region)
    statements = ([("DELETE FROM meta WHERE key = ?", (drop,))] if drop is not None else []) + list(sql or [])
    if statements:
        conn = sqlite3.connect(str(out))
        try:
            for statement, params in statements:
                conn.execute(statement, params)
            conn.commit()
        finally:
            conn.close()
    return out


def fixtures(region: str, max_age_days: int) -> list[tuple]:
    """(label, stamped region, built_at, meta key dropped, extract 'la' or 'marin', statements run after,
    the refusal it must name or None = ACCEPTED)."""
    fresh = stamp_days_ago(0.001)
    return [
        ("a fresh region-la corpus", region, fresh, None, "la", None, None),
        ("stamped 40 days ago", region, stamp_days_ago(40), None, "la", None,
         f"older than {max_age_days} days (P-DATA-03)"),
        ("stamped region 'bay'", "bay", fresh, None, "la", None, "meta.region is 'bay'"),
        ("no meta.region at all", region, fresh, "region", "la", None, "meta.region is None"),
        ("no meta.built_at at all", region, fresh, "built_at", "la", None, "meta.built_at is missing"),
        ("stamped 2 days in the future", region, stamp_days_ago(-2), None, "la", None,
         "is in the future by more than"),
        ("stamped la, content in Marin", region, fresh, None, "marin", None, "lies outside region"),
        ("meta.bbox claiming la's whole box over a window", region, fresh, None, "la",
         [("UPDATE meta SET value = ? WHERE key = 'bbox'", (LA_BOX_E7,))],
         "disagrees with the segments' extent"),
        ("no segments at all", region, fresh, None, "la", [("DELETE FROM segments", ())],
         "carries no segments"),
    ]

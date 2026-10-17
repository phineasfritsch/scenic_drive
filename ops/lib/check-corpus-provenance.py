"""P-DATA-03's CORPUS half: corpus.sqlite's meta.region is the active region, its built_at is fresh, and its
CONTENT lies inside that region.

    python ops/lib/check-corpus-provenance.py
    python ops/lib/check-corpus-provenance.py --prove-red
    python ops/lib/check-corpus-provenance.py --corpus <corpus.sqlite> [--region la | --region-json <file>]

THE DEFECT (T-0197 rv1/rv2-pr119, filed as T-0219). `etl.corpus` STAMPS a region - services/etl/etl/corpus.py,
`region = region or extract_region` then `writer.set_meta("region", region)` - and until this file NOTHING in
the tree read it back against the active region. A corpus cut for another region, or a year old, opens on the
phone as a complete corpus: every table present, every index built, `build_complete` = 1.

THIS FILE IS BOTH HALVES (the tiles side subprocesses services/tiles/check_pmtiles.py): `check_corpus` is the
shipping decision and `main` the one entry point P-DATA-03, test_corpus_provenance.py and `--corpus` all run.

THE READER (T-0219 R1): plain sqlite3 over `meta` and `segments`, READ-ONLY by URI (an INSERT raises) - never
CorpusWriter, whose `__init__` `os.remove()`s an existing file.

THE STAMP IS NOT THE CONTENT (T-0233). meta.region says which region a corpus CLAIMS; the content limb reads
where its segments ARE - `min(min_lon_e7), min(min_lat_e7), max(max_lon_e7), max(max_lat_e7)` over `segments`
- and requires that extent inside the region's own region.json bbox widened by CORPUS_OVERHANG_DEG, and
meta.bbox (itself a stamp, written from that extent by corpuswriter.bbox_e7) to EQUAL it. The widening is
measured, not assumed: `osmium extract -c` completes border ways, and the full LA corpus (874,391 segments)
overhangs la's box by 0.0609 W / 0.0167 S / 0.0859 E / 0.0421 N degrees (T-0233 R1), so "a clip is never
larger than its region" is false for a corpus. Every comparison is in integer e7 (R5). A region bbox carrying
NaN or min >= max is refused by name (R6): a float comparison against NaN is False, which would accept all.

THE POPULATION is ops/lib/corpus_provenance_cases.py: built in process by the SHIPPING `corpus.build`, never
committed (a frozen built_at turns the age limb into a calendar); accepted ones are translated into la (R12).

THE REAL ARTEFACT: `SCENIC_LA_CORPUS` naming a file runs the same decision over it; set and absent REFUSES.

WHAT IT DOES NOT COVER: places and landmarks are not read (segments are the routable content); a corpus with no
segments - the bundled fallback is one - is refused, and nothing runs this over the fallback. Nor does this
read count.*, surface_coverage (P-DATA-04 owns that) or content_sha256.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import subprocess
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory


def _root() -> Path:
    """The repo root by MARKER, for this file AND a mutated copy in a temp dir run with cwd=ROOT."""
    here = Path(__file__).resolve()
    for base in [*here.parents, Path.cwd().resolve()]:
        if (base / "pins/PINS.yaml").is_file() and (base / "services/etl/etl/corpus.py").is_file():
            return base
    raise SystemExit("check-corpus-provenance: no repo root above this file or at the cwd "
                     "(looked for pins/PINS.yaml beside services/etl/etl/corpus.py)")


ROOT = _root()
ETL = ROOT / "services/etl"
EXTRACT = ETL / "tests/fixtures/corpus_extract.json"
REGIONS = ETL / "regions"
MUTATIONS = ROOT / "ops/lib/check-corpus-provenance-mutations.py"
CORPUS_ENV = "SCENIC_LA_CORPUS"
# P-DATA-03: built_at under 30 days, the same limit the tiles half enforces.
MAX_AGE_DAYS = 30
# The tiles half's rv1-pr109 R1, which applies harder here: `--built-at` is a REQUIRED argument typed by an
# operator (corpus.py, "An INPUT: no clock is read"), so a wrong year is reachable by hand and not only from a
# host clock set ahead. One hour is NTP drift; it is three orders of magnitude under MAX_AGE_DAYS.
MAX_FUTURE_SKEW = timedelta(hours=1)
# T-0233 R1: 2.9x the largest measured complete_ways overhang (0.0858999 deg, the full LA corpus's east edge)
# and under a ninth of the 2.40 deg between la's north edge and sfbay's south edge.
CORPUS_OVERHANG_DEG = 0.25

sys.path.insert(0, str(ETL))
sys.path.insert(0, str(ROOT / "ops/lib"))


def refuse(reason: str, *extra: str) -> int:
    print(f"P-DATA-03 (corpus half): {reason}")
    for line in extra:
        print(f"  {line}")
    return 1


def _connect_ro(path: Path) -> sqlite3.Connection:
    uri = "file:" + urllib.parse.quote(Path(path).resolve().as_posix()) + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def read_meta(path: Path) -> dict:
    """The corpus's whole meta table, READ-ONLY. The check may never mutate what it judges."""
    conn = _connect_ro(path)
    try:
        return {str(k): v for k, v in conn.execute("SELECT key, value FROM meta")}
    finally:
        conn.close()


def read_extent(path: Path) -> tuple[int, int, int, int] | None:
    """Where the segments ARE, e7 (min_lon, min_lat, max_lon, max_lat); None when there are none."""
    conn = _connect_ro(path)
    try:
        row = conn.execute("SELECT min(min_lon_e7), min(min_lat_e7), max(max_lon_e7), max(max_lat_e7) "
                           "FROM segments").fetchone()
    finally:
        conn.close()
    return None if row is None or row[0] is None else tuple(int(v) for v in row)


def region_limits(bbox: dict, overhang: float) -> tuple[int, int, int, int]:
    """The region bbox widened by `overhang` degrees, e7. Raises ValueError on NaN, inf or a disordered box."""
    edges = [float(bbox[key]) for key in ("min_lon", "min_lat", "max_lon", "max_lat")]
    if not all(math.isfinite(v) for v in edges) or not (edges[0] < edges[2] and edges[1] < edges[3]):
        raise ValueError(f"region bbox {edges} is not a finite min < max box (P-DATA-03)")
    return (round((edges[0] - overhang) * 1e7), round((edges[1] - overhang) * 1e7),
            round((edges[2] + overhang) * 1e7), round((edges[3] + overhang) * 1e7))


def load_region(path: Path) -> tuple[str, tuple[int, int, int, int]]:
    """(the expected id, the content limits) - both READ from region.json, never typed here (T-0219 R3)."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return str(doc["id"]), region_limits(doc["bbox"], CORPUS_OVERHANG_DEG)


def _e7(box) -> str:
    return ",".join(str(v) for v in box)


def check_corpus(path: Path, region: str, *, limits: tuple[int, int, int, int],
                 max_age_days: int = MAX_AGE_DAYS, max_future_skew: timedelta = MAX_FUTURE_SKEW,
                 now: datetime | None = None) -> list[str]:
    """Every failure, named. An empty list means this corpus may ship.

    `limits` is required: a call that forgot the region's box must not silently skip the content limb.
    """
    failures: list[str] = []
    try:
        meta = read_meta(path)
        extent = read_extent(path)
    except sqlite3.Error as exc:
        return [f"{Path(path).name}: meta or segments is unreadable ({exc}): this is not a corpus"]

    if meta.get("region") != region:
        failures.append(f"meta.region is {meta.get('region')!r}, expected {region!r} (P-DATA-03)")

    stamp = meta.get("built_at")
    if stamp is None or str(stamp).strip() == "":
        failures.append("meta.built_at is missing (P-DATA-03)")
    else:
        try:
            built = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        except ValueError:
            failures.append(f"meta.built_at {stamp!r} is not an ISO-8601 timestamp (P-DATA-03)")
        else:
            reference = now or datetime.now(timezone.utc)
            # `--built-at` is written as `...Z` with no offset; comparing a naive datetime against an aware
            # one RAISES instead of refusing, and a traceback is not a refusal.
            if built.tzinfo is None:
                built = built.replace(tzinfo=timezone.utc)
            if built < reference - timedelta(days=max_age_days):
                failures.append(f"meta.built_at {stamp} is older than {max_age_days} days (P-DATA-03)")
            elif built > reference + max_future_skew:
                failures.append(f"meta.built_at {stamp} is in the future by more than the "
                                f"{max_future_skew} skew tolerance (P-DATA-03)")
    # T-0233: the CONTENT - the segments' extent inside the widened box, and meta.bbox saying exactly it.
    if extent is None:
        failures.append("the corpus carries no segments: its content extent is unknown (P-DATA-03)")
    else:
        lo_lon, lo_lat, hi_lon, hi_lat = limits
        if extent[0] < lo_lon or extent[1] < lo_lat or extent[2] > hi_lon or extent[3] > hi_lat:
            failures.append(f"content extent {_e7(extent)} lies outside region {region!r}'s bbox widened by "
                            f"{CORPUS_OVERHANG_DEG} deg ({_e7(limits)}, e7) (P-DATA-03)")
        stamped = str(meta.get("bbox") or "")
        if stamped != _e7(extent):
            failures.append(f"meta.bbox {stamped!r} disagrees with the segments' extent {_e7(extent)} "
                            "(P-DATA-03)")
    return failures


def run_fixtures(region: str, limits: tuple, region_file: Path, max_age_days: int) -> int:
    try:
        from etl import corpus
        from corpus_provenance_cases import build_fixture, fixtures, translated_extract
    except ImportError as exc:
        return refuse(f"the shipping corpus builder or the fixture table is unavailable: {exc}",
                      "services/etl/etl/corpus.py owns build(); the fixtures are ITS output or they are "
                      "not evidence about the pipeline.")
    if not EXTRACT.is_file():
        return refuse(f"{EXTRACT.relative_to(ROOT).as_posix()} is missing",
                      "The pin is a property of the committed tree; a missing fixture is a refusal.")

    failures: list[str] = []
    lines: list[str] = []
    cases = fixtures(region, max_age_days)
    with TemporaryDirectory() as tmp:
        extracts = {"marin": EXTRACT, "la": translated_extract(EXTRACT, Path(tmp) / "la-extract.json")}
        for index, (label, stamped_region, built_at, drop, where, sql, want) in enumerate(cases):
            path = build_fixture(Path(tmp) / f"case{index}.sqlite", corpus, extracts[where],
                                 region=stamped_region, built_at=built_at, drop=drop, sql=sql)
            found = check_corpus(path, region, limits=limits, max_age_days=max_age_days)
            said = "; ".join(found) or "<accepted>"
            if want is None and found:
                failures.append(f"{label}: REFUSED but must be accepted; it said: {said}")
            elif want is not None and not any(want in f for f in found):
                failures.append(f"{label}: accepted or wrongly named (expected {want!r}); it said: {said}")
            elif want is None:
                lines.append(f"  {label}: accepted")
            else:
                lines.append(f"  {label}: refused, named {want!r}")

        named = os.environ.get(CORPUS_ENV)
        if named:
            real = Path(named)
            if not real.is_file():
                failures.append(f"{CORPUS_ENV}={named} names no file (set and absent is a refusal, "
                                "never a skip)")
            else:
                found = check_corpus(real, region, limits=limits, max_age_days=max_age_days)
                if found:
                    failures.append(f"the real artefact {named} was REFUSED: {'; '.join(found)}")
                else:
                    lines.append(f"  {real.name}: accepted - {describe(real)}")
        else:
            lines.append(f"  the real artefact was not checked: ${CORPUS_ENV} is unset "
                         "(a corpus is a build product and does not exist in CI)")

    if failures:
        return refuse("the region/freshness/content limbs do not decide:", *failures)
    print(f"P-DATA-03 (corpus half): ops/lib/check-corpus-provenance.py over {len(cases)} corpora built "
          f"in process by etl.corpus.build, against region {region!r} and content limits {_e7(limits)} "
          f"read from {Path(region_file).as_posix()}:")
    for line in lines:
        print(line)
    return 0


def describe(path: Path) -> str:
    meta = read_meta(path)
    return (f"region={meta.get('region')} bytes={path.stat().st_size} built_at={meta.get('built_at')} "
            f"bbox={meta.get('bbox')}")


def prove_red() -> int:
    """The mutation table, run from its sibling (T-0219 R9). A missing table is a refusal, never a pass."""
    if not MUTATIONS.is_file():
        return refuse(f"{MUTATIONS.name} is missing: this check's red evidence has no table")
    return subprocess.run([sys.executable, str(MUTATIONS)], cwd=str(ROOT)).returncode


def check_one(path: Path, region: str, limits: tuple, max_age_days: int) -> int:
    if not path.is_file():
        return refuse(f"{path} names no file")
    found = check_corpus(path, region, limits=limits, max_age_days=max_age_days)
    if found:
        print(f"CORPUS REFUSED: {path}")
        for failure in found:
            print(f"  - {failure}")
        return 1
    meta = read_meta(path)
    print(f"CORPUS OK: {path.name} {describe(path)} corpus_version={meta.get('corpus_version')} "
          f"limits={_e7(limits)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P-DATA-03's corpus half: region, built_at and content.")
    parser.add_argument("--region", default="la",
                        help="the region DIRECTORY under services/etl/regions; its region.json 'id' and 'bbox' "
                             "are the expectation, never typed here (default: la)")
    parser.add_argument("--region-json", type=Path, default=None,
                        help="read the expectation from this region.json instead of --region's")
    parser.add_argument("--corpus", type=Path, default=None,
                        help="decide ONE corpus.sqlite instead of running the fixtures")
    parser.add_argument("--max-age-days", type=int, default=MAX_AGE_DAYS)
    parser.add_argument("--prove-red", action="store_true",
                        help="apply every mutant to a copy of this file; each must be refused by name")
    args = parser.parse_args(argv)

    region_file = args.region_json or (REGIONS / args.region / "region.json")
    try:
        region, limits = load_region(region_file)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return refuse(f"the active region is unreadable: {exc}",
                      f"expected {region_file} to carry an 'id' and a finite min < max 'bbox'")

    if args.corpus is not None:
        return check_one(args.corpus, region, limits, args.max_age_days)
    if args.prove_red:
        return prove_red()
    return run_fixtures(region, limits, region_file, args.max_age_days)


if __name__ == "__main__":
    raise SystemExit(main())

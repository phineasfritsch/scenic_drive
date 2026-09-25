"""P-DATA-03's CORPUS half: corpus.sqlite's meta.region is the active region and its built_at is fresh.

    python ops/lib/check-corpus-provenance.py
    python ops/lib/check-corpus-provenance.py --prove-red
    python ops/lib/check-corpus-provenance.py --corpus <corpus.sqlite> [--region la]

THE DEFECT (T-0197 rv1/rv2-pr119, filed as T-0219). `etl.corpus` STAMPS a region - services/etl/etl/corpus.py,
`region = region or extract_region` then `writer.set_meta("region", region)` - and until this file NOTHING in
the tree read it back against the active region. A corpus cut for another region, or a year old, opens on the
phone as a complete corpus: every table present, every index built, `build_complete` = 1.

THIS FILE IS BOTH HALVES, WHICH THE TILES SIDE IS NOT. ops/lib/check-pmtiles-provenance.py subprocesses a
pre-existing shipping checker (services/tiles/check_pmtiles.py, run by build-la.sh step 6 and
ops/publish-tiles). No corpus checker existed to subprocess - that absence IS the defect - so `check_corpus`
is the shipping decision and `main` the shipping entry point: P-DATA-03's command, the pytest's subject
(services/etl/tests/test_corpus_provenance.py) and `--corpus` over a built corpus are one symbol.

THE READER (T-0219 R1). Plain sqlite3 over the `meta` table, opened READ-ONLY, which is the read shape the
shipping code already uses: surfacecoverage.py and corpusmatch.py both spell `SELECT value FROM meta WHERE
key = ?`. NOT CorpusWriter - it has no read path at all, and its `__init__` `os.remove()`s an existing file,
so "reading the union corpus through corpuswriter" would DELETE 19,906,560 bytes. Read-only is not a comment
here, it is the sqlite URI: an INSERT through this handle raises OperationalError.

THE POPULATION. A corpus is a build product and is never committed, so an assertion that ran only over a real
one would be green in CI with nothing to look at. What exists everywhere is the SHIPPING BUILDER, so the
fixtures are built in process by `corpus.build` over the seven-way tests/fixtures/corpus_extract.json - the
path test_corpus_budget.py already uses - and are not committed either: a committed corpus carries a frozen
built_at that goes stale in thirty days and turns the age limb into a calendar.

    a fresh region-la corpus          ACCEPTED   (a checker that refuses everything proves nothing)
    stamped 40 days ago               REFUSED    naming `older than 30 days (P-DATA-03)`
    stamped region 'bay'              REFUSED    naming `meta.region is 'bay'`
    no meta.region at all             REFUSED    naming `meta.region is None`
    no meta.built_at at all           REFUSED    naming `meta.built_at is missing`
    stamped two days in the future    REFUSED    naming `is in the future by more than`

The two absent-key fixtures are built by the shipping builder and then have that ONE meta row deleted through
sqlite: `CorpusWriter.finalize` REFUSES a corpus missing any REQUIRED_META_KEY, so an absent key cannot be
built and the only other way to make one is a second writer, which would no longer be the shipping stamp
(R2). Fixtures five and six are not in the filed acceptance; mutants four and five survive without them.

THE REAL ARTEFACT. When `SCENIC_LA_CORPUS` names a file the same decision runs over it and must pass - the
pin over the real build, on the box that has it. Set and naming nothing is a REFUSAL, never a skip.

WHAT IT DOES NOT COVER. Whether the corpus's CONTENT is the region it claims: one stamped `la` whose ways are
all in Marin passes here. meta.bbox is written beside region and comparing it against region.json's bbox is a
second assertion nobody has filed - the tiles half does check exactly that for PMTiles, through the header
bounds. Nor does this read count.*, surface_coverage (P-DATA-04 owns that) or content_sha256.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory


def _root() -> Path:
    """The repo root - for this file in the tree AND for a mutated copy of it outside the tree.

    A mutant copy lives in a temp directory, where `parents[2]` is somebody else's folder, so the root is
    found by MARKER rather than by depth: the parents of this file first, then the working directory (the
    mutation driver launches the copy with cwd=ROOT). Fail closed if neither carries the markers.
    """
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
MUTATIONS = Path(__file__).resolve().parent / "check-corpus-provenance-mutations.py"
CORPUS_ENV = "SCENIC_LA_CORPUS"
# P-DATA-03: built_at under 30 days, the same limit the tiles half enforces.
MAX_AGE_DAYS = 30
# The tiles half's rv1-pr109 R1, which applies harder here: `--built-at` is a REQUIRED argument typed by an
# operator (corpus.py, "An INPUT: no clock is read"), so a wrong year is reachable by hand and not only from a
# host clock set ahead. One hour is NTP drift; it is three orders of magnitude under MAX_AGE_DAYS, so it can
# never mask a stale build.
MAX_FUTURE_SKEW = timedelta(hours=1)

sys.path.insert(0, str(ETL))


def refuse(reason: str, *extra: str) -> int:
    print(f"P-DATA-03 (corpus half): {reason}")
    for line in extra:
        print(f"  {line}")
    return 1


def read_meta(path: Path) -> dict:
    """The corpus's whole meta table, READ-ONLY. The check may never mutate what it judges."""
    uri = "file:" + urllib.parse.quote(Path(path).resolve().as_posix()) + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        return {str(k): v for k, v in conn.execute("SELECT key, value FROM meta")}
    finally:
        conn.close()


def active_region(name: str) -> str:
    """The region id READ from services/etl/regions/<name>/region.json, never typed here (R3)."""
    path = REGIONS / name / "region.json"
    return str(json.loads(path.read_text(encoding="utf-8"))["id"])


def check_corpus(path: Path, region: str, *, max_age_days: int = MAX_AGE_DAYS,
                 max_future_skew: timedelta = MAX_FUTURE_SKEW,
                 now: datetime | None = None) -> list[str]:
    """Every failure, named. An empty list means this corpus may ship.

    The limits are parameters rather than constants read from the module body so a second region can state its
    own numbers instead of inheriting LA's.
    """
    failures: list[str] = []
    try:
        meta = read_meta(path)
    except sqlite3.Error as exc:
        return [f"{Path(path).name}: meta is unreadable ({exc}): this is not a corpus"]

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
    return failures


def stamp_days_ago(days: float) -> str:
    moment = datetime.now(timezone.utc) - timedelta(days=days)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_fixture(out: Path, corpus, *, region: str, built_at: str, drop: str | None = None) -> Path:
    """One corpus from the SHIPPING builder, optionally with one meta row deleted afterwards (R2)."""
    corpus.build(EXTRACT, out, built_at, region=region)
    if drop is not None:
        conn = sqlite3.connect(str(out))
        try:
            conn.execute("DELETE FROM meta WHERE key = ?", (drop,))
            conn.commit()
        finally:
            conn.close()
    return out


def fixtures(region: str) -> list[tuple]:
    """(label, stamped region, built_at, meta key dropped, the refusal it must name or None = ACCEPTED)."""
    return [
        ("a fresh region-la corpus", region, stamp_days_ago(0.001), None, None),
        ("stamped 40 days ago", region, stamp_days_ago(40), None,
         f"older than {MAX_AGE_DAYS} days (P-DATA-03)"),
        ("stamped region 'bay'", "bay", stamp_days_ago(0.001), None, "meta.region is 'bay'"),
        ("no meta.region at all", region, stamp_days_ago(0.001), "region", "meta.region is None"),
        ("no meta.built_at at all", region, stamp_days_ago(0.001), "built_at", "meta.built_at is missing"),
        ("stamped 2 days in the future", region, stamp_days_ago(-2), None, "is in the future by more than"),
    ]


def run_fixtures(region: str, max_age_days: int) -> int:
    try:
        from etl import corpus
    except ImportError as exc:
        return refuse(f"the shipping corpus builder is unavailable: {exc}",
                      "services/etl/etl/corpus.py owns build(); the fixtures are ITS output or they are "
                      "not evidence about the pipeline.")
    if not EXTRACT.is_file():
        return refuse(f"{EXTRACT.relative_to(ROOT).as_posix()} is missing",
                      "The pin is a property of the committed tree; a missing fixture is a refusal.")

    failures: list[str] = []
    lines: list[str] = []
    cases = fixtures(region)
    with TemporaryDirectory() as tmp:
        for index, (label, stamped_region, built_at, drop, want) in enumerate(cases):
            path = build_fixture(Path(tmp) / f"case{index}.sqlite", corpus,
                                 region=stamped_region, built_at=built_at, drop=drop)
            found = check_corpus(path, region, max_age_days=max_age_days)
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
                found = check_corpus(real, region, max_age_days=max_age_days)
                if found:
                    failures.append(f"the real artefact {named} was REFUSED: {'; '.join(found)}")
                else:
                    meta = read_meta(real)
                    lines.append(f"  {real.name}: accepted - region={meta.get('region')} "
                                 f"bytes={real.stat().st_size} built_at={meta.get('built_at')}")
        else:
            lines.append(f"  the real artefact was not checked: ${CORPUS_ENV} is unset "
                         "(a corpus is a build product and does not exist in CI)")

    if failures:
        return refuse("the region/freshness limbs do not decide:", *failures)
    print(f"P-DATA-03 (corpus half): ops/lib/check-corpus-provenance.py over {len(cases)} corpora built "
          f"in process by etl.corpus.build, against region {region!r} read from "
          f"{(REGIONS / region / 'region.json').relative_to(ROOT).as_posix()}:")
    for line in lines:
        print(line)
    return 0


def prove_red() -> int:
    """The mutation table, run. It lives in a sibling - ops/lib/check-corpus-provenance-mutations.py - for
    CLAUDE.md's 300-line cap and because a table that QUOTES the code it mutates cannot assert its own
    sites are unique while sitting in the same file (T-0219 R9; the precedent is
    ops/lib/check-map-attribution-mutations). A missing table is a refusal, never a pass: it is the only
    evidence this check has ever been seen red."""
    if not MUTATIONS.is_file():
        return refuse(f"{MUTATIONS.name} is missing: this check's red evidence has no table")
    return subprocess.run([sys.executable, str(MUTATIONS)], cwd=str(ROOT)).returncode


def check_one(path: Path, region: str, max_age_days: int) -> int:
    if not path.is_file():
        return refuse(f"{path} names no file")
    found = check_corpus(path, region, max_age_days=max_age_days)
    if found:
        print(f"CORPUS REFUSED: {path}")
        for failure in found:
            print(f"  - {failure}")
        return 1
    meta = read_meta(path)
    print(f"CORPUS OK: {path.name} region={meta.get('region')} bytes={path.stat().st_size} "
          f"built_at={meta.get('built_at')} corpus_version={meta.get('corpus_version')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P-DATA-03's corpus half: meta.region and meta.built_at.")
    parser.add_argument("--region", default="la",
                        help="the region DIRECTORY under services/etl/regions; its region.json 'id' is the "
                             "expected value, which is never typed here (default: la)")
    parser.add_argument("--corpus", type=Path, default=None,
                        help="decide ONE corpus.sqlite instead of running the fixtures")
    parser.add_argument("--max-age-days", type=int, default=MAX_AGE_DAYS)
    parser.add_argument("--prove-red", action="store_true",
                        help="apply every mutant to a copy of this file; each must be refused by name")
    args = parser.parse_args(argv)

    try:
        region = active_region(args.region)
    except (OSError, ValueError, KeyError) as exc:
        return refuse(f"the active region is unreadable: {exc}",
                      f"expected {(REGIONS / args.region / 'region.json')} to carry an 'id'")

    if args.corpus is not None:
        return check_one(args.corpus, region, args.max_age_days)
    if args.prove_red:
        return prove_red()
    return run_fixtures(region, args.max_age_days)


if __name__ == "__main__":
    raise SystemExit(main())

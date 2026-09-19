"""`python -m etl.corpus` - build corpus.sqlite from an extract.

    python -m etl.corpus --input tests/fixtures/corpus_extract.json --out corpus.sqlite \
        --built-at 2026-09-18T00:00:00Z [--previous prev.sqlite] [--curated regions/sfbay/curated.yaml]

`--built-at` is REQUIRED and there is no default, deliberately. Defaulting it to the wall clock would make
`meta.built_at` - and therefore the file's bytes, and therefore the OTA manifest's sha256 - different on
every build of identical input, and P-DATA-01 says two builds of the same extract are byte-identical. The
one `datetime` in this module parses the argument; nothing here reads a clock.

What this slice emits: `osm_features`, `segments` + `segments_rtree`, `term_defs`, `meta`, and
`segment_alias` when `--previous` is given. `places`, `curated`, `terms_osm` and `terms_raster` are emitted
EMPTY - the POI join, `regions/sfbay/curated.yaml` and the term producers are other tasks (see the task Log,
rulings R3, R10, R12). Every one of those tables exists in the file with its indexes, so the reader on the
device sees a complete schema and zero rows rather than a missing table.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys

from . import contentdigest, corpusmatch, schema, surfacecoverage
from .corpuswriter import CorpusWriter
from .extractway import load_extract
from .segmenter import Segmenter


# plan:283's M2 exit clause, "corpus <60 MB", as ONE literal the emitter enforces on itself. MiB rather
# than MB by T-0206 ruling R3: the plan does not distinguish, this task's acceptance line says 60 MiB, and
# MiB is the looser of the two readings, so the ceiling never refuses a corpus the plan's cell allowed.
# Measured against real LA data in T-0206: 46,231 real ways -> 19,906,560 B, 430.59 B per way, which over
# the clip's 560,208 filtered ways extrapolates to 241,224,000 B - 3.83x this budget, with terms, places
# and FTS still empty. The number below is the ceiling, NOT a claim that LA fits under it.
CORPUS_BUDGET_BYTES = 60 * 1024 * 1024

BUDGET_EXIT = 3


class CorpusTooLargeError(RuntimeError):
    """The finished corpus is over budget. The FILE IS LEFT ON DISK (T-0206 ruling R4): the exit code is
    what stops a pipeline, the bytes are what a human needs to find the overage."""


def compact_built_at(built_at: str) -> str:
    """2026-09-18T00:00:00Z -> 20260918T000000Z. The default corpus_version: derived from an input, so it is
    an input, so two builds of the same extract agree on it."""
    stamp = _dt.datetime.strptime(built_at, "%Y-%m-%dT%H:%M:%SZ")
    return stamp.strftime("%Y%m%dT%H%M%SZ")


def load_curated(path) -> list:
    """(drive_id, seq, osm_way_id, payload) rows. Absent file -> no rows; see the task Log, R10."""
    if path is None:
        return []
    import os
    if not os.path.exists(path):
        return []
    import json
    import yaml
    with open(path, "r", encoding="utf-8") as handle:
        doc = yaml.safe_load(handle) or {}
    rows = []
    for drive in doc.get("drives", []):
        drive_id = str(drive["id"])
        for seq, way_id in enumerate(drive.get("ways", [])):
            payload = json.dumps({k: v for k, v in drive.items() if k != "ways"},
                                 sort_keys=True, separators=(",", ":"))
            rows.append((drive_id, seq, int(way_id), payload))
    return rows


def build(input_path, out_path, built_at: str, previous=None, curated_path=None,
          corpus_version=None, region=None, budget_bytes: int = CORPUS_BUDGET_BYTES) -> dict:
    """Build one corpus. Returns the report `main` prints; raises on any refusal.

    `budget_bytes` defaults to the one literal above and exists as a parameter so the refusal is provable
    without a 60 MiB fixture in git (T-0206 ruling R6)."""
    extract_region, ways = load_extract(input_path)
    region = region or extract_region
    segmenter = Segmenter()
    segments = []
    for way in ways:
        segments.extend(segmenter.cut(way.way_id, list(way.coords)))

    writer = CorpusWriter(out_path)
    try:
        writer.write_features(ways)
        assigned = writer.write_segments(segments)
        writer.write_places([])
        writer.write_term_defs()
        writer.write_curated(load_curated(curated_path))

        new_ids = {sid for sid, _ in assigned}
        carry = {"previous": 0, "carried": 0, "aliased": 0, "lost": 0, "matched": 0, "aliases": []}
        changed_ways = 0
        matcher_ways = 0
        previous_digest = ""
        carry_rate = ""
        if previous is not None:
            geometry = {sid: list(seg.coords) for sid, seg in assigned}
            carry = corpusmatch.carry_forward(writer.conn, previous, new_ids, geometry)
            writer.write_aliases(carry["aliases"])
            prev_digests = corpusmatch.previous_way_digests(previous)
            changed_ways = sum(1 for w in ways
                               if w.way_id in prev_digests and prev_digests[w.way_id] != w.geom_sha256)
            matcher_ways = sum(1 for wid in prev_digests if wid not in {w.way_id for w in ways})
            previous_digest = corpusmatch.previous_content_sha256(previous)
            carry_rate = str(corpusmatch.carry_rate_bp(carry))

        writer.set_meta("schema_version", schema.SCHEMA_VERSION)
        writer.set_meta("min_app_build", schema.MIN_APP_BUILD)
        writer.set_meta("corpus_version", corpus_version or compact_built_at(built_at))
        writer.set_meta("region", region)
        writer.set_meta("bbox", writer.bbox_e7())
        writer.set_meta("built_at", built_at)
        writer.set_meta("attribution", schema.ATTRIBUTION)
        writer.set_meta("odbl_notice", schema.ODBL_NOTICE)
        writer.set_meta("table_licenses", ";".join(
            f"{t}={schema.TABLE_LICENSES[t]}" for t in sorted(schema.TABLE_LICENSES)))
        writer.set_meta("sqlite_version", _sqlite_version())
        writer.set_meta("carry_rate", carry_rate)
        # T-0205 ruling R1: the per-class surface coverage is computed ONCE, here, over the extract's own
        # ways (their RAW surface tag), and the check re-reads this value rather than recounting anything.
        writer.set_meta(surfacecoverage.META_KEY, surfacecoverage.encode(surfacecoverage.coverage(ways)))
        writer.set_meta("previous_content_sha256", previous_digest)
        writer.write_counts({
            "closed_ways": sum(1 for w in ways if w.is_closed),
            "changed_ways": changed_ways,
            "matcher_ways": matcher_ways,
            "ids_carried": carry["carried"],
            "ids_lost": carry["lost"],
            "ids_aliased": carry["aliased"],
        })
        content = writer.finalize()
    finally:
        writer.close()

    import os
    size = os.path.getsize(out_path)
    if size > budget_bytes:
        raise CorpusTooLargeError(
            f"{out_path}: the corpus is {size} bytes, over the budget of {budget_bytes} bytes "
            f"(plan:283, 'corpus <60 MB'). The file is LEFT ON DISK so the overage can be inspected.")

    return {
        "region": region,
        "bytes": size,
        "budget_bytes": budget_bytes,
        "ways": len(ways),
        "segments": len(segments),
        "collisions": writer.collisions,
        "content_sha256": content,
        "file_sha256": contentdigest.file_sha256(out_path),
        "carry_rate_bp": carry_rate,
        "ids_carried": carry["carried"],
        "ids_aliased": carry["aliased"],
        "ids_lost": carry["lost"],
        "previous_ids": carry["previous"],
    }


def _sqlite_version() -> str:
    import sqlite3
    return sqlite3.sqlite_version


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="python -m etl.corpus", description="build corpus.sqlite")
    parser.add_argument("--input", required=True, help="JSON synthetic extract (see etl/extractway.py)")
    parser.add_argument("--out", required=True, help="corpus.sqlite to write; overwritten if it exists")
    parser.add_argument("--built-at", required=True, metavar="ISO",
                        help="build stamp, e.g. 2026-09-18T00:00:00Z. An INPUT: no clock is read.")
    parser.add_argument("--previous", default=None, help="previous corpus.sqlite, to carry ids forward")
    parser.add_argument("--curated", default=None, help="curated.yaml; absent file means no curated rows")
    parser.add_argument("--corpus-version", default=None, help="default: --built-at compacted")
    parser.add_argument("--region", default=None, help="default: the extract's own region")
    parser.add_argument("--budget-bytes", type=int, default=CORPUS_BUDGET_BYTES, metavar="N",
                        help=f"refuse a corpus over N bytes; default {CORPUS_BUDGET_BYTES} (60 MiB)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        compact_built_at(args.built_at)
    except ValueError:
        print(f"--built-at must be YYYY-MM-DDTHH:MM:SSZ, got {args.built_at!r}", file=sys.stderr)
        return 2
    try:
        report = build(args.input, args.out, args.built_at, previous=args.previous,
                       curated_path=args.curated, corpus_version=args.corpus_version,
                       region=args.region, budget_bytes=args.budget_bytes)
    except CorpusTooLargeError as too_large:
        print(f"CORPUS REFUSED {too_large}", file=sys.stderr)
        return BUDGET_EXIT
    print(f"CORPUS region={report['region']} ways={report['ways']} segments={report['segments']} "
          f"collisions={report['collisions']}")
    print(f"CORPUS bytes={report['bytes']} budget={report['budget_bytes']}")
    print(f"CORPUS content_sha256={report['content_sha256']}")
    print(f"CORPUS file_sha256={report['file_sha256']}")
    if report["previous_ids"]:
        print(f"CORPUS carry previous={report['previous_ids']} carried={report['ids_carried']} "
              f"aliased={report['ids_aliased']} lost={report['ids_lost']} "
              f"rate_bp={report['carry_rate_bp']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

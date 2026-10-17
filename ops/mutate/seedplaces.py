#!/usr/bin/env python3
"""Mutation harness AND population for etl/seedplaces.py and its entry point ops/seed-places (T-0393, ruling R8).

WHY IT HAS ONE. seedplaces turns the corpus into the D1 rows the Worker resolves every /plan and /trip destination
against, so the coordinate a route is planned to is decided here. Covered: every bound of every row field and of
--chunk, the schema/build/empty refusals, the type check, the upsert, the coordinate and id spelling, the chunk
step, the summary line and its digest, the out-dir and dry-run guards, the exit code and the wrapper's default.

THE CONTRACT is ops/mutate/extractadapter.py's, kept identically: `(name, file, old, new)` entries whose `old`
must appear VERBATIM or the run FAILS; a catch requires a NAMED TEST to fail; subjects, emptied tests and this
file are compared to `git show HEAD:` first and after; `MIN_MUTATIONS` EQUALS the population; an EQUIVALENT
catch is a FAILURE; `--prove-vacuity` empties the tests and requires every mutation MISSED; `--only` runs a
named subset. Every `__pycache__` under services/etl is purged before each run, then 1.1 s.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mutate_only

import extractadapter as harness  # noqa: E402  the protocol: pristine guard, pycache purge, arm

ETL = harness.ETL
SUBJECT = ETL / "etl" / "seedplaces.py"
WRAPPER = ETL.parents[1] / "ops" / "seed-places"
TESTS = ETL / "tests" / "test_seedplaces.py"
EMPTIED = (TESTS,)
SUBJECTS = (SUBJECT, WRAPPER)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/seedplaces.py",)
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

LAT = "        if not is_int(lat_e7) or not -LAT_E7_MAX <= lat_e7 <= LAT_E7_MAX:"
LON = "        if not is_int(lon_e7) or not -LON_E7_MAX <= lon_e7 <= LON_E7_MAX:"
PID = "        if not is_int(place_id) or not 1 <= place_id <= PLACE_ID_MAX:"
SCHEMA = '    if meta.get("schema_version") != str(schema.SCHEMA_VERSION):'
BUILD = '    if meta.get("build_complete") != "1":'
EMPTY = "    if not rows:\n"
CHUNK = "    if not 1 <= chunk <= CHUNK_MAX:"
ONE_OF = "    if dry_run == (out is not None):"
OUT_DIR = "    if out is not None and out.exists() and (not out.is_dir() or any(out.iterdir())):"
MKDIR = "    out.mkdir(parents=True, exist_ok=True)"
UPSERT = 'TAIL = "\\nON CONFLICT (id) DO UPDATE SET lat = excluded.lat, lon = excluded.lon;\\n"'
VALUE = "    return f\"('{place_id}', {lat_e7} / 10000000.0, {lon_e7} / 10000000.0)\""
STEP = "            for start in range(0, len(rows), chunk)]"
SLICE = "rows[start:start + chunk]"
LINE = '        digest.update(f"{place_id}\\t{lat_e7}\\t{lon_e7}\\n".encode("ascii"))'
COUNT = "rows={len(rows)} chunks={chunks} "
FILE = '        path = out / f"places-{index:04d}.sql"'
DEFAULT = '  --corpus "$root/apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite" "$@"'

MUTATIONS = [
    ("CHUNK_DEFAULT raised", SUBJECT, "CHUNK_DEFAULT = 500", "CHUNK_DEFAULT = 501"),
    ("CHUNK_DEFAULT lowered", SUBJECT, "CHUNK_DEFAULT = 500", "CHUNK_DEFAULT = 499"),
    ("CHUNK_MAX raised", SUBJECT, "CHUNK_MAX = 1000", "CHUNK_MAX = 1001"),
    ("CHUNK_MAX lowered", SUBJECT, "CHUNK_MAX = 1000", "CHUNK_MAX = 999"),
    ("chunk 0 accepted", SUBJECT, CHUNK, "    if not 0 <= chunk <= CHUNK_MAX:"),
    ("PLACE_ID_MAX lowered", SUBJECT, "PLACE_ID_MAX = 2 ** 63 - 1", "PLACE_ID_MAX = 2 ** 63 - 2"),
    ("LAT_E7_MAX raised", SUBJECT, "LAT_E7_MAX = 900000000", "LAT_E7_MAX = 900000001"),
    ("LAT_E7_MAX lowered", SUBJECT, "LAT_E7_MAX = 900000000", "LAT_E7_MAX = 899999999"),
    ("LON_E7_MAX raised", SUBJECT, "LON_E7_MAX = 1800000000", "LON_E7_MAX = 1800000001"),
    ("LON_E7_MAX lowered", SUBJECT, "LON_E7_MAX = 1800000000", "LON_E7_MAX = 1799999999"),
    ("place_id 0 accepted", SUBJECT, PID, PID.replace("not 1 <=", "not 0 <=")),
    ("place_id type check dropped", SUBJECT, PID, PID.replace("not is_int(place_id) or ", "")),
    ("lat lower bound dropped", SUBJECT, LAT, "        if not is_int(lat_e7) or not lat_e7 <= LAT_E7_MAX:"),
    ("lat upper bound dropped", SUBJECT, LAT, "        if not is_int(lat_e7) or not -LAT_E7_MAX <= lat_e7:"),
    ("lat type check dropped", SUBJECT, LAT, LAT.replace("not is_int(lat_e7) or ", "")),
    ("lon lower bound dropped", SUBJECT, LON, "        if not is_int(lon_e7) or not lon_e7 <= LON_E7_MAX:"),
    ("lon upper bound dropped", SUBJECT, LON, "        if not is_int(lon_e7) or not -LON_E7_MAX <= lon_e7:"),
    ("lon type check dropped", SUBJECT, LON, LON.replace("not is_int(lon_e7) or ", "")),
    ("lat checked against the lon range", SUBJECT, LAT, LAT.replace("LAT_E7_MAX", "LON_E7_MAX")),
    ("is_int accepts floats", SUBJECT, "    return type(value) is int", "    return isinstance(value, (int, float))"),
    ("schema_version not checked", SUBJECT, SCHEMA, "    if False:"),
    ("build_complete not checked", SUBJECT, BUILD, "    if False:"),
    ("an empty corpus accepted", SUBJECT, EMPTY, "    if False:\n"),
    ("the upsert does nothing on conflict", SUBJECT, UPSERT, 'TAIL = "\\nON CONFLICT (id) DO NOTHING;\\n"'),
    ("the upsert updates lat only", SUBJECT, UPSERT,
     'TAIL = "\\nON CONFLICT (id) DO UPDATE SET lat = excluded.lat;\\n"'),
    ("lat and lon swapped", SUBJECT, VALUE,
     "    return f\"('{place_id}', {lon_e7} / 10000000.0, {lat_e7} / 10000000.0)\""),
    ("divided by 1e6", SUBJECT, VALUE, VALUE.replace("10000000.0", "1000000.0")),
    ("the id unquoted - an integer, not D1's TEXT", SUBJECT, VALUE, VALUE.replace("'{place_id}'", "{place_id}")),
    ("the coordinate rendered as a rounded decimal", SUBJECT, VALUE,
     "    return f\"('{place_id}', {lat_e7 / 10 ** 7:.6f}, {lon_e7 / 10 ** 7:.6f})\""),
    ("chunks overlap by one row", SUBJECT, SLICE, "rows[start:start + chunk + 1]"),
    ("the chunk step skips a row", SUBJECT, STEP, "            for start in range(0, len(rows), chunk + 1)]"),
    ("the digest line separator changed", SUBJECT, LINE, LINE.replace("\\t", ",")),
    ("the digest omits lon", SUBJECT, LINE, '        digest.update(f"{place_id}\\t{lat_e7}\\n".encode("ascii"))'),
    ("rows= prints the chunk count", SUBJECT, COUNT, "rows={chunks} chunks={chunks} "),
    ("--dry-run with --out accepted", SUBJECT, ONE_OF, "    if dry_run and out is not None:"),
    ("a non-empty out dir accepted", SUBJECT, OUT_DIR, "    if False:"),
    ("an existing empty out dir crashes - exist_ok dropped", SUBJECT, MKDIR, "    out.mkdir(parents=True)"),
    ("a nested out dir crashes - parents dropped", SUBJECT, MKDIR, "    out.mkdir(exist_ok=True)"),
    ("an out file reaches iterdir - the is_dir clause dropped", SUBJECT, OUT_DIR,
     "    if out is not None and out.exists() and any(out.iterdir()):"),
    ("an out file accepted", SUBJECT, OUT_DIR,
     "    if out is not None and out.exists() and out.is_dir() and any(out.iterdir()):"),
    ("every existing out path refused", SUBJECT, OUT_DIR, "    if out is not None and out.exists() and True:"),
    ("an absent out path refused - the exists clause dropped", SUBJECT, OUT_DIR,
     "    if out is not None and (not out.is_dir() or any(out.iterdir())):"),
    ("an out dir holding only subdirectories accepted", SUBJECT, OUT_DIR,
     "    if out is not None and out.exists() and (not out.is_dir() or any(q.is_file() for q in out.iterdir())):"),
    ("an out dir holding only dotfiles accepted", SUBJECT, OUT_DIR,
     "    if out is not None and out.exists() and (not out.is_dir() or "
     "any(not q.name.startswith('.') for q in out.iterdir())):"),
    ("chunk files numbered from 0", SUBJECT, "enumerate(texts, start=1)", "enumerate(texts)"),
    ("chunk file name changed", SUBJECT, FILE, '        path = out / f"places-{index}.sql"'),
    ("the wrangler line names another database", SUBJECT, 'D1_DATABASE = "scenic"', 'D1_DATABASE = "scenic-test"'),
    ("the wrangler line is not --remote", SUBJECT, "execute {D1_DATABASE} --remote --file", "execute {D1_DATABASE} --file"),
    ("a refusal exits 1", SUBJECT, "REFUSED = 2", "REFUSED = 1"),
    ("the wrapper defaults to no corpus", WRAPPER, DEFAULT, '  "$@"'),
    ("the wrapper defaults to the LA work corpus", WRAPPER, DEFAULT,
     '  --corpus "$root/services/etl/work/t0266/la-corpus.sqlite" "$@"'),
]

EQUIVALENT = [
    ("the canonical digest unsorted - read_corpus already returns rows ORDER BY place_id, and canonical_sha256 has "
     "no other caller", SUBJECT, "    for place_id, lat_e7, lon_e7 in sorted(rows):",
     "    for place_id, lat_e7, lon_e7 in rows:"),
]
KNOWN_MISSED = []

MIN_MUTATIONS = 51
harness.PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"] + [str(path) for path in EMPTIED]


def main(argv: list | None = None) -> int:
    only = mutate_only.select_only(sys.argv[1:] if argv is None else argv,
                                   [m[0] for m in list(MUTATIONS) + list(EQUIVALENT)], substring=True,
                                   split=False)
    parser = argparse.ArgumentParser(allow_abbrev=False, prog="ops/mutate/seedplaces.py",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--prove-vacuity", action="store_true",
                        help="empty the test file and require every mutation to be MISSED")
    parser.add_argument("--only", action="append", default=[], metavar="SUBSTRING",
                        help="run only the entries whose name contains SUBSTRING (repeatable)")
    args = parser.parse_args(argv)
    if len(MUTATIONS) < MIN_MUTATIONS:
        print("population is %d, floor is %d" % (len(MUTATIONS), MIN_MUTATIONS), file=sys.stderr)
        return 1
    mutations = [m for m in MUTATIONS if only is None or m[0] in only]
    equivalent = [m for m in EQUIVALENT if only is None or m[0] in only]
    harness.assert_pristine(GUARDED)
    originals = {path: path.read_text(encoding="utf-8") for path in SUBJECTS + EMPTIED}
    subjects = {path: originals[path] for path in SUBJECTS}
    if args.prove_vacuity:
        for path in EMPTIED:
            path.write_text("", encoding="utf-8", newline="\n")
        caught, missed, skipped = harness.arm(mutations, subjects, False, "VACUITY")
        harness.restore(originals)
        harness.assert_pristine(GUARDED)
        ok = caught == 0 and skipped == 0 and missed == len(mutations)
        print("VACUITY %s" % ("PROVED" if ok else "FAILED"))
        return 0 if ok else 1
    code, failed = harness.run_tests()
    if code != 0 or failed:
        print("BASELINE is not green: exit %d, %s" % (code, failed), file=sys.stderr)
        return 1
    print("BASELINE exit=0, %d mutations, floor %d" % (len(mutations), MIN_MUTATIONS))
    caught, missed, skipped = harness.arm(mutations, subjects, True, "MUTATIONS")
    eq_caught, _eq_missed, eq_skipped = harness.arm(equivalent, subjects, False, "EQUIVALENT")
    harness.assert_pristine(GUARDED)
    ok = caught == len(mutations) and skipped == 0 and eq_caught == 0 and eq_skipped == 0 and not KNOWN_MISSED
    print("MUTATE %s  caught=%d/%d equivalent_caught=%d" % ("OK" if ok else "FAILED", caught,
                                                            len(mutations), eq_caught))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

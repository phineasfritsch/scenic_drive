"""ops/seed-places, through the shipped entry point (T-0393 rulings R1-R7).

The fixture corpus is built here from etl.schema's own DDL; `ops/seed-places` turns it into the SQL committed under
services/api/test/fixtures/seed-places/, which services/api/test/seedPlaces.test.ts applies to a local D1 and reads
back whole. The committed files must equal a fresh run byte for byte, so a change to the exporter that is not
re-exported (and so not re-proved against D1) is red here by name.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import sqlite3
import contextlib
import io
import subprocess
import sys
import types

import pytest

from etl import schema, seedplaces

ROOT = pathlib.Path(__file__).resolve().parents[3]
ENTRY = ROOT / "ops" / "seed-places"
FALLBACK = ROOT / "apps" / "ios" / "ScenicDrive" / "Corpus" / "corpus-fallback.sqlite"
COMMITTED = ROOT / "services" / "api" / "test" / "fixtures" / "seed-places"
FIXTURE_CHUNK = 2

# (place_id, lat_e7, lon_e7): a real LA row, the fallback's largest id, both bounds of every range, and 2^53 + 1 -
# the first id a float or a JS number cannot hold.
FIXTURE_ROWS = [
    (5618378043290861, 342641350, -1185229920),
    (9221466198646572373, 344491615, -1178446900),
    (1, 900000000, 1800000000),
    (9223372036854775807, -900000000, -1800000000),
    (9007199254740993, 0, 0),
]

EXPECTED_FILES = {
    "places-0001.sql": "INSERT INTO places (id, lat, lon) VALUES\n"
                       "('1', 900000000 / 10000000.0, 1800000000 / 10000000.0),\n"
                       "('5618378043290861', 342641350 / 10000000.0, -1185229920 / 10000000.0)\n"
                       "ON CONFLICT (id) DO UPDATE SET lat = excluded.lat, lon = excluded.lon;\n",
    "places-0002.sql": "INSERT INTO places (id, lat, lon) VALUES\n"
                       "('9007199254740993', 0 / 10000000.0, 0 / 10000000.0),\n"
                       "('9221466198646572373', 344491615 / 10000000.0, -1178446900 / 10000000.0)\n"
                       "ON CONFLICT (id) DO UPDATE SET lat = excluded.lat, lon = excluded.lon;\n",
    "places-0003.sql": "INSERT INTO places (id, lat, lon) VALUES\n"
                       "('9223372036854775807', -900000000 / 10000000.0, -1800000000 / 10000000.0)\n"
                       "ON CONFLICT (id) DO UPDATE SET lat = excluded.lat, lon = excluded.lon;\n",
}


def bash() -> str:
    found = shutil.which("bash")
    assert found is not None
    return found


def seed(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHON=sys.executable)
    return subprocess.run([bash(), str(ENTRY), *args], capture_output=True, text=True, env=env, cwd=ROOT)


def main(*args: str) -> types.SimpleNamespace:
    """`python -m etl.seedplaces` - what ops/seed-places execs - in process: the refusal tables run in seconds."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = seedplaces.main(list(args))
    return types.SimpleNamespace(returncode=code, stdout=out.getvalue(), stderr=err.getvalue())


def sha(rows) -> str:
    text = "".join(f"{p}\t{a}\t{o}\n" for p, a, o in sorted(rows))
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def full_corpus(path: pathlib.Path, rows, meta=None) -> pathlib.Path:
    conn = sqlite3.connect(path)
    schema.apply_schema(conn)
    values = {"schema_version": str(schema.SCHEMA_VERSION), "build_complete": "1", "region": "fx",
              "corpus_version": "20261017T000000Z"} if meta is None else meta
    conn.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", sorted(values.items()))
    conn.executemany("INSERT INTO places (place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7) "
                     "VALUES (?, 'n', ?, 'park', NULL, ?, ?)",
                     [(p, i + 1, o, a) for i, (p, a, o) in enumerate(rows)])
    conn.commit()
    conn.close()
    return path


def loose_corpus(path: pathlib.Path, rows) -> pathlib.Path:
    """A corrupt corpus: right meta, a places table with no types or CHECKs, so any value can reach the exporter."""
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("CREATE TABLE places (place_id, lat_e7, lon_e7)")
    conn.executemany("INSERT INTO meta VALUES (?, ?)", [("schema_version", str(schema.SCHEMA_VERSION)),
                                                        ("build_complete", "1")])
    conn.executemany("INSERT INTO places VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return path


def written(out: pathlib.Path) -> dict:
    return {p.name: p.read_bytes().decode("ascii") for p in sorted(out.iterdir())} if out.exists() else {}


def test_fixture_export_equals_typed_sql_and_the_committed_files(tmp_path):
    corpus = full_corpus(tmp_path / "fx.sqlite", FIXTURE_ROWS)
    out = tmp_path / "out"
    done = seed("--corpus", str(corpus), "--out", str(out), "--chunk", str(FIXTURE_CHUNK))
    assert done.returncode == 0, done.stderr
    assert written(out) == EXPECTED_FILES
    assert written(COMMITTED) == EXPECTED_FILES
    assert done.stdout.splitlines() == [
        f"seed-places: schema_version={schema.SCHEMA_VERSION} region=fx corpus_version=20261017T000000Z rows=5 "
        f"chunks=3 sha256={sha(FIXTURE_ROWS)}"] + [
        f"npx wrangler d1 execute scenic --remote --file {out / name}" for name in sorted(EXPECTED_FILES)]


def test_rerun_into_a_fresh_dir_writes_the_same_bytes(tmp_path):
    corpus = full_corpus(tmp_path / "fx.sqlite", FIXTURE_ROWS)
    first, second = tmp_path / "a", tmp_path / "b"
    assert seed("--corpus", str(corpus), "--out", str(first), "--chunk", "2").returncode == 0
    assert seed("--corpus", str(corpus), "--out", str(second), "--chunk", "2").returncode == 0
    assert written(first) == written(second) == EXPECTED_FILES


def test_dry_run_of_the_bundled_fallback_is_its_whole_canonical_rows(tmp_path):
    conn = sqlite3.connect(f"{FALLBACK.as_uri()}?mode=ro", uri=True)
    rows = conn.execute("SELECT place_id, lat_e7, lon_e7 FROM places").fetchall()
    meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    conn.close()
    done = seed("--dry-run")
    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines() == [
        f"seed-places: schema_version=4 region=la corpus_version={meta['corpus_version']} rows={len(rows)} "
        f"chunks={-(-len(rows) // 500)} sha256={sha(rows)}"]
    assert len(rows) == 1334


def test_default_chunk_is_500_rows_per_statement(tmp_path):
    rows = [(i, i, -i) for i in range(1, 1002)]
    out = tmp_path / "out"
    assert main("--corpus", str(full_corpus(tmp_path / "c.sqlite", rows)), "--out", str(out)).returncode == 0
    files = written(out)
    assert sorted(files) == ["places-0001.sql", "places-0002.sql", "places-0003.sql"]
    assert [text.count(" / 10000000.0)") for text in files.values()] == [500, 500, 1]
    assert files["places-0003.sql"] == ("INSERT INTO places (id, lat, lon) VALUES\n"
                                        "('1001', 1001 / 10000000.0, -1001 / 10000000.0)\n"
                                        "ON CONFLICT (id) DO UPDATE SET lat = excluded.lat, lon = excluded.lon;\n")


def test_the_widest_statement_the_largest_chunk_can_make_fits_d1s_100000_bytes(tmp_path):
    rows = [(9223372036854775807 - i, -900000000, -1800000000) for i in range(1000)]
    out = tmp_path / "out"
    assert main("--corpus", str(full_corpus(tmp_path / "c.sqlite", rows)), "--out", str(out),
                "--chunk", "1000").returncode == 0
    files = written(out)
    assert list(files) == ["places-0001.sql"]
    assert 70000 < len(files["places-0001.sql"].encode("ascii")) < 100000


GOOD_META = {"schema_version": str(schema.SCHEMA_VERSION), "build_complete": "1"}


@pytest.mark.parametrize("meta", [
    dict(GOOD_META, schema_version=str(schema.SCHEMA_VERSION - 1)),
    dict(GOOD_META, schema_version=str(schema.SCHEMA_VERSION + 1)),
    {"build_complete": "1"},
    dict(GOOD_META, build_complete="0"),
    {"schema_version": str(schema.SCHEMA_VERSION)},
], ids=["schema-minus-1", "schema-plus-1", "schema-missing", "build-incomplete", "build-complete-missing"])
def test_a_corpus_from_another_schema_or_an_unfinished_build_is_refused_and_nothing_written(tmp_path, meta):
    out = tmp_path / "out"
    done = main("--corpus", str(full_corpus(tmp_path / "c.sqlite", FIXTURE_ROWS, meta)), "--out", str(out))
    assert (done.returncode, done.stdout, written(out)) == (2, "", {})


def test_a_corpus_with_no_places_is_refused(tmp_path):
    out = tmp_path / "out"
    done = main("--corpus", str(full_corpus(tmp_path / "c.sqlite", [])), "--out", str(out))
    assert (done.returncode, done.stdout, written(out)) == (2, "", {})


def test_a_missing_corpus_is_refused(tmp_path):
    done = main("--corpus", str(tmp_path / "absent.sqlite"), "--dry-run")
    assert (done.returncode, done.stdout) == (2, "")


@pytest.mark.parametrize("args", [["--dry-run", "--chunk", "0"], ["--dry-run", "--chunk", "1001"], []],
                         ids=["chunk-0", "chunk-1001", "neither-dry-run-nor-out"])
def test_bad_arguments_are_refused(tmp_path, args):
    done = main("--corpus", str(full_corpus(tmp_path / "c.sqlite", FIXTURE_ROWS)), *args)
    assert (done.returncode, done.stdout) == (2, "")


def test_chunk_1000_is_accepted_and_dry_run_with_out_refused(tmp_path):
    corpus = str(full_corpus(tmp_path / "c.sqlite", FIXTURE_ROWS))
    assert main("--corpus", corpus, "--dry-run", "--chunk", "1000").stdout.split(" chunks=")[1][:2] == "1 "
    assert main("--corpus", corpus, "--dry-run", "--out", str(tmp_path / "o")).returncode == 2


def state(path: pathlib.Path):
    """What is at `path`: None if nothing, the bytes of a regular file, else the directory's files by name."""
    if not path.exists():
        return None
    return path.read_bytes() if path.is_file() else written(path)


# --out PATH before the run: (name, the relative path, what to create there, accepted). The expected exit code,
# stdout, stderr and after-state are each computed from the row and its absolute path below, never typed per row.
OUT_STATES = [
    ("absent", "out", None, True),
    ("absent-under-an-absent-parent", "a/b/out", None, True),
    ("existing-empty-dir", "out", {}, True),
    ("existing-non-empty-dir", "out", {"keep.txt": "x"}, False),
    ("existing-regular-file", "out", b"x", False),
    ("existing-empty-regular-file", "out", b"", False),
]


@pytest.mark.parametrize("rel,before,accepted", [r[1:] for r in OUT_STATES], ids=[r[0] for r in OUT_STATES])
def test_every_out_state_exits_0_or_2_with_exact_output_and_files(tmp_path, rel, before, accepted):
    out = tmp_path / rel
    if isinstance(before, bytes):
        out.write_bytes(before)
    elif before is not None:
        out.mkdir()
        for name, text in before.items():
            (out / name).write_text(text, encoding="ascii")
    snapshot = state(out)
    corpus = full_corpus(tmp_path / "c.sqlite", FIXTURE_ROWS)
    done = main("--corpus", str(corpus), "--out", str(out), "--chunk", str(FIXTURE_CHUNK))
    head = (f"seed-places: schema_version={schema.SCHEMA_VERSION} region=fx corpus_version=20261017T000000Z rows=5 "
            f"chunks=3 sha256={sha(FIXTURE_ROWS)}")
    if accepted:
        expected = (0, "".join(f"{line}\n" for line in [head] + [
            f"npx wrangler d1 execute scenic --remote --file {out / name}" for name in sorted(EXPECTED_FILES)]),
            "", EXPECTED_FILES)
    else:
        expected = (2, "", f"seed-places: REFUSED: --out {out} exists and is not an empty directory\n", snapshot)
    assert (done.returncode, done.stdout, done.stderr, state(out)) == expected


BOUNDS = [
    ((0, 0, 0), 2), ((-1, 0, 0), 2), ((1, 0, 0), 0), ((9223372036854775807, 0, 0), 0), ((5.0, 0, 0), 2),
    (("5", 0, 0), 2), ((None, 0, 0), 2),
    ((5, 900000000, 0), 0), ((5, 900000001, 0), 2), ((5, -900000000, 0), 0), ((5, -900000001, 0), 2),
    ((5, 0, 1800000000), 0), ((5, 0, 1800000001), 2), ((5, 0, -1800000000), 0), ((5, 0, -1800000001), 2),
    ((5, 1.0, 0), 2), ((5, 0, 1.0), 2), ((5, "1", 0), 2), ((5, 0, "1"), 2), ((5, None, 0), 2), ((5, 0, None), 2),
]


@pytest.mark.parametrize("row,code", BOUNDS, ids=[f"{r}->{c}" for r, c in BOUNDS])
def test_every_bound_of_every_row_field(tmp_path, row, code):
    out = tmp_path / "out"
    done = main("--corpus", str(loose_corpus(tmp_path / "c.sqlite", [row])), "--out", str(out))
    assert done.returncode == code, done.stderr
    if code == 0:
        assert written(out) == {"places-0001.sql": "INSERT INTO places (id, lat, lon) VALUES\n"
                                f"('{row[0]}', {row[1]} / 10000000.0, {row[2]} / 10000000.0)\n"
                                "ON CONFLICT (id) DO UPDATE SET lat = excluded.lat, lon = excluded.lon;\n"}
    else:
        assert written(out) == {}

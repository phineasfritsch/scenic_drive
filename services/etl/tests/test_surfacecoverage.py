"""T-0205: the corpus meta carries surface coverage per highway class, and a check refuses a collapse.

Every test that names the defect binds to the SHIPPING entry point (CLAUDE.md): the meta test builds a corpus
with `corpus.build`, the one `python -m etl.corpus` runs, and reads meta back out of the built file; the check
tests call `surfacecoverage.main`, the one the pin runs. Nothing here asserts a helper against a literal
table, and nothing recomputes the coverage it is checking.
"""
from __future__ import annotations

import json
import math
import pathlib
import subprocess
import sys

import pytest

from etl import corpus, schema, surfacecoverage

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
EXTRACT = FIXTURES / "corpus_extract.json"
LA_WINDOW = FIXTURES / "surface_coverage_la_window.json"
BELOW_BASELINE = FIXTURES / "surface_coverage_below_baseline.json"
BUILT_AT = "2026-01-01T00:00:00Z"

# What corpus_extract.json's seven ways are, read off their RAW surface tags: one motorway and one
# residential and two secondaries with no tag, a `cobblestone` tertiary beside an untagged one, and a
# `gravel` unclassified.
EXPECTED = {
    "motorway": {"known": 0, "unknown": 1, "unpaved": 0, "total": 1},
    "residential": {"known": 0, "unknown": 1, "unpaved": 0, "total": 1},
    "secondary": {"known": 0, "unknown": 2, "unpaved": 0, "total": 2},
    "tertiary": {"known": 1, "unknown": 1, "unpaved": 0, "total": 2},
    "unclassified": {"known": 0, "unknown": 0, "unpaved": 1, "total": 1},
}


def build(tmp_path) -> pathlib.Path:
    out = tmp_path / "corpus.sqlite"
    corpus.build(str(EXTRACT), str(out), BUILT_AT)
    return out


def test_corpus_meta_carries_the_surface_coverage_table_per_class(tmp_path):
    assert surfacecoverage.from_corpus(build(tmp_path)) == EXPECTED


def test_an_untagged_motorway_is_unknown_and_not_known(tmp_path):
    """The whole reason coverage is not read off `osm_features.surface` (ruling R1b).

    That column calls an untagged motorway PAVED - surface.py says so - and a coverage table built from it
    would claim every freeway was surveyed. The built corpus must disagree with its own column here.
    """
    table = surfacecoverage.from_corpus(build(tmp_path))
    assert table["motorway"]["known"] == 0
    assert table["motorway"]["unknown"] == 1


def test_a_gravel_way_counts_as_unpaved_and_not_as_unknown(tmp_path):
    table = surfacecoverage.from_corpus(build(tmp_path))
    assert table["unclassified"]["unpaved"] == 1
    assert table["unclassified"]["unknown"] == 0


def test_the_meta_key_is_required_so_a_corpus_cannot_ship_without_it():
    assert surfacecoverage.META_KEY in schema.REQUIRED_META_KEYS
    assert surfacecoverage.META_KEY not in schema.DIGEST_EXCLUDED_META


def test_adding_the_meta_key_did_not_move_schema_version():
    """Ruling R2: a meta key is not DDL, so no device's corpus is invalidated over the air."""
    assert schema.SCHEMA_VERSION == 2


def test_the_check_refuses_residential_below_its_baseline_by_name(tmp_path, capsys):
    """RED BY NAME: the class is named in the refusal, not a count of failures."""
    # The literal 1, never `surfacecoverage.REFUSAL_EXIT`: a test that reads the module's own constant
    # cannot see that constant set to 0, which is the shape of the defect scenic_tags.py caught in
    # scenecheck.py (REFUSAL_EXIT = 0 reports the failure with a passing exit code).
    assert surfacecoverage.main(["--table", str(BELOW_BASELINE)]) == 1
    err = capsys.readouterr().err
    assert "residential" in err
    assert "below the baseline" in err


def test_the_check_is_green_over_the_measured_la_window(capsys):
    assert surfacecoverage.main(["--table", str(LA_WINDOW)]) == 0
    assert "refused=0" in capsys.readouterr().out


def test_the_check_prints_the_fraction_as_a_number_for_every_class(capsys):
    surfacecoverage.main(["--table", str(LA_WINDOW)])
    out = capsys.readouterr().out
    table = json.loads(LA_WINDOW.read_text(encoding="utf-8"))
    assert len(out.strip().splitlines()) == len(table) + 1
    assert "known_frac=0.1222" in out


def test_every_baseline_is_met_by_the_window_it_was_measured_from():
    """A baseline raised above the real population, or lowered to nothing, is caught here rather than by a
    build that refuses everything or by one that can no longer refuse anything."""
    table = surfacecoverage.from_table_file(LA_WINDOW)
    for cls, baseline in sorted(surfacecoverage.BASELINES.items()):
        assert baseline > 0.0, cls
        assert surfacecoverage.known_fraction(table[cls]) >= baseline, cls
        assert table[cls]["total"] >= surfacecoverage.MIN_CLASS_WAYS, cls


def test_a_class_under_the_minimum_count_gets_no_fraction_verdict(capsys):
    """Ruling R3: below 25 ways one way moves the fraction by over four points, so it is not a verdict.

    It is still REFUSED - by name, as a class too small to judge (ruling S3) - which is a different sentence
    from "its coverage collapsed", and the two must not be confused.
    """
    small = {"residential": {"known": 0, "unknown": 5, "unpaved": 0, "total": 5}}
    assert surfacecoverage.refusals(small) == []
    assert surfacecoverage.main(["--table", _write(small, capsys)]) == 1
    assert "residential has only 5 ways" in capsys.readouterr().err


def test_baselines_are_exactly_the_measurement_times_the_ruled_margin():
    """Ruling S2. `"motorway": 0.593` -> `0.001` used to pass every test in this file: nothing bound the
    literals to the population they are supposed to be 75% of. Here the RULE (the margin, the floor, the
    truncation) comes from the module and every NUMBER comes from the committed measurement."""
    table = surfacecoverage.from_table_file(LA_WINDOW)
    expected = {}
    for cls, row in table.items():
        if row["total"] >= surfacecoverage.MIN_CLASS_WAYS:
            scaled = (row["known"] / row["total"]) * surfacecoverage.BASELINE_MARGIN
            expected[cls] = math.floor(scaled * 1000) / 1000
    assert surfacecoverage.BASELINES == expected
    assert set(surfacecoverage.BASELINES) == set(expected)


def test_the_check_refuses_a_table_where_nothing_was_judged(capsys):
    """Ruling S3, the three shapes that were green on pristine code: no classes at all, every class
    relabelled upstream, and a table of nothing but classes too small to have a verdict."""
    window = surfacecoverage.from_table_file(LA_WINDOW)
    relabelled = {"road_%s" % cls: row for cls, row in window.items()}
    tiny = {cls: {"known": 2, "unknown": 2, "unpaved": 0, "total": 4} for cls in surfacecoverage.BASELINES}
    for table in ({}, relabelled, tiny):
        assert surfacecoverage.main(["--table", _write(table, capsys)]) == 1
        assert "residential" in capsys.readouterr().err


def test_a_large_class_with_no_baseline_is_reported_by_name(capsys):
    table = surfacecoverage.from_table_file(LA_WINDOW)
    table["busway"] = {"known": 40, "unknown": 10, "unpaved": 0, "total": 50}
    assert surfacecoverage.main(["--table", _write(table, capsys)]) == 0
    assert "SURFACE UNKNOWN CLASS busway" in capsys.readouterr().err


def test_a_class_exactly_at_its_baseline_passes():
    """Ruling S4: the baseline is a floor, and a floor is an allowed value."""
    row = {"known": 91, "unknown": 909, "unpaved": 0, "total": 1000}
    assert surfacecoverage.known_fraction(row) == surfacecoverage.BASELINES["residential"]
    assert surfacecoverage.refusals({"residential": row}) == []


def test_a_class_one_way_below_its_baseline_is_refused():
    row = {"known": 90, "unknown": 910, "unpaved": 0, "total": 1000}
    assert [r.split(":")[0] for r in surfacecoverage.refusals({"residential": row})] == ["residential"]


def test_a_class_at_the_minimum_count_is_refused(capsys):
    at_floor = {"residential": {"known": 0, "unknown": surfacecoverage.MIN_CLASS_WAYS, "unpaved": 0,
                                "total": surfacecoverage.MIN_CLASS_WAYS}}
    assert [r.split(":")[0] for r in surfacecoverage.refusals(at_floor)] == ["residential"]


def test_a_class_with_no_baseline_is_never_refused_however_bare():
    assert surfacecoverage.refusals(
        {"living_street": {"known": 0, "unknown": 400, "unpaved": 0, "total": 400}}) == []


def test_the_encoded_value_is_stable_so_two_builds_agree_byte_for_byte():
    table = surfacecoverage.from_table_file(LA_WINDOW)
    assert surfacecoverage.encode(table) == surfacecoverage.encode(
        dict(reversed(list(table.items()))))


def test_decode_refuses_a_table_whose_buckets_do_not_add_up():
    with pytest.raises(ValueError):
        surfacecoverage.decode(json.dumps(
            {"residential": {"known": 1, "unknown": 1, "unpaved": 0, "total": 9}}))


def test_decode_refuses_a_row_missing_a_bucket():
    with pytest.raises(ValueError):
        surfacecoverage.decode(json.dumps({"residential": {"known": 1, "unknown": 0, "total": 1}}))


def test_a_corpus_without_the_key_is_a_refusal_not_an_empty_verdict(tmp_path):
    import sqlite3
    path = build(tmp_path)
    conn = sqlite3.connect(str(path))
    conn.execute("DELETE FROM meta WHERE key = ?", (surfacecoverage.META_KEY,))
    conn.commit()
    conn.close()
    with pytest.raises(ValueError):
        surfacecoverage.from_corpus(path)


# --- the --corpus form, over a corpus corpus.build really built (ruling S1) ------------------------------
# Ten (cls, highway) pairs: exactly the classes BASELINES names, which is what the whitelist requires of any
# table the check gives a verdict on. 25 ways each, the MIN_CLASS_WAYS floor.
BASELINED_CLASSES = (("motorway", "motorway"), ("motorway", "motorway_link"), ("primary", "primary"),
                     ("residential", "residential"), ("secondary", "secondary"), ("service", "service"),
                     ("tertiary", "tertiary"), ("track", "track"), ("trunk", "trunk"),
                     ("unclassified", "unclassified"))
ETL_DIR = FIXTURES.parent.parent


def _write_extract(path: pathlib.Path, residential_known: int) -> None:
    ways = []
    for index, (cls, highway) in enumerate(BASELINED_CLASSES):
        known = residential_known if highway == "residential" else 20
        for seq in range(surfacecoverage.MIN_CLASS_WAYS):
            lat = 34.0 + index * 0.01 + seq * 0.0002
            way = {"id": len(ways) + 1, "cls": cls, "highway": highway, "access_ok": 1, "oneway": 0,
                   "nodes": [[round(lat, 6), -118.0], [round(lat, 6), -117.998]]}
            if seq < known:
                way["surface"] = "asphalt"
            ways.append(way)
    path.write_text(json.dumps({"region": "fixture", "ways": ways}), encoding="utf-8", newline="\n")


def _built_corpus(tmp_path, name: str, residential_known: int) -> pathlib.Path:
    extract = tmp_path / ("%s.json" % name)
    _write_extract(extract, residential_known)
    out = tmp_path / ("%s.sqlite" % name)
    corpus.build(str(extract), str(out), BUILT_AT)
    return out


def _run_on_corpus(path: pathlib.Path):
    """The module as the pipeline runs it: a subprocess, so `__main__`'s sys.exit(main()) is covered too."""
    return subprocess.run([sys.executable, "-m", "etl.surfacecoverage", "--corpus", str(path)],
                          cwd=str(ETL_DIR), capture_output=True, text=True)


def test_the_corpus_form_refuses_a_built_corpus_whose_residential_coverage_collapsed(tmp_path):
    """RED BY NAME over the path a build actually runs (ruling S1): every other check test goes through
    --table, and `bad = refusals(table) if args.table else []` survived because of it."""
    done = _run_on_corpus(_built_corpus(tmp_path, "collapsed", residential_known=0))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "residential" in done.stderr
    assert "below the baseline" in done.stderr


def test_the_corpus_form_passes_a_built_corpus_whose_classes_are_all_covered(tmp_path):
    done = _run_on_corpus(_built_corpus(tmp_path, "healthy", residential_known=20))
    assert done.returncode == 0, done.stdout + done.stderr
    assert "refused=0" in done.stdout


_TMP = []


def _write(table: dict, capsys) -> str:
    """A table file beside pytest's tmp dir. Kept alive in _TMP so the path survives the call."""
    import tempfile
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8", newline="\n")
    handle.write(surfacecoverage.encode(table))
    handle.close()
    _TMP.append(handle.name)
    return handle.name

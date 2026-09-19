"""plan:283's "corpus <60 MB" as a literal the emitter itself enforces, and the defect it names.

THE DEFECT (T-0206). The M2 exit row has carried "corpus <60 MB" since the plan and nothing in this tree
ever weighed a corpus: T-0030's Log line 255 says "CORPUS SIZE IS UNMEASURED" in as many words. T-0206
measured it - 46,231 real LA ways (the canyon window plus both grid halves) build a 19,906,560 B corpus,
430.5890 B per way, which over the clip's 560,208 filtered ways extrapolates to 241,219,402 B, 3.834x the
budget - and the emitter still had no opinion about its own size. An emitter that cannot refuse its own
output leaves the ceiling to whoever notices the download, which on this project is the user.

WHY THE BUDGET IS A PARAMETER WITH A LITERAL DEFAULT (T-0206 ruling R6). The refusal has to be provable
without a 60 MiB fixture in git. Monkeypatching `corpus.CORPUS_BUDGET_BYTES` would prove it, but it binds
the test to a module attribute rather than to the shipping behaviour, and CLAUDE.md says a defect-named
test binds to the symbol production runs. So `build` and the CLI take `budget_bytes`, defaulting to the one
literal, the small committed fixture is refused under a small EXPLICIT budget through both entry points,
and `test_the_default_budget_is_exactly_60_mib` pins the default so that lowering it is red by name.

Both refusal tests run through a SHIPPING entry point: `corpus.build` (what `main` calls) and
`python -m etl.corpus` as a real subprocess (what a pipeline runs). No helper is called anywhere here.
"""
from __future__ import annotations

import inspect
import pathlib
import subprocess
import sys

import pytest

from etl import corpus

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
EXTRACT = FIXTURES / "corpus_extract.json"
ETL_ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILT_AT = "2026-09-18T00:00:00Z"

# The committed fixture is 7 ways / 79 segments and builds a corpus of a few tens of kB. A budget of one
# byte is refused by any corpus that exists at all, which is the point: the fixture is not padded, the
# budget is lowered, and the arithmetic under test is the same comparison either way.
TINY_BUDGET = 1

SIXTY_MIB = 60 * 1024 * 1024


def test_the_default_budget_is_exactly_60_mib():
    """plan:283's ceiling, as one literal. Red if anyone relaxes it to make a real build pass."""
    assert corpus.CORPUS_BUDGET_BYTES == SIXTY_MIB
    assert corpus.CORPUS_BUDGET_BYTES == 62914560
    default = inspect.signature(corpus.build).parameters["budget_bytes"].default
    assert default is corpus.CORPUS_BUDGET_BYTES


def test_build_refuses_a_corpus_over_the_budget_and_names_both_numbers(tmp_path):
    out = tmp_path / "over.sqlite"
    with pytest.raises(corpus.CorpusTooLargeError) as excinfo:
        corpus.build(EXTRACT, out, BUILT_AT, budget_bytes=TINY_BUDGET)
    message = str(excinfo.value)
    assert str(out.stat().st_size) in message
    assert str(TINY_BUDGET) in message


def test_the_refused_corpus_is_left_on_disk_for_inspection(tmp_path):
    """T-0206 ruling R4: the non-zero exit stops the pipeline, the bytes are what a human needs."""
    out = tmp_path / "over.sqlite"
    with pytest.raises(corpus.CorpusTooLargeError):
        corpus.build(EXTRACT, out, BUILT_AT, budget_bytes=TINY_BUDGET)
    assert out.exists()
    assert out.stat().st_size > TINY_BUDGET


def test_a_corpus_under_the_budget_is_built_and_reports_its_bytes(tmp_path):
    out = tmp_path / "under.sqlite"
    report = corpus.build(EXTRACT, out, BUILT_AT)
    assert report["bytes"] == out.stat().st_size
    assert report["bytes"] < corpus.CORPUS_BUDGET_BYTES
    assert report["budget_bytes"] == corpus.CORPUS_BUDGET_BYTES


def _run_cli(args):
    return subprocess.run([sys.executable, "-m", "etl.corpus", *args], cwd=str(ETL_ROOT),
                          capture_output=True, text=True)


def test_the_cli_exits_non_zero_over_the_budget(tmp_path):
    out = tmp_path / "cli-over.sqlite"
    done = _run_cli(["--input", str(EXTRACT), "--out", str(out), "--built-at", BUILT_AT,
                     "--budget-bytes", str(TINY_BUDGET)])
    # T-0206 R9: not `!= 0`. 2 is already --built-at's refusal, so a bare non-zero cannot tell a pipeline
    # "over budget" from "bad stamp"; R4 chose 3 for exactly that reason.
    assert done.returncode == corpus.BUDGET_EXIT, done.stdout
    assert corpus.BUDGET_EXIT == 3
    assert str(TINY_BUDGET) in done.stderr
    assert out.exists()


def test_the_cli_default_budget_is_the_literal_on_the_shipping_parser():
    """T-0206 R7 (i). `inspect.signature(build)` does NOT bind the CLI: argparse's own default is a second,
    independent place the ceiling is spelled, and a pipeline runs `python -m etl.corpus` with no flag. Read
    it back out of the shipping parser over an argv with the required arguments only."""
    parsed = corpus.parse_args(["--input", "x.json", "--out", "y.sqlite", "--built-at", BUILT_AT])
    assert parsed.budget_bytes is corpus.CORPUS_BUDGET_BYTES
    assert parsed.budget_bytes == SIXTY_MIB


def test_build_refuses_an_unlimited_budget(tmp_path):
    """T-0206 R7 (ii): `None` is not "unlimited". With this refusal a None default anywhere - argparse's or
    the signature's - makes the no-flag CLI run exit non-zero instead of shipping an unweighed corpus. The
    refusal happens before anything is written: nothing is built that nobody weighed."""
    out = tmp_path / "unlimited.sqlite"
    with pytest.raises(TypeError) as excinfo:
        corpus.build(EXTRACT, out, BUILT_AT, budget_bytes=None)
    assert "budget_bytes" in str(excinfo.value)
    assert not out.exists()


def _built_size(tmp_path, name="probe.sqlite"):
    out = tmp_path / name
    corpus.build(EXTRACT, out, BUILT_AT)
    return out.stat().st_size


def test_a_corpus_of_exactly_the_budget_is_refused(tmp_path):
    """T-0206 R8: plan:283 says "corpus <60 MB", strictly less, so the tie refuses."""
    size = _built_size(tmp_path)
    out = tmp_path / "tie.sqlite"
    with pytest.raises(corpus.CorpusTooLargeError):
        corpus.build(EXTRACT, out, BUILT_AT, budget_bytes=size)


def test_a_corpus_one_byte_over_the_budget_is_refused(tmp_path):
    size = _built_size(tmp_path)
    out = tmp_path / "over-by-one.sqlite"
    with pytest.raises(corpus.CorpusTooLargeError):
        corpus.build(EXTRACT, out, BUILT_AT, budget_bytes=size - 1)


def test_a_corpus_one_byte_under_the_budget_is_built(tmp_path):
    size = _built_size(tmp_path)
    out = tmp_path / "under-by-one.sqlite"
    report = corpus.build(EXTRACT, out, BUILT_AT, budget_bytes=size + 1)
    assert report["bytes"] == size
    assert report["budget_bytes"] == size + 1


def test_the_cli_refuses_one_byte_under_the_built_size(tmp_path):
    """The CLI half of R8's boundary, through the shipping subprocess and the shipping exit code."""
    size = _built_size(tmp_path)
    out = tmp_path / "cli-tie.sqlite"
    done = _run_cli(["--input", str(EXTRACT), "--out", str(out), "--built-at", BUILT_AT,
                     "--budget-bytes", str(size - 1)])
    assert done.returncode == corpus.BUDGET_EXIT, done.stdout
    assert str(size - 1) in done.stderr


def test_the_cli_builds_and_prints_the_bytes_under_the_default_budget(tmp_path):
    out = tmp_path / "cli-under.sqlite"
    done = _run_cli(["--input", str(EXTRACT), "--out", str(out), "--built-at", BUILT_AT])
    assert done.returncode == 0, done.stderr
    assert f"CORPUS bytes={out.stat().st_size} budget={SIXTY_MIB}" in done.stdout
    # The comparison actually ran against that printed budget: the default path both reports and passes.
    assert out.stat().st_size < SIXTY_MIB

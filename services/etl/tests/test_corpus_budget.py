"""plan:283's "corpus <60 MB" as a literal the emitter itself enforces, and the defect it names.

THE DEFECT (T-0206). The M2 exit row has carried "corpus <60 MB" since the plan and nothing in this tree
ever weighed a corpus: T-0030's Log line 255 says "CORPUS SIZE IS UNMEASURED" in as many words. T-0206
measured it - 46,231 real LA ways (the canyon window plus both grid halves) build a 19,906,560 B corpus,
430.59 B per way, which over the clip's 560,208 filtered ways extrapolates to 241,224,000 B, 3.83x the
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
    assert done.returncode != 0, done.stdout
    assert str(TINY_BUDGET) in done.stderr
    assert out.exists()


def test_the_cli_builds_and_prints_the_bytes_under_the_default_budget(tmp_path):
    out = tmp_path / "cli-under.sqlite"
    done = _run_cli(["--input", str(EXTRACT), "--out", str(out), "--built-at", BUILT_AT])
    assert done.returncode == 0, done.stderr
    assert f"CORPUS bytes={out.stat().st_size} budget={SIXTY_MIB}" in done.stdout

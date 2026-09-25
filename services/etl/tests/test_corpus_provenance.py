"""P-DATA-03's corpus half, in CI: the shipping provenance check still DECIDES region and freshness.

THE DEFECT (T-0197 rv1/rv2-pr119, filed as T-0219). `etl.corpus` stamps `meta.region` - corpus.py's
`region = region or extract_region` then `writer.set_meta("region", region)` - and nothing read it back
against the active region. A corpus cut for another region, or a year old, opens on the device as a complete
corpus: every table there, every index built, `build_complete` = 1.

WHAT THIS BINDS TO. `ops/lib/check-corpus-provenance.py`, run as a SUBPROCESS at its real path - the command
pins/PINS.yaml's P-DATA-03 assertion runs, and the one an operator runs over a built corpus with `--corpus`.
Not a helper, not a copy, not an importable shim: this file spells the shipping command and reads its exit
code, so deleting a limb from that checker turns these tests red rather than leaving them green over their own
table (CLAUDE.md: a test named for a defect binds to the shipping symbol).

WHY THE CORPORA ARE BUILT HERE AND NOT COMMITTED. `corpus.build` is the shipping builder and a committed
corpus would carry a frozen `built_at` that goes stale in thirty days, turning the age limb into a calendar.
Every corpus below comes out of the builder the pipeline runs.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import subprocess
import sys

from etl import corpus

ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECKER = ROOT / "ops/lib/check-corpus-provenance.py"
FIXTURES = pathlib.Path(__file__).parent / "fixtures"
EXTRACT = FIXTURES / "corpus_extract.json"

# Deliberately not "now": the age limb is what is under test, so the stamp is an argument here exactly as
# `--built-at` is an argument to the builder (corpus.py: "An INPUT: no clock is read").
def stamp(days_ago: float) -> str:
    moment = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=days_ago)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def corpus_region_id(name: str) -> str:
    path = ROOT / "services/etl/regions" / name / "region.json"
    return str(json.loads(path.read_text(encoding="utf-8"))["id"])


def run_checker(*args: str) -> subprocess.CompletedProcess:
    """The shipping command, at its real path, from the repo root."""
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True, cwd=str(ROOT))


def built(tmp_path, name: str, *, region: str, days_ago: float) -> pathlib.Path:
    out = tmp_path / name
    corpus.build(EXTRACT, out, stamp(days_ago), region=region)
    return out


def test_the_checker_is_committed_where_the_pin_names_it():
    """A missing checker must never read as a pass: P-DATA-03's assertion is this path."""
    assert CHECKER.is_file(), f"{CHECKER} is missing; P-DATA-03's corpus half has nothing to run"


def test_the_shipping_check_exits_zero_and_names_every_verdict():
    done = run_checker()
    assert done.returncode == 0, done.stdout + done.stderr
    for label in ("a fresh region-la corpus", "stamped 40 days ago", "stamped region 'bay'",
                  "no meta.region at all", "no meta.built_at at all", "stamped 2 days in the future"):
        assert label in done.stdout, done.stdout


def test_a_fresh_la_corpus_is_accepted(tmp_path):
    """First, because a checker that refuses everything decides nothing."""
    good = built(tmp_path, "fresh.sqlite", region="la", days_ago=0.001)
    done = run_checker("--corpus", str(good))
    assert done.returncode == 0, done.stdout + done.stderr
    assert "CORPUS OK" in done.stdout
    assert "region=la" in done.stdout


def test_a_corpus_stamped_for_another_region_is_refused(tmp_path):
    """The defect itself: a corpus the builder really built, stamped `bay`, offered as LA's."""
    wrong = built(tmp_path, "bay.sqlite", region="bay", days_ago=0.001)
    done = run_checker("--corpus", str(wrong))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "meta.region is 'bay'" in done.stdout


def test_a_corpus_older_than_thirty_days_is_refused(tmp_path):
    stale = built(tmp_path, "stale.sqlite", region="la", days_ago=40)
    done = run_checker("--corpus", str(stale))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "older than 30 days (P-DATA-03)" in done.stdout


def test_a_corpus_stamped_in_the_future_is_refused(tmp_path):
    """An age limb that only looks backwards passes a stamp from 2099 (the tiles half's rv1-pr109 R1)."""
    ahead = built(tmp_path, "ahead.sqlite", region="la", days_ago=-2)
    done = run_checker("--corpus", str(ahead))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "is in the future by more than" in done.stdout


def test_the_expected_region_is_read_from_region_json_and_never_typed(tmp_path):
    """`--region sfbay` must judge against sfbay's OWN id, so the same LA corpus is refused for it.

    If the expected value were a literal in the checker, this corpus would pass under both regions.
    """
    la_corpus = built(tmp_path, "la.sqlite", region="la", days_ago=0.001)
    expected = corpus_region_id("sfbay")
    done = run_checker("--corpus", str(la_corpus), "--region", "sfbay")
    assert done.returncode == 1, done.stdout + done.stderr
    assert f"meta.region is 'la', expected {expected!r}" in done.stdout


def test_a_corpus_that_is_not_a_corpus_is_refused(tmp_path):
    """"Could not look" must never read as "nothing wrong"."""
    junk = tmp_path / "junk.sqlite"
    junk.write_bytes(b"this is not a database")
    done = run_checker("--corpus", str(junk))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "not a corpus" in done.stdout


def test_the_prove_red_table_still_kills_every_mutant():
    """The check has been seen red, on every run, not once in a task log.

    Five defects are applied to a copy of the checker - the region comparison deleted, an absent region key
    defaulted to the expected value (T-0197 B4), the 30-day comparison flipped, an absent built_at treated as
    fresh, and the future-skew limb deleted - and each must be refused BY NAME.
    """
    done = run_checker("--prove-red")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "5/5 mutants refused by name" in done.stdout

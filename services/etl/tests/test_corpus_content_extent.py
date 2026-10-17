"""P-DATA-03's CORPUS half, content limb (T-0233): every bound, through the SHIPPED entry point.

The subject is `python ops/lib/check-corpus-provenance.py --corpus <file> [--region-json <file>]` in a
subprocess at its real path - the command P-DATA-03 and an operator run. Each row is a corpus the SHIPPING
corpus.build really built (the committed Marin extract translated into la, T-0233 R12), then one segment moved
to the bound under test and meta.bbox rewritten to the new extent, so the containment limb alone decides.

THE LIMITS are derived here, independently of the checker's constant: la's edges READ from region.json and
the ruled overhang (R1, 0.25 deg), in exact decimal e7 - so `exactly on the limit` is exact.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from etl import corpus

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "ops/lib/check-corpus-provenance.py"
EXTRACT = Path(__file__).parent / "fixtures/corpus_extract.json"
LA_JSON = ROOT / "services/etl/regions/la/region.json"
EDGES = ("min_lon", "min_lat", "max_lon", "max_lat")
OVERHANG = Decimal("0.25")
COLUMNS = ("min_lon_e7", "min_lat_e7", "max_lon_e7", "max_lat_e7")

sys.path.insert(0, str(ROOT / "ops/lib"))
from corpus_provenance_cases import stamp_days_ago, translated_extract  # noqa: E402


def limits_e7() -> list[int]:
    box = json.loads(LA_JSON.read_text(encoding="utf-8"))["bbox"]
    signs = (-1, -1, 1, 1)
    return [int((Decimal(str(box[k])) + s * OVERHANG) * 10 ** 7) for k, s in zip(EDGES, signs)]


@pytest.fixture(scope="module")
def la_corpus(tmp_path_factory) -> Path:
    tmp = tmp_path_factory.mktemp("la")
    out = tmp / "la.sqlite"
    corpus.build(translated_extract(EXTRACT, tmp / "la.json"), out, stamp_days_ago(0.001), region="la")
    return out


def run(path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CHECKER), "--corpus", str(path), *extra],
                          capture_output=True, text=True, cwd=str(ROOT))


def edited(src: Path, dst: Path, *statements: str) -> Path:
    """A copy of `src` with the statements run, then meta.bbox restamped to the segments' new extent."""
    shutil.copyfile(src, dst)
    conn = sqlite3.connect(str(dst))
    try:
        for statement in statements:
            conn.execute(statement)
        row = conn.execute("SELECT min(min_lon_e7), min(min_lat_e7), max(max_lon_e7), max(max_lat_e7) "
                           "FROM segments").fetchone()
        conn.execute("UPDATE meta SET value = ? WHERE key = 'bbox'", (",".join(str(v) for v in row),))
        conn.commit()
    finally:
        conn.close()
    return dst


def edge_rows() -> list[tuple]:
    """(id, edge index, offset in e7 units OUTWARD from the limit, refused?)."""
    rows = []
    for index, key in enumerate(EDGES):
        rows += [(f"{key} one e7 inside the limit", index, -1, False),
                 (f"{key} exactly on the limit", index, 0, False),
                 (f"{key} one e7 past the limit", index, 1, True)]
    return rows


@pytest.mark.parametrize("label,index,offset,refused", edge_rows(), ids=[r[0] for r in edge_rows()])
def test_every_edge_of_la_is_a_decided_bound(tmp_path, la_corpus, label, index, offset, refused):
    value = limits_e7()[index] + (-offset if index < 2 else offset)
    path = edited(la_corpus, tmp_path / "c.sqlite",
                  f"UPDATE segments SET {COLUMNS[index]} = {value} WHERE rowid = (SELECT min(rowid) FROM segments)")
    done = run(path)
    if refused:
        assert done.returncode == 1, done.stdout + done.stderr
        assert "lies outside region 'la'" in done.stdout, done.stdout
    else:
        assert done.returncode == 0, done.stdout + done.stderr
        assert "CORPUS OK" in done.stdout


def test_the_limits_the_checker_prints_are_the_ruled_ones(la_corpus):
    done = run(la_corpus)
    assert done.returncode == 0, done.stdout + done.stderr
    assert f"limits={','.join(str(v) for v in limits_e7())}" in done.stdout, done.stdout


def test_content_with_lat_and_lon_swapped_cannot_be_written(tmp_path, la_corpus):
    """Measured while writing this table: la's longitudes (-119..-117.85) are not latitudes, and the segments
    schema's CHECK constraint (min_lat_e7 BETWEEN -900000000 AND 900000000) refuses the swapped row, so a
    swapped corpus never reaches the checker. The constraint is the anchor; this row holds it."""
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        edited(la_corpus, tmp_path / "c.sqlite",
               "UPDATE segments SET min_lon_e7 = min_lat_e7, min_lat_e7 = min_lon_e7, "
               "max_lon_e7 = max_lat_e7, max_lat_e7 = max_lon_e7")


def test_a_marin_corpus_stamped_la_is_refused_by_name(tmp_path):
    """The defect itself, as filed: the shipping builder's own output, stamped la, content in Marin."""
    out = tmp_path / "marin.sqlite"
    corpus.build(EXTRACT, out, stamp_days_ago(0.001), region="la")
    done = run(out)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "lies outside region 'la'" in done.stdout, done.stdout


def region_variant(tmp_path: Path, **bbox) -> Path:
    doc = json.loads(LA_JSON.read_text(encoding="utf-8"))
    doc["bbox"].update(bbox)
    out = tmp_path / "region.json"
    out.write_text(json.dumps(doc), encoding="utf-8")
    return out


@pytest.mark.parametrize("key", EDGES)
def test_a_nan_region_edge_is_refused_by_name(tmp_path, la_corpus, key):
    done = run(la_corpus, "--region-json", str(region_variant(tmp_path, **{key: float("nan")})))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "is not a finite min < max box" in done.stdout, done.stdout


@pytest.mark.parametrize("swap", [("min_lon", "max_lon"), ("min_lat", "max_lat")])
def test_a_region_with_min_and_max_swapped_is_refused_by_name(tmp_path, la_corpus, swap):
    box = json.loads(LA_JSON.read_text(encoding="utf-8"))["bbox"]
    done = run(la_corpus, "--region-json",
               str(region_variant(tmp_path, **{swap[0]: box[swap[1]], swap[1]: box[swap[0]]})))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "is not a finite min < max box" in done.stdout, done.stdout


def test_a_region_with_lat_and_lon_swapped_refuses_la_content(tmp_path, la_corpus):
    box = json.loads(LA_JSON.read_text(encoding="utf-8"))["bbox"]
    swapped = region_variant(tmp_path, min_lon=box["min_lat"], min_lat=box["min_lon"],
                             max_lon=box["max_lat"], max_lat=box["max_lon"])
    done = run(la_corpus, "--region-json", str(swapped))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "lies outside region 'la'" in done.stdout, done.stdout

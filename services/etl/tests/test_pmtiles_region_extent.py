"""P-DATA-03's TILES half, content limb (T-0233): every bound, through the SHIPPED command.

The subject is `python services/tiles/check_pmtiles.py <archive> --region-json <file>` - what build-la.sh step 6
and ops/publish-tiles run - in a subprocess at its real path. It lives here and not in services/tiles/tests
because that suite runs in neither ops/test nor CI (T-0233 R8); this one runs in both.

THE LIMITS are derived here, independently of the checker's constant: la's edges READ from region.json and
the ruled overhang (R2) - one z14 tile, 360 / 2**14 degrees, in e7 - recomputed. Each edge is tabled
outward at the overhang exactly (accepted), one e7 unit inside it (accepted) and one past it (refused naming
`extend past the region bbox`), and inward one e7 unit past la's own edge (refused naming `do not cover`).
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "services/tiles/check_pmtiles.py"
HARNESS = ROOT / "ops/lib/check-pmtiles-provenance.py"
LA_JSON = ROOT / "services/etl/regions/la/region.json"
EDGES = ("min_lon", "min_lat", "max_lon", "max_lat")
OVERHANG_E7 = round(360 / 2 ** 14 * 10 ** 7)

sys.path.insert(0, str(ROOT / "services/tiles"))
sys.path.insert(0, str(ROOT / "services/tiles/tests"))
from test_pmtiles_budget import good_metadata, write_pmtiles  # noqa: E402


def la_e7() -> list[int]:
    box = json.loads(LA_JSON.read_text(encoding="utf-8"))["bbox"]
    return [int(Decimal(str(box[key])) * 10 ** 7) for key in EDGES]


def fresh_meta() -> dict:
    stamp = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return good_metadata(built_at=stamp)


def run(archive: Path, region_json: Path = LA_JSON) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CHECKER), str(archive), "--region-json", str(region_json)],
                          capture_output=True, text=True, cwd=str(ROOT))


def archive_with(tmp_path: Path, e7: list[int]) -> Path:
    return write_pmtiles(tmp_path / "a.pmtiles", tuple(v / 1e7 for v in e7), fresh_meta())


def edge_rows() -> list[tuple]:
    """(id, edge index, offset in e7 units OUTWARD from la's edge, the name it must carry or None)."""
    rows = []
    for index, key in enumerate(EDGES):
        rows += [(f"{key} outward by the overhang exactly", index, OVERHANG_E7, None),
                 (f"{key} outward one e7 inside the overhang", index, OVERHANG_E7 - 1, None),
                 (f"{key} outward one e7 past the overhang", index, OVERHANG_E7 + 1, "extend past the region bbox"),
                 (f"{key} exactly on la's edge", index, 0, None),
                 (f"{key} one e7 inward of la's edge", index, -1, "do not cover the region bbox")]
    return rows


def test_the_ruled_overhang_is_one_z14_tile():
    assert OVERHANG_E7 == 219727
    assert math.isclose(OVERHANG_E7 / 1e7, 0.02197265625, abs_tol=1e-7)


@pytest.mark.parametrize("label,index,offset,want", edge_rows(), ids=[r[0] for r in edge_rows()])
def test_every_edge_of_la_is_a_decided_bound(tmp_path, label, index, offset, want):
    e7 = la_e7()
    e7[index] += -offset if index < 2 else offset
    done = run(archive_with(tmp_path, e7))
    if want is None:
        assert done.returncode == 0, done.stdout + done.stderr
        assert "PMTILES OK" in done.stdout
    else:
        assert done.returncode == 1, done.stdout + done.stderr
        assert want in done.stdout, done.stdout


def test_bounds_with_lat_and_lon_swapped_are_refused(tmp_path):
    lon0, lat0, lon1, lat1 = la_e7()
    done = run(archive_with(tmp_path, [lat0, lon0, lat1, lon1]))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "extend past the region bbox" in done.stdout or "do not cover the region bbox" in done.stdout


def region_variant(tmp_path: Path, **bbox) -> Path:
    doc = json.loads(LA_JSON.read_text(encoding="utf-8"))
    doc["bbox"].update(bbox)
    out = tmp_path / "region.json"
    out.write_text(json.dumps(doc), encoding="utf-8")
    return out


@pytest.mark.parametrize("key", EDGES)
def test_a_nan_region_edge_is_refused_by_name(tmp_path, key):
    """Every comparison against NaN is False: before T-0233 this archive was PMTILES OK."""
    done = run(archive_with(tmp_path, la_e7()), region_variant(tmp_path, **{key: float("nan")}))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "is not a finite min < max box" in done.stdout, done.stdout


@pytest.mark.parametrize("swap", [("min_lon", "max_lon"), ("min_lat", "max_lat")])
def test_a_region_with_min_and_max_swapped_is_refused_by_name(tmp_path, swap):
    box = json.loads(LA_JSON.read_text(encoding="utf-8"))["bbox"]
    done = run(archive_with(tmp_path, la_e7()),
               region_variant(tmp_path, **{swap[0]: box[swap[1]], swap[1]: box[swap[0]]}))
    assert done.returncode == 1, done.stdout + done.stderr
    assert "is not a finite min < max box" in done.stdout, done.stdout


def test_a_region_with_lat_and_lon_swapped_refuses_la_bounds(tmp_path):
    box = json.loads(LA_JSON.read_text(encoding="utf-8"))["bbox"]
    swapped = region_variant(tmp_path, min_lon=box["min_lat"], min_lat=box["min_lon"],
                             max_lon=box["max_lat"], max_lat=box["max_lon"])
    done = run(archive_with(tmp_path, la_e7()), swapped)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "extend past the region bbox" in done.stdout or "do not cover the region bbox" in done.stdout


def test_the_pin_harness_names_every_bounds_verdict():
    done = subprocess.run([sys.executable, str(HARNESS)], capture_output=True, text=True, cwd=str(ROOT))
    assert done.returncode == 0, done.stdout + done.stderr
    for label in ("Bay Area bounds stamped la", "California-wide bounds stamped la",
                  "bounds short of la's east edge"):
        assert label in done.stdout, done.stdout


def test_the_tiles_prove_red_table_kills_every_mutant():
    done = subprocess.run([sys.executable, str(HARNESS), "--prove-red"], capture_output=True, text=True,
                          cwd=str(ROOT))
    assert done.returncode == 0, done.stdout + done.stderr
    assert "--prove-red 6/6 mutants refused by name" in done.stdout

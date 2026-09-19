"""The COMMAND the recipe and the publish script run, end to end - not the function behind it.

`build-la.sh` step 6 and `ops/publish-tiles` both invoke `check_pmtiles.py <archive> --region-json <file>`
and believe its exit code. Nothing exercised that path: `test_the_bbox_is_read_from_the_region_file_not_typed`
calls `bbox_from_region` directly, so replacing `bbox_from_region(args.region_json)` in `main()` with the LA
box as a literal left the whole suite green while the checker stopped reading the region file at all - and a
region file is the one place the bbox is argued, so a corrected box (T-0142's shape) would be silently
ignored and a tile set cut to the stale box would pass the publish gate (rv1-pr109 B1).

Every case below runs the shipped file in a subprocess and asserts on its stdout and its exit code.
SUBJECTS: the in-process fixture always, and the real build when `$SCENIC_LA_PMTILES` names it. Nothing here
skips - no `pytest.skip`, no `skipif`. When that variable is set and the file is not there, this FAILS.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_pmtiles_budget import LA_BBOX, good_metadata, write_pmtiles  # noqa: E402

TILES = Path(__file__).resolve().parents[1]
CHECKER = TILES / "check_pmtiles.py"
REGION_JSON = TILES.parents[1] / "services/etl/regions/la/region.json"
ARCHIVE_ENV = "SCENIC_LA_PMTILES"


def run_checker(archive: Path, region_json: Path) -> tuple[int, str]:
    """The command, as the recipe spells it. Returns (exit code, everything it printed)."""
    proc = subprocess.run(
        [sys.executable, str(CHECKER), str(archive), "--region-json", str(region_json)],
        capture_output=True, text=True, cwd=str(TILES.parents[1]),
    )
    return proc.returncode, proc.stdout + proc.stderr


def region_file(tmp_path: Path, name: str = "region.json", **bbox: float) -> Path:
    """The real region file with its bbox edited - the shape of a bbox correction landing in the tree."""
    doc = json.loads(REGION_JSON.read_text(encoding="utf-8"))
    doc["bbox"].update(bbox)
    out = tmp_path / name
    out.write_text(json.dumps(doc), encoding="utf-8")
    return out


def subjects(tmp_path: Path) -> list[tuple[str, Path]]:
    fresh = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = [("fixture", write_pmtiles(tmp_path / "la.pmtiles", LA_BBOX, good_metadata(built_at=fresh)))]
    named = os.environ.get(ARCHIVE_ENV)
    if named:
        real = Path(named)
        assert real.is_file(), f"{ARCHIVE_ENV}={named} names no file"
        found.append((real.name, real))
    return found


def test_the_cli_reads_the_bbox_from_the_region_file_it_is_given(tmp_path: Path) -> None:
    """The same archive, two region files: accepted against the committed bbox, refused against a wider one.

    A checker carrying the box as a literal cannot tell them apart, which is the defect. The refusal has to
    NAME the box it was given, so the numbers in the message come from the file and not from the module.
    """
    wider = region_file(tmp_path, "wider.json", max_lon=-117.5)
    for subject, archive in subjects(tmp_path):
        code, out = run_checker(archive, REGION_JSON)
        assert code == 0, f"{subject}: {out}"
        assert "PMTILES OK" in out, f"{subject}: {out}"

        code, out = run_checker(archive, wider)
        assert code == 1, f"{subject}: {out}"
        assert "PMTILES REFUSED" in out, f"{subject}: {out}"
        assert "do not cover the region bbox (-119.0,33.7,-117.5,34.45)" in out, f"{subject}: {out}"


def test_the_cli_reads_the_region_id_from_the_region_file_too(tmp_path: Path) -> None:
    """`meta.region` is compared against the id in the file, not against a literal `la` in the checker."""
    doc = json.loads(REGION_JSON.read_text(encoding="utf-8"))
    doc["id"] = "sfbay"
    renamed = tmp_path / "sfbay.json"
    renamed.write_text(json.dumps(doc), encoding="utf-8")
    for subject, archive in subjects(tmp_path):
        code, out = run_checker(archive, renamed)
        assert code == 1, f"{subject}: {out}"
        assert "meta.region is 'la', expected 'sfbay'" in out, f"{subject}: {out}"


def test_the_cli_refuses_a_bad_archive_with_exit_one(tmp_path: Path) -> None:
    """The exit code is the whole interface: step 6 runs under `set -e` and publish-tiles believes it."""
    stub = write_pmtiles(tmp_path / "stub.pmtiles", LA_BBOX, good_metadata(), padding=0, entries=3)
    code, out = run_checker(stub, REGION_JSON)
    assert code == 1, out
    assert "PMTILES REFUSED" in out and "truncated" in out, out

"""The tiles OTA manifest writer (T-0345), driven through main() over archives written by the tests' own writer.

The written manifest is compared by FULL equality against a recomputation that does not call the module's own
helpers (hashlib over the bytes, the stamp re-formatted by hand), so a writer that drops, renames or re-derives a
field fails here. Every refusal is asserted by name AND by the absence of the output file. The last test hands the
writer's output to the SHIPPED `ops/lib/sane_prod.py tiles`, over this checkout's real region.json and
BasemapResolver.swift: the writer and ops/sane --prod exit 8 must agree on what a good manifest is.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tiles_manifest  # noqa: E402
from test_pmtiles_budget import LA_BBOX, good_metadata, write_pmtiles  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
REGION_JSON = ROOT / "services/etl/regions/la/region.json"
RESOLVER = ROOT / "apps/ios/Packages/ScenicApp/Sources/MapAdapter/BasemapResolver.swift"
NOW = datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc)
BUILT_AT = "2026-10-08T07:30:15Z"


def archive(tmp_path: Path, name: str = "la.pmtiles", **meta: object) -> Path:
    return write_pmtiles(tmp_path / name, LA_BBOX, good_metadata(**{"built_at": BUILT_AT, **meta}))


def run(path: Path, out: Path, min_app_build: str = "7", now: datetime = NOW) -> int:
    argv = ["--archive", str(path), "--region-json", str(REGION_JSON), "--min-app-build", min_app_build,
            "--out", str(out)]
    return tiles_manifest.main(argv, now=now)


def test_the_manifest_is_the_archive_measured_whole(tmp_path: Path) -> None:
    path = archive(tmp_path, maxzoom=15)
    out = tmp_path / "manifest.json"
    assert run(path, out) == 0
    data = path.read_bytes()
    assert json.loads(out.read_text(encoding="utf-8")) == {
        "version": "20261008T073015Z", "region": "la", "file": "la.pmtiles", "built_at": BUILT_AT,
        "maxzoom": 15, "min_app_build": 7, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
    }


def test_the_default_output_sits_beside_the_archive(tmp_path: Path) -> None:
    path = archive(tmp_path)
    argv = ["--archive", str(path), "--region-json", str(REGION_JSON), "--min-app-build", "1"]
    assert tiles_manifest.main(argv, now=NOW) == 0
    assert (tmp_path / "la.pmtiles.manifest.json").is_file()


@pytest.mark.parametrize("name,meta,min_build,now,needle", [
    ("la.pmtiles", {"region": "bay"}, "1", NOW, "region is 'bay'"),
    ("sfbay.pmtiles", {}, "1", NOW, "file is 'sfbay.pmtiles'"),
    ("la.pmtiles", {}, "0", NOW, "min_app_build is 0"),
    ("la.pmtiles", {}, "1", NOW + timedelta(days=31), "older than 30 days"),
    ("la.pmtiles", {}, "1", NOW - timedelta(days=2), "ahead of now"),
    ("la.pmtiles", {"maxzoom": 13}, "1", NOW, "maxzoom is 13"),
    ("la.pmtiles", {"maxzoom": 16}, "1", NOW, "maxzoom is 16"),
    ("la.pmtiles", {"built_at": "2026-10-08 07:30:15"}, "1", NOW, "built_at is '2026-10-08 07:30:15'"),
])
def test_the_writer_refuses_and_writes_nothing(tmp_path: Path, capsys, name, meta, min_build, now, needle) -> None:
    path = archive(tmp_path, name=name, **meta)
    out = tmp_path / "manifest.json"
    assert run(path, out, min_app_build=min_build, now=now) == 1
    assert needle in capsys.readouterr().out
    assert not out.exists()


def test_the_writer_refuses_an_archive_over_the_budget(tmp_path: Path, capsys) -> None:
    path = archive(tmp_path)
    with path.open("ab") as handle:
        handle.truncate(125_829_121)
    out = tmp_path / "manifest.json"
    assert run(path, out) == 1
    assert "bytes is 125829121" in capsys.readouterr().out
    assert not out.exists()


def test_ops_sane_accepts_what_the_writer_writes(tmp_path: Path) -> None:
    fresh = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = write_pmtiles(tmp_path / "la.pmtiles", LA_BBOX, good_metadata(built_at=fresh))
    out = tmp_path / "manifest.json"
    assert tiles_manifest.main(["--archive", str(path), "--region-json", str(REGION_JSON),
                                "--min-app-build", "1", "--out", str(out)]) == 0
    p = subprocess.run([sys.executable, str(ROOT / "ops/lib/sane_prod.py"), "tiles", str(REGION_JSON),
                        str(RESOLVER)], input=out.read_text(encoding="utf-8"), capture_output=True, text=True)
    assert (p.returncode, p.stdout.split(" region ")[0]) == (0, f"tiles {fresh[:10].replace('-', '')}T"
                                                             f"{fresh[11:19].replace(':', '')}Z"), p.stdout

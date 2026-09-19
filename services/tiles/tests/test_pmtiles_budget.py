"""The PMTiles artifact check, over fixtures built here rather than downloaded.

A 127-byte v3 header is a fixed record, so a wrong-bounds archive can be CONSTRUCTED - which is the only
way this check gets seen red without a bad 60 MB file to hand. `check_pmtiles.parse_header` is the same
parser the build recipe runs, and T-0165's Log quotes it agreeing field for field with
`pmtiles show --header-json` on the real LA build.
"""

from __future__ import annotations

import gzip
import json
import struct
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_pmtiles import BUDGET_BYTES, bbox_from_region, check, parse_header, read_metadata  # noqa: E402

LA_BBOX = (-119.0, 33.7, -117.85, 34.45)
NOW = datetime(2026, 9, 19, 5, 0, tzinfo=timezone.utc)


def write_pmtiles(path: Path, bounds: tuple[float, float, float, float], metadata: dict,
                  *, padding: int = 0, version: int = 3) -> Path:
    """A minimal but structurally real PMTiles v3 archive: header, gzip metadata, then filler tile data."""
    blob = gzip.compress(json.dumps(metadata).encode("utf-8"))
    meta_offset = 127
    data_offset = meta_offset + len(blob)
    header = bytearray(b"PMTiles" + bytes([version]))
    header += struct.pack(
        "<11Q",
        data_offset, 0,             # root directory offset, length
        meta_offset, len(blob),     # json metadata offset, length
        0, 0,                       # leaf directories offset, length
        data_offset, padding,       # tile data offset, length
        1, 1, 1,                    # addressed, entries, contents
    )
    header += struct.pack("<6B", 1, 2, 2, 1, 0, 14)  # clustered, gzip, gzip, mvt, minzoom, maxzoom
    header += struct.pack("<4i", *(round(v * 1e7) for v in bounds))
    header += struct.pack("<B2i", 0, round((bounds[0] + bounds[2]) / 2 * 1e7),
                          round((bounds[1] + bounds[3]) / 2 * 1e7))
    assert len(header) == 127
    path.write_bytes(bytes(header) + blob + b"\0" * padding)
    return path


def good_metadata(**overrides) -> dict:
    meta = {"region": "la", "built_at": "2026-09-19T05:02:38Z", "bbox": "-119.0,33.7,-117.85,34.45",
            "maxzoom": 14, "vector_layers": [{"id": "roads"}]}
    meta.update(overrides)
    return meta


@pytest.fixture()
def good(tmp_path: Path) -> Path:
    return write_pmtiles(tmp_path / "good.pmtiles", LA_BBOX, good_metadata())


def test_header_round_trips(good: Path) -> None:
    header = parse_header(good)
    assert (header["min_lon"], header["min_lat"], header["max_lon"], header["max_lat"]) == LA_BBOX
    assert (header["min_zoom"], header["max_zoom"], header["spec_version"]) == (0, 14, 3)
    assert read_metadata(good)["region"] == "la"


def test_a_covering_archive_passes(good: Path) -> None:
    assert check(good, LA_BBOX, region="la", now=NOW) == []


def test_refuses_bounds_that_do_not_cover_the_region(tmp_path: Path) -> None:
    """The failure this check exists for: an extract cut to the wrong box still looks like a basemap."""
    # East to -118.0 instead of -117.85: Angeles Crest and the whole San Gabriel front are simply absent.
    short = write_pmtiles(tmp_path / "short.pmtiles", (-119.0, 33.7, -118.0, 34.45), good_metadata())
    failures = check(short, LA_BBOX, region="la", now=NOW)
    assert len(failures) == 1
    assert "do not cover the region bbox" in failures[0]


def test_refuses_bounds_short_on_every_edge(tmp_path: Path) -> None:
    for i, bounds in enumerate([(-118.9, 33.7, -117.85, 34.45), (-119.0, 33.8, -117.85, 34.45),
                                (-119.0, 33.7, -118.9, 34.45), (-119.0, 33.7, -117.85, 34.4)]):
        clipped = write_pmtiles(tmp_path / f"clipped{i}.pmtiles", bounds, good_metadata())
        assert any("do not cover" in f for f in check(clipped, LA_BBOX, region="la", now=NOW)), bounds


def test_a_wider_archive_is_fine(tmp_path: Path) -> None:
    """Cover, not equal - an extract's bounds snap out to whole tiles, so they are never exactly the bbox."""
    wide = write_pmtiles(tmp_path / "wide.pmtiles", (-119.5, 33.5, -117.5, 34.6), good_metadata())
    assert check(wide, LA_BBOX, region="la", now=NOW) == []


def test_refuses_over_the_120_mb_budget(good: Path) -> None:
    failures = check(good, LA_BBOX, region="la", budget=good.stat().st_size - 1, now=NOW)
    assert len(failures) == 1
    assert "exceeds" in failures[0] and "1" in failures[0]


def test_the_budget_is_120_mib() -> None:
    assert BUDGET_BYTES == 120 * 1024 * 1024


def test_refuses_the_wrong_region(tmp_path: Path) -> None:
    other = write_pmtiles(tmp_path / "sfbay.pmtiles", LA_BBOX, good_metadata(region="sfbay"))
    assert any("meta.region" in f for f in check(other, LA_BBOX, region="la", now=NOW))


def test_refuses_a_stale_build(tmp_path: Path) -> None:
    stale = (NOW - timedelta(days=31)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old = write_pmtiles(tmp_path / "old.pmtiles", LA_BBOX, good_metadata(built_at=stale))
    assert any("older than 30 days" in f for f in check(old, LA_BBOX, region="la", now=NOW))


def test_refuses_a_missing_built_at(tmp_path: Path) -> None:
    meta = good_metadata()
    del meta["built_at"]
    nostamp = write_pmtiles(tmp_path / "nostamp.pmtiles", LA_BBOX, meta)
    assert any("built_at is missing" in f for f in check(nostamp, LA_BBOX, region="la", now=NOW))


def test_refuses_something_that_is_not_pmtiles(tmp_path: Path) -> None:
    junk = tmp_path / "junk.pmtiles"
    junk.write_bytes(b"not a pmtiles archive, but long enough to be one" * 8)
    assert check(junk, LA_BBOX, region="la", now=NOW) == ["not a PMTiles v3 archive: "
                                                          "junk.pmtiles does not start with the PMTiles magic"]


def test_refuses_a_v4_archive(tmp_path: Path) -> None:
    future = write_pmtiles(tmp_path / "v4.pmtiles", LA_BBOX, good_metadata(), version=4)
    assert any("spec version 4" in f for f in check(future, LA_BBOX, region="la", now=NOW))


def test_the_bbox_is_read_from_the_region_file_not_typed() -> None:
    region = Path(__file__).resolve().parents[3] / "services/etl/regions/la/region.json"
    assert bbox_from_region(region) == LA_BBOX

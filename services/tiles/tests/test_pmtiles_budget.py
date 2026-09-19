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

from check_pmtiles import (  # noqa: E402
    BUDGET_BYTES, MAX_FUTURE_SKEW, MIN_BYTES, MIN_MAXZOOM, MIN_TILE_ENTRIES,
    bbox_from_region, check, parse_header, read_metadata,
)

LA_BBOX = (-119.0, 33.7, -117.85, 34.45)
NOW = datetime(2026, 9, 19, 5, 0, tzinfo=timezone.utc)


def write_pmtiles(path: Path, bounds: tuple[float, float, float, float], metadata: dict,
                  *, padding: int = MIN_BYTES, version: int = 3, maxzoom: int = 14,
                  entries: int = MIN_TILE_ENTRIES) -> Path:
    """A minimal but structurally real PMTiles v3 archive: header, gzip metadata, then filler tile data.

    The two defaults sit ON the floors `check` now carries, so a fixture written for some other limb is not
    silently refused by the size or entry floor and every test below keeps the subject it was written for.
    """
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
        entries, entries, entries,  # addressed, entries, contents
    )
    header += struct.pack("<6B", 1, 2, 2, 1, 0, maxzoom)  # clustered, gzip, gzip, mvt, minzoom, maxzoom
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


def test_refuses_an_archive_coarser_than_the_ruled_maxzoom(tmp_path: Path) -> None:
    """R3 ruled z14 BY MEASUREMENT. Every zoom below it is a smaller file, so the budget limb is blind to
    this one from the other side: `build-la.sh --maxzoom 12` writes a ~20 MB archive that fits the ceiling
    and hands the driver a map that goes soft two zoom levels early."""
    coarse = write_pmtiles(tmp_path / "z10.pmtiles", LA_BBOX, good_metadata(maxzoom=10), maxzoom=10)
    failures = check(coarse, LA_BBOX, region="la", now=NOW)
    assert any("max_zoom 10 is below the required 14" in f for f in failures), failures
    # Lowering the floor is a decision a caller has to state, not a default it can drift into.
    assert check(coarse, LA_BBOX, region="la", min_maxzoom=10, now=NOW) == []


def test_the_zoom_floor_is_the_zoom_r3_ruled() -> None:
    assert MIN_MAXZOOM == 14


def test_refuses_a_header_and_metadata_that_disagree_about_maxzoom(tmp_path: Path) -> None:
    """Written by two different steps - the header by `pmtiles extract`, the metadata by the recipe's own
    stamp - so they disagree exactly when a rebuild changed one and not the other."""
    split = write_pmtiles(tmp_path / "split.pmtiles", LA_BBOX, good_metadata(maxzoom=10), maxzoom=14)
    assert any("meta.maxzoom 10 disagrees with the header's max_zoom 14" in f
               for f in check(split, LA_BBOX, region="la", now=NOW))


def test_refuses_a_missing_meta_maxzoom(tmp_path: Path) -> None:
    meta = good_metadata()
    del meta["maxzoom"]
    nozoom = write_pmtiles(tmp_path / "nozoom.pmtiles", LA_BBOX, meta)
    assert any("meta.maxzoom is missing" in f for f in check(nozoom, LA_BBOX, region="la", now=NOW))


def test_refuses_an_archive_with_no_tiles_in_it(tmp_path: Path) -> None:
    """In bounds, inside the budget, correctly stamped - and it draws nothing at all."""
    empty = write_pmtiles(tmp_path / "empty.pmtiles", LA_BBOX, good_metadata(), entries=0)
    assert any("carries no tiles" in f for f in check(empty, LA_BBOX, region="la", now=NOW))


def test_the_build_recipe_reads_the_budget_out_of_this_module() -> None:
    """One definition of the ceiling. Step 3 and step 6 must refuse the same file, and a second copy of the
    number in the shell is a copy that drifts the day the ceiling moves."""
    recipe = (Path(__file__).resolve().parents[1] / "build-la.sh").read_text(encoding="utf-8")
    assert str(BUDGET_BYTES) not in recipe, "build-la.sh carries its own copy of the budget literal"
    assert "check_pmtiles.BUDGET_BYTES" in recipe


def test_the_bbox_is_read_from_the_region_file_not_typed() -> None:
    region = Path(__file__).resolve().parents[3] / "services/etl/regions/la/region.json"
    assert bbox_from_region(region) == LA_BBOX


# rv1-pr109 R1 and R2: two limbs that could not fail. The age limb only looked backwards, and the tile limb
# was `== 0`, so a stamp from 2099 and a 330-byte stub with three entries in it were both publishable.


@pytest.mark.parametrize("stamp", ["2099-01-01T00:00:00Z", "2099-01-01T00:00:00"])
def test_refuses_a_build_stamped_in_the_future(tmp_path: Path, stamp: str) -> None:
    """Both spellings: the recipe writes the Z, and a stamp typed without an offset is UTC here too - which
    used to raise on the comparison instead of refusing, and a traceback is not a refusal."""
    ahead = write_pmtiles(tmp_path / "ahead.pmtiles", LA_BBOX, good_metadata(built_at=stamp))
    failures = check(ahead, LA_BBOX, region="la", now=NOW)
    assert any("is in the future" in f for f in failures), failures


def test_a_stamp_a_few_minutes_ahead_is_inside_the_skew_tolerance(tmp_path: Path) -> None:
    """Two hosts whose clocks differ by seconds must not fail the build; that is what the tolerance is for."""
    soon = (NOW + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    fresh = write_pmtiles(tmp_path / "soon.pmtiles", LA_BBOX, good_metadata(built_at=soon))
    assert check(fresh, LA_BBOX, region="la", now=NOW) == []


def test_the_future_skew_tolerance_is_the_one_hour_ruled() -> None:
    assert MAX_FUTURE_SKEW == timedelta(hours=1)


def test_refuses_a_truncated_archive(tmp_path: Path) -> None:
    """In bounds, correctly stamped, z14 in both places, three entries - and 330 bytes of it. Before the
    floors this returned no failures at all, so a half-written extract published as a basemap."""
    stub = write_pmtiles(tmp_path / "stub.pmtiles", LA_BBOX, good_metadata(), padding=0, entries=3)
    assert stub.stat().st_size < 1000, stub.stat().st_size
    failures = check(stub, LA_BBOX, region="la", now=NOW)
    assert any(f"tile_entries_count 3 is below the floor of {MIN_TILE_ENTRIES}" in f for f in failures), failures
    assert any(f"is below the {MIN_BYTES}-byte floor" in f for f in failures), failures


def test_the_floors_are_the_ones_ruled_off_the_measured_build() -> None:
    """2549 entries and 63,520,949 bytes were measured; the floors are stated, not derived at runtime."""
    assert MIN_TILE_ENTRIES == 256
    assert MIN_BYTES == 1024 * 1024

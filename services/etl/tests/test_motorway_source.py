"""T-0208 R1b: the motorway set a way's proximity is measured to is a REGION fact, not a CLIP fact.

WHY THIS TEST EXISTS, from a measurement and not from a worry. Over T-0204's two real docs
(`grid-a-doc.json`, `grid-b-doc.json`) the 190 ways that `osmium extract` completed into BOTH clips carry
byte-identical rows only 92 times. The single field that ever differs is `meters_to_nearest_motorway`, on 98
of the 190, and 15 of those cross `score.score`'s 150 m threshold - so the same road takes the x0.7 freeway
multiplier in one window and not in the other. Ranking against one region-wide reference cannot repair that:
it is the same defect one layer down, a per-way term computed against whatever landed in the window.

So `waydoc.build` takes the motorway geometry from a file of its own when one is given. The default is
unchanged - the clip's own ways - because every other caller and every other test measures a self-contained
fixture, and a required argument would be a migration this task does not need.

THE SHIPPING SYMBOL is `waydoc.main`: the region build's first pass ran `python -m etl.waydoc ...
--motorways work/la-motorways.osm.xml`, and a test that stopped at `build` stayed green while `main` dropped
the flag (rv1-t0208 B2). The two CLI tests below bind both of the flag's paths through `main` itself.
"""
from __future__ import annotations

import json
import pathlib

from etl import score, waydoc

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
CLIP = FIXTURES / "scenic_clip.osm.xml"
REGION_MOTORWAYS = FIXTURES / "region_motorways.osm.xml"

# Way 101 shares node 14 with the clip's own motorway 102, so the clip's answer for it is exactly 0.0.
CANYON_WAY = 101
# The region file has its motorway ~390 m off way 101 - past the 150 m threshold, inside the 1 km horizon.
NEAR_HORIZON_M = 1000.0


def elevation(points: list) -> list:
    return [100.0 + index * 1.0 for index, _point in enumerate(points)]


def landcover(points: list) -> list:
    return [10] * len(points)


def build(**over) -> dict:
    kwargs = {"region_id": "la", "elevation": elevation, "landcover": landcover}
    kwargs.update(over)
    return waydoc.build(CLIP, **kwargs)


def distance_of(document: dict, way_id: int) -> float:
    return {row["way_id"]: row for row in document["ways"]}[way_id]["meters_to_nearest_motorway"]


def cli_document(tmp_path: pathlib.Path, monkeypatch, *flags) -> dict:
    """`python -m etl.waydoc` as pass 1 ran it, with the DEM and landcover samplers stubbed.

    `main` has no argument for either sampler and the motorway distance depends on neither, so they are
    replaced at the module attributes `build` reads at call time. `--no-byways` because the byway overlay
    reads a real inputs file and is not the motorway set.
    """
    monkeypatch.setattr(waydoc.dem, "tiles_for_region", lambda region_id: frozenset())
    monkeypatch.setattr(waydoc.dem, "sample_smoothed", lambda points, tiles=None: elevation(points))
    monkeypatch.setattr(waydoc, "default_landcover", landcover)
    out = tmp_path / "clip-doc.json"
    argv = ["--input", str(CLIP), "--region", "la", "--out", str(out), "--no-byways"] + list(flags)
    assert waydoc.main(argv) == 0
    return json.loads(out.read_text(encoding="utf-8"))


def test_the_cli_measures_to_the_region_motorway_file_it_is_given(tmp_path, monkeypatch):
    """THE SEAM, through the shipping entry point: `main --motorways` answers the region set's distance."""
    written = distance_of(cli_document(tmp_path, monkeypatch, "--motorways", str(REGION_MOTORWAYS)), CANYON_WAY)
    assert written == distance_of(build(motorway_source=REGION_MOTORWAYS), CANYON_WAY)
    assert score.MOTORWAY_PROXIMITY_M < written < NEAR_HORIZON_M


def test_the_cli_without_a_motorway_file_measures_to_the_clips_own_motorways(tmp_path, monkeypatch):
    """The flag's OTHER path: no `--motorways` is the clip's own set, right for one self-contained clip."""
    assert distance_of(cli_document(tmp_path, monkeypatch), CANYON_WAY) == 0.0


def test_the_clip_answers_zero_because_the_clip_contains_the_motorway():
    """The behaviour being replaced, pinned so the change is visible rather than assumed."""
    assert distance_of(build(), CANYON_WAY) == 0.0


def test_the_motorway_distance_is_measured_to_the_supplied_region_set_not_to_the_clips_own_ways():
    """THE SEAM one layer down: with a region motorway file, the clip's own motorway 102 is not measured to.

    The region file's only motorway is ~390 m away, so way 101 moves from 0.0 to the far side of
    `score.MOTORWAY_PROXIMITY_M` - which is the boundary the whole x0.7 multiplier turns on.
    """
    metres = distance_of(build(motorway_source=REGION_MOTORWAYS), CANYON_WAY)
    assert metres > score.MOTORWAY_PROXIMITY_M
    assert metres < NEAR_HORIZON_M


def test_a_non_motorway_in_the_region_file_is_not_measured_to():
    """The region file also holds a residential way laid on way 101's first node.

    If the reader took every way in the file rather than `proximity.is_motorway`'s four classes, way 101
    would answer 0.0 again - this time for the wrong reason, and invisibly.
    """
    assert distance_of(build(motorway_source=REGION_MOTORWAYS), CANYON_WAY) != 0.0

"""T-0242: the region build, through its ONE entry point, gives a way in two tiles ONE score - the region's.

WHAT THIS FILE BINDS TO. `ops/etl-region --local <stage>` - the script the LA rebuild ran (in the ETL image,
where it execs the same `python -m regionbuild`) - over a TWO-TILE FIXTURE: T-0208's seam pair,
fixtures/seam_window_a.json and seam_window_b.json, unmodified. They are way documents (pass 1's output)
cut from T-0204's grid-a and grid-b docs; they share three byte-identical ways - Mulholland Drive
1533792498 and West Sunset Boulevard 399301293 among them - and differ in population, so a tile ranked
against itself gives those ways two scores (test_seam_one_score.py keeps that asserted).

The stages run here are reference -> score -> merge -> tag. motorways, tiles, docs, toxml and topbf need
osmium and GDAL, which only the ETL image has; the full LA rebuild through the same entry point is what
proves them (T-0242's Log).

EXACT EQUALITY, NOT AGREEMENT. Two tiles that agree with each other could both be wrong in the same way (a
reference over one tile only). So every scored row is compared to `assemble.assemble(document, reference)`
with the reference built here, over BOTH documents, the way region_reference composes it; the merged table
to those rows, first tile wins; and the tags on the written ways to `tagwriter.tags_for_row` of that row.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

from etl import assemble, region_reference, scenecheck, tagwriter
from regionbuild import tiles
from regionbuild.layout import Layout

ROOT = pathlib.Path(__file__).resolve().parents[3]
ENTRY = ROOT / "ops" / "etl-region"
FIXTURES = pathlib.Path(__file__).parent / "fixtures"
TILES = {"seam_window_a": FIXTURES / "seam_window_a.json", "seam_window_b": FIXTURES / "seam_window_b.json"}
REGION = "la"
MULHOLLAND = 1533792498
WEST_SUNSET = 399301293
SEAM_REFUSED = 3
LA_NONEMPTY_GRID_CELLS = 53


def document(tile: str) -> dict:
    return json.loads(TILES[tile].read_text(encoding="utf-8"))


def roundtrip(rows: list) -> list:
    return json.loads(json.dumps(rows))


def region_reference_over(documents: list) -> dict:
    """The reference over every tile of the build, composed by the shipping functions."""
    tables = []
    for doc in documents:
        byways = list(doc.get("byways") or [])
        tables.append(region_reference.raw_values([assemble.record_from_row(row, byways) for row in doc["ways"]]))
    return region_reference.table_of(region_reference.merge(tables))


def expected_rows() -> dict:
    """tile -> the rows `assemble` gives that tile against the region reference."""
    reference = region_reference_over([document(tile) for tile in sorted(TILES)])
    return {tile: roundtrip(assemble.assemble(document(tile), reference)) for tile in sorted(TILES)}


def entry(work: pathlib.Path, stage: str, tile_list: pathlib.Path) -> subprocess.CompletedProcess:
    """One stage through ops/etl-region, the way an operator types it."""
    bash = shutil.which("bash")
    assert bash, "no bash on PATH: ops/etl-region cannot be run"
    return subprocess.run([bash, ENTRY.as_posix(), "--local", stage, "--work", str(work),
                           "--tile-list", str(tile_list), "--jobs", "2"],
                          env={**os.environ, "PYTHON": pathlib.Path(sys.executable).as_posix()},
                          capture_output=True, text=True)


def new_store(root: pathlib.Path, tiles_present) -> tuple:
    layout = Layout(root, REGION)
    layout.docs.mkdir(parents=True)
    for tile in tiles_present:
        shutil.copyfile(TILES[tile], layout.doc_of(tile))
    tile_list = root / "tiles.txt"
    tile_list.write_text("\n".join(sorted(TILES)) + "\n", encoding="utf-8")
    return layout, tile_list


def clip_xml(path: pathlib.Path) -> None:
    """A clip holding every way of both tiles (scored or refused), each a road on two shared nodes."""
    ids = sorted({int(row["way_id"]) for tile in TILES for row in document(tile)["ways"]}
                 | {int(entry["way_id"]) for tile in TILES for entry in document(tile).get("refused") or []})
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<osm version="0.6" generator="test_region_build">',
             '  <node id="1" lat="34.1" lon="-118.45"/>', '  <node id="2" lat="34.1001" lon="-118.4501"/>']
    lines += ['  <way id="%d"><nd ref="1"/><nd ref="2"/><tag k="highway" v="secondary"/></way>' % way_id
              for way_id in ids]
    path.write_text("\n".join(lines + ["</osm>"]) + "\n", encoding="utf-8")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    layout, tile_list = new_store(tmp_path_factory.mktemp("region"), TILES)
    clip_xml(layout.clip_xml)
    runs = {stage: entry(layout.work, stage, tile_list) for stage in ("reference", "score", "merge", "tag")}
    return layout, runs


def scored(layout: Layout, tile: str) -> list:
    return json.loads(layout.scored_of(tile).read_text(encoding="utf-8"))["rows"]


def test_the_entry_point_scores_every_shared_way_once_against_the_region_reference(built):
    """THE SEAM PROPERTY through ops/etl-region: each tile's rows ARE the region-reference rows, exactly."""
    layout, runs = built
    for stage in ("reference", "score"):
        assert runs[stage].returncode == 0, "%s: %s%s" % (stage, runs[stage].stdout, runs[stage].stderr)
    expected = expected_rows()
    a, b = ({row["way_id"]: row["score"] for row in scored(layout, tile)} for tile in sorted(TILES))
    shared = sorted(set(a) & set(b))
    assert MULHOLLAND in shared and WEST_SUNSET in shared, "the fixture lost T-0204's named seam ways"
    differing = {way_id: (a[way_id], b[way_id]) for way_id in shared if a[way_id] != b[way_id]}
    assert differing == {}, "ops/etl-region gave a way in two tiles two scores: %s" % differing
    for tile in sorted(TILES):
        assert scored(layout, tile) == expected[tile], (
            "tile %s was not scored against the region reference over both tiles" % tile)


def test_the_merged_table_is_one_row_per_way_first_tile_wins(built):
    layout, runs = built
    assert runs["merge"].returncode == 0, runs["merge"].stdout + runs["merge"].stderr
    expected = expected_rows()
    first = {}
    for tile in sorted(TILES):
        for row in expected[tile]:
            first.setdefault(row["way_id"], row)
    merged = json.loads(layout.merged_table.read_text(encoding="utf-8"))["rows"]
    assert merged == [first[way_id] for way_id in sorted(first)]
    shared = set.intersection(*({row["way_id"] for row in expected[tile]} for tile in TILES))
    assert "seam_ways=%d seam_differ=0" % len(shared) in runs["merge"].stdout, runs["merge"].stdout


def test_the_tag_stage_writes_each_ways_merged_row_onto_it(built):
    layout, runs = built
    assert runs["tag"].returncode == 0, runs["tag"].stdout + runs["tag"].stderr
    merged = {row["way_id"]: row for row in json.loads(layout.merged_table.read_text(encoding="utf-8"))["rows"]}
    written = {way_id: {k: v for k, v in tags.items() if k.startswith(tagwriter.PREFIX)}
               for way_id, tags, _coords in scenecheck.read_ways(layout.tagged_xml)}
    assert set(written) == set(merged)
    assert {way_id: written[way_id] for way_id in merged} == {
        way_id: tagwriter.tags_for_row(row) for way_id, row in merged.items()}
    assert written[MULHOLLAND] == tagwriter.tags_for_row(merged[MULHOLLAND])


def test_the_reference_stage_refuses_a_plan_tile_with_no_document(tmp_path):
    """T-0208's first reference was built over 125 of 152 documents and nothing in its numbers said so."""
    layout, tile_list = new_store(tmp_path, ["seam_window_a"])
    run = entry(layout.work, "reference", tile_list)
    assert run.returncode == 2, run.stdout + run.stderr
    assert "seam_window_b" in run.stdout
    assert not layout.reference.exists()


def test_the_merge_stage_refuses_a_seam_way_with_two_scores(tmp_path):
    """A seam way whose tiles disagree stops the build before a table is written."""
    layout, tile_list = new_store(tmp_path, TILES)
    layout.scored.mkdir()
    for tile, rows in expected_rows().items():
        if tile == "seam_window_b":
            rows = [dict(row, score=row["score"] / 2) if row["way_id"] == MULHOLLAND else row for row in rows]
        layout.scored_of(tile).write_text(json.dumps({"rows": rows}), encoding="utf-8")
    run = entry(layout.work, "merge", tile_list)
    assert run.returncode == SEAM_REFUSED, run.stdout + run.stderr
    assert "DISAGREE way %d" % MULHOLLAND in run.stdout
    assert not layout.merged_table.exists()


def test_the_la_plan_is_152_tiles_that_partition_the_nonempty_grid_cells():
    names = tiles.plan(REGION)
    boxes = [tiles.bbox_of(REGION, name) for name in names]
    assert len(names) == len(set(names)) == 152
    overlapping = [(names[i], names[j]) for i in range(len(boxes)) for j in range(i + 1, len(boxes))
                   if min(boxes[i]["right"], boxes[j]["right"]) - max(boxes[i]["left"], boxes[j]["left"]) > 1e-9
                   and min(boxes[i]["top"], boxes[j]["top"]) - max(boxes[i]["bottom"], boxes[j]["bottom"]) > 1e-9]
    assert overlapping == []
    west, south, east, north, columns, rows = tiles.GRIDS[REGION]
    cell = (east - west) / columns * (north - south) / rows
    area = sum((box["right"] - box["left"]) * (box["top"] - box["bottom"]) for box in boxes)
    assert abs(area - LA_NONEMPTY_GRID_CELLS * cell) < 1e-6

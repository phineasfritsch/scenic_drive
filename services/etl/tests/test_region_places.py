"""T-0274: the region build makes places too - the T-0266 osmium pass and the T-0270 fallback corpus as stages.

WHAT THIS FILE BINDS TO. `regionbuild.cli.main` - what `python -m regionbuild` runs and ops/etl-region execs,
in the ETL image or with --local - and, for the pure-python fallback stage, `ops/etl-region --local` itself.

osmium exists only in the ETL image, so the places stage's osmium calls go to a recording fake of
`regionbuild.osm.run` that copies the allowlist fixture where `osmium cat` writes; the command lines are
asserted whole. The LA run through the image is the task Log's.

EXACT EQUALITY. The places in the bundle file are compared row for row to `fallback.choose` over
`placeallow.select` of the same stream, and the bundle's bytes to a file the SHIPPING `fallback.build`
writes from that stream with the same stamp: the stage adds nothing and drops nothing.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys

from etl import fallback, placeallow
from regionbuild import cli, osm, places
from regionbuild.layout import Layout

HERE = pathlib.Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "places_allowlist.osm.xml"
ENTRY = HERE.parents[2] / "ops" / "etl-region"
BUNDLE = pathlib.Path("apps") / "ios" / "ScenicDrive" / "Corpus" / "corpus-fallback.sqlite"
BUILT_AT = "2026-10-06T00:00:00Z"
COUNTS = {"data.count.nodes": "11\n", "data.count.ways": "22\n", "data.count.relations": "33\n"}


class FakeOsmium:
    """Records every osmium command; `cat` writes the fixture places stream, `fileinfo` answers COUNTS."""

    def __init__(self):
        self.calls = []

    def __call__(self, *command):
        command = [str(part) for part in command]
        self.calls.append(command)
        if command[1] == "tags-filter":
            pathlib.Path(command[command.index("-o") + 1]).write_bytes(b"pbf")
        elif command[1] == "cat":
            shutil.copyfile(FIXTURE, command[command.index("-o") + 1])
        elif command[1] == "fileinfo":
            return COUNTS[command[4]]
        return ""


def store(tmp_path: pathlib.Path, with_clip: bool = True) -> Layout:
    layout = Layout(tmp_path / "work", "la")
    layout.work.mkdir()
    if with_clip:
        layout.source.write_bytes(b"the unfiltered clip")
    return layout


def run_places(monkeypatch, capsys, layout: Layout) -> tuple:
    fake = FakeOsmium()
    monkeypatch.setattr(osm, "run", fake)
    code = cli.main(["places", "--work", str(layout.work), "--region", layout.region])
    return code, fake.calls, capsys.readouterr().out


def run_fallback(layout: Layout, root: pathlib.Path, region: str = "la") -> subprocess.CompletedProcess:
    bash = shutil.which("bash")
    assert bash, "no bash on PATH: ops/etl-region cannot be run"
    return subprocess.run([bash, ENTRY.as_posix(), "--local", "fallback", "--work", str(layout.work),
                           "--region", region, "--bundle-root", str(root)],
                          env={**os.environ, "PYTHON": pathlib.Path(sys.executable).as_posix()},
                          capture_output=True, text=True)


def stage_lines(out: str, prefix: str) -> list:
    return [line for line in out.splitlines() if line.startswith(prefix)]


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_region_build_runs_places_then_fallback_after_check():
    assert cli.ALL == ("motorways", "tiles", "docs", "reference", "score", "merge", "toxml", "tag", "topbf",
                       "check", "places", "fallback")
    assert cli.STAGES == cli.ALL + ("sha", "windows", "all")


def test_the_places_stage_runs_the_allowlist_pass_on_the_regions_own_clip(tmp_path, monkeypatch, capsys):
    layout = store(tmp_path)
    code, calls, out = run_places(monkeypatch, capsys, layout)
    assert code == 0
    assert calls == [
        ["osmium", "tags-filter", str(layout.work / "la.osm.pbf"), *placeallow.keep_expressions(),
         "-o", str(layout.work / "la-places.osm.pbf"), "--overwrite"],
        ["osmium", "cat", str(layout.work / "la-places.osm.pbf"), "-o", str(layout.work / "la-places.osm.xml"),
         "--overwrite"],
        ["osmium", "fileinfo", "-e", "-g", "data.count.nodes", str(layout.work / "la-places.osm.pbf")],
        ["osmium", "fileinfo", "-e", "-g", "data.count.ways", str(layout.work / "la-places.osm.pbf")],
        ["osmium", "fileinfo", "-e", "-g", "data.count.relations", str(layout.work / "la-places.osm.pbf")],
    ]
    assert (layout.work / "la-places.osm.xml").read_bytes() == FIXTURE.read_bytes()
    assert stage_lines(out, "PLACES") == [
        "PLACES OSM nodes=11 ways=22 relations=33 xml_bytes=%d" % FIXTURE.stat().st_size,
        placeallow.count_line(placeallow.select(FIXTURE)[1]),
    ]


def test_a_store_without_the_regions_own_clip_is_refused_before_osmium(tmp_path, monkeypatch, capsys):
    layout = store(tmp_path, with_clip=False)
    code, calls, out = run_places(monkeypatch, capsys, layout)
    assert (code, calls) == (2, [])
    assert stage_lines(out, "PLACES") == ["PLACES REFUSED: no unfiltered clip %s" % (layout.work / "la.osm.pbf")]
    assert not (layout.work / "la-places.osm.xml").exists()


def test_the_places_stream_reaches_the_bundle_corpus_row_for_row(tmp_path, monkeypatch, capsys):
    layout = store(tmp_path)
    assert run_places(monkeypatch, capsys, layout)[0] == 0
    root = tmp_path / "checkout"
    done = run_fallback(layout, root)
    assert done.returncode == 0, done.stdout + done.stderr
    bundle = root / BUNDLE
    expected = sorted((p["cls"], p["osm_type"], p["osm_id"], p["name"])
                      for p in fallback.choose(placeallow.select(FIXTURE)[0]))
    with sqlite3.connect(f"file:{bundle.as_posix()}?mode=ro", uri=True) as conn:
        rows = sorted(conn.execute("SELECT cls, osm_type, osm_id, name FROM places").fetchall())
    assert rows == expected
    reference = tmp_path / "reference.sqlite"
    fallback.build(FIXTURE, str(reference), BUILT_AT, "la")
    assert bundle.read_bytes() == reference.read_bytes()
    assert (layout.work / "la-corpus-fallback.sqlite").read_bytes() == reference.read_bytes()
    assert stage_lines(done.stdout, "FALLBACK file_sha256=") == ["FALLBACK file_sha256=%s" % sha256(reference)]
    assert stage_lines(done.stdout, "BUNDLE") == ["BUNDLE %s sha256=%s" % (bundle, sha256(reference))]


def test_two_fallback_runs_write_the_same_bytes(tmp_path):
    layout = store(tmp_path)
    shutil.copyfile(FIXTURE, layout.work / "la-places.osm.xml")
    digests = []
    for run in ("a", "b"):
        root = tmp_path / run
        done = run_fallback(layout, root)
        assert done.returncode == 0, done.stdout + done.stderr
        digests.append(sha256(root / BUNDLE))
    reference = tmp_path / "reference.sqlite"
    fallback.build(FIXTURE, str(reference), BUILT_AT, "la")
    assert digests == [sha256(reference)] * 2


def test_a_region_with_no_bundle_is_refused_and_writes_nothing(tmp_path):
    layout = Layout(tmp_path / "work", "sf")
    layout.work.mkdir()
    shutil.copyfile(FIXTURE, layout.work / "sf-places.osm.xml")
    root = tmp_path / "checkout"
    done = run_fallback(layout, root, region="sf")
    assert done.returncode == 2
    assert stage_lines(done.stdout, "BUNDLE") == ["BUNDLE REFUSED: region sf has no bundle in %s"
                                                  % sorted(places.BUNDLE)]
    assert not root.exists()
    assert not (layout.work / "sf-corpus-fallback.sqlite").exists()

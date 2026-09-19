"""The provenance stamp: what `tile_meta.py` writes into the archive's metadata and into the sidecar.

The module had no test at all (rv1-pr109 R3), so a stamp that hardcoded its region or its built_at - the
exact failure `check_pmtiles.py` then trusts, since the checker reads `meta.region` and `meta.built_at` back
out of the archive - survived the whole suite. Both subcommands are driven through `main()` here, with
values that are NOT the ones a hardcode would reach for: the merge case stamps `sfbay`, so a literal `la` in
`_provenance` fails by name.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tile_meta  # noqa: E402
from test_pmtiles_budget import LA_BBOX, good_metadata, write_pmtiles  # noqa: E402

BBOX = "-119.0,33.7,-117.85,34.45"
BUILT_AT = "2026-09-19T05:02:38Z"
REPLICATION = "2026-09-14T20:00:00Z"
# P-DATA-03's two keys plus the three that say which build these tiles came out of. Every one of them has to
# reach BOTH the archive's own metadata and the sidecar beside it.
STAMP = ("region", "built_at", "bbox", "maxzoom", "source_build")


def stamp_args(region: str = "la", built_at: str = BUILT_AT) -> list[str]:
    # `--bbox=` joined, exactly as build-la.sh spells it: a western longitude starts with a minus, and
    # argparse reads `--bbox -119.0,...` as a missing argument followed by an unknown option.
    return ["--region", region, f"--bbox={BBOX}", "--maxzoom", "14", "--build", "20260915",
            "--source-url", "https://build.protomaps.com/20260915.pmtiles", "--built-at", built_at]


def test_merge_stamps_the_arguments_into_the_source_metadata(tmp_path: Path) -> None:
    src = tmp_path / "src.json"
    src.write_text(json.dumps({"vector_layers": [{"id": "roads"}], "attribution": "OpenStreetMap",
                               "planetiler:osm:osmosisreplicationtime": REPLICATION}), encoding="utf-8")
    out = tmp_path / "meta.json"
    argv = ["merge", "--src-meta", str(src), "--out", str(out)] + stamp_args(region="sfbay")
    assert tile_meta.main(argv) == 0
    merged = json.loads(out.read_text(encoding="utf-8"))
    assert [key for key in STAMP if key not in merged] == []
    assert (merged["region"], merged["built_at"], merged["bbox"], merged["maxzoom"],
            merged["source_build"]) == ("sfbay", BUILT_AT, BBOX, 14, "20260915")
    # The OSM replication time outlives the build URL, so it is carried through rather than re-typed.
    assert merged["source_replication_time"] == REPLICATION
    # And nothing of the source's is lost: writing back metadata without vector_layers blinds every style.
    assert merged["vector_layers"] == [{"id": "roads"}]
    assert merged["attribution"] == "OpenStreetMap"


def test_merge_refuses_source_metadata_with_no_vector_layers(tmp_path: Path) -> None:
    src = tmp_path / "src.json"
    src.write_text(json.dumps({"attribution": "OpenStreetMap"}), encoding="utf-8")
    out = tmp_path / "meta.json"
    assert tile_meta.main(["merge", "--src-meta", str(src), "--out", str(out)] + stamp_args()) == 1
    assert not out.exists()


def test_the_sidecar_carries_the_stamp_and_the_files_own_bytes_and_sha256(tmp_path: Path) -> None:
    """The two facts that cannot live inside the file. A first-run download sheet needs both BEFORE it has
    the file, so they are measured off the bytes on disk - and checked here against a second, independent
    hash of the same bytes rather than by calling `sha256_of` back."""
    archive = write_pmtiles(tmp_path / "la.pmtiles", LA_BBOX,
                            good_metadata(source_replication_time=REPLICATION))
    out = tmp_path / "la.pmtiles.json"
    assert tile_meta.main(["sidecar", "--archive", str(archive), "--out", str(out)] + stamp_args()) == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert [key for key in STAMP if key not in record] == []
    assert (record["region"], record["built_at"], record["bbox"], record["maxzoom"],
            record["source_build"]) == ("la", BUILT_AT, BBOX, 14, "20260915")
    assert record["file"] == "la.pmtiles"
    assert record["bytes"] == archive.stat().st_size
    assert record["sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    # Read back out of the archive we just stamped, so the sidecar cannot claim a provenance the file lacks.
    assert record["source_replication_time"] == REPLICATION


def test_the_sidecar_refuses_an_archive_that_is_not_there(tmp_path: Path) -> None:
    out = tmp_path / "missing.json"
    argv = ["sidecar", "--archive", str(tmp_path / "nope.pmtiles"), "--out", str(out)] + stamp_args()
    assert tile_meta.main(argv) == 1
    assert not out.exists()

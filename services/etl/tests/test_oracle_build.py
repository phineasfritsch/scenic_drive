r"""`oracle_select.build()` under test - the provenance half and the funnel, exercised rather than asserted.

T-0025 round 5 made `build()` write `source_sha256` computed from the file it read (it had been a hardcoded
literal, so the fixture asserted its own provenance) and refuse a KMZ whose digest is not the manifest's pin.
Both halves then deleted with the suite green (T-0069, measured): the guard written for them compared two
hand-editable literals in the same commit, and NO test called `build()` or `eligible()` at all. So this file
calls `build()`, off a synthetic KMZ in `tmp_path` - no 2.5 MB oracle, no osmium, so it runs everywhere.

ROUND TWO (T-0074). Those six tests still left seven mutations green at `177 passed`, each one the ADJACENT
route to a hole this file had already closed:

  - the funnel had exactly ONE negative path, a `junction=roundabout` way, so `or near_tagged_node(...)`,
    `if not same_geometry(...)` and BOTH copies of `if len(rows) != 1: continue` deleted with nothing red;
  - every KMZ here was a few hundred bytes, so narrowing the refusal to `st_size < (1 << 20)` and collapsing
    `_sha256` to a single `fh.read(1 << 20)` were invisible at synthetic scale - and exactly wrong for the
    2 557 952-byte file both exist to protect.

Each condition now has a negative case driven through `build()`, and two KMZs here are over a megabyte.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from etl import curvature as cv
from etl import oracle
from etl import oracle_select as sel

MANIFEST = Path(__file__).resolve().parents[1] / "inputs" / "manifest.yaml"
PINNED_NAME = "vermont-curvature.kmz"

# Three collinear nodes: enough to clear `len(ours) < 3` in eligible(), and their curvature value is never
# read here - this file is about provenance and the funnel, not about agreement.
COORDS = [(44.0, -72.8), (44.001, -72.8), (44.002, -72.8)]
WAY_ID = 123
OTHER_WAY = 456
# ~11 m of latitude: over GEOMETRY_TOL_M (1 m) and under SQUASH_RADIUS_M (30 m), so the one offset serves as
# "this geometry is not the KML's" and as "this node is inside the squash radius".
NUDGE = 0.0001
STAMP = (2026, 9, 8, 0, 0, 0)   # fixed zip date, so a padded KMZ is byte-deterministic across two builds

_ROW = ('<tr><td><a href="https://www.openstreetmap.org/way/{way}">{way}</a></td>'
        "<td>asphalt</td><td>{curv}</td></tr>")

_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<Placemark>
  <name>{name}</name>
  <description><![CDATA[Curvature: 500
    <table>
    {rows}
    </table>]]></description>
  <LineString><coordinates>{coords}</coordinates></LineString>
</Placemark>
</Document></kml>
"""


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_kmz(path: Path, name: str = "Probe Road", ways=(WAY_ID,), coords=None, pad: int = 0) -> Path:
    """A KMZ holding one collection of `ways`, in the shape `etl.oracle`'s regexes read. `pad` bytes of a
    leading STORED member push it past a size threshold and, being written first and identically, also make
    two padded KMZs share their first `pad` bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    kml = _KML.format(name=name,
                      rows="\n    ".join(_ROW.format(way=w, curv=500.0) for w in ways),
                      coords=" ".join(f"{lon},{lat}" for lat, lon in (coords or COORDS)))
    with zipfile.ZipFile(path, "w") as z:
        if pad:
            z.writestr(zipfile.ZipInfo("pad.bin", STAMP), bytes(pad))
        z.writestr(zipfile.ZipInfo("doc.kml", STAMP), kml)
    return path


def write_export(path: Path, props: dict | None = None, way: int = WAY_ID, coords=None, nodes=()) -> Path:
    """An `osmium export -f geojsonseq` stream; default geometry matches the KMZ's, so condition 2 passes.
    `nodes` are `(id, properties, (lat, lon))` - osmium emits them in the same stream, and they become the
    tagged-node grid that condition 3 tests ways against."""
    lines = [json.dumps({
        "type": "Feature", "id": f"w{way}",
        "geometry": {"type": "LineString", "coordinates": [[lon, lat] for lat, lon in (coords or COORDS)]},
        "properties": props if props is not None else {"highway": "residential"},
    })]
    lines += [json.dumps({
        "type": "Feature", "id": f"n{nid}",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": nprops,
    }) for nid, nprops, (lat, lon) in nodes]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


class TestBuildRecordsTheFileItRead:
    def test_the_written_digest_is_the_kmz_on_disk_and_not_the_manifest_pin(self, tmp_path):
        """Restore the literal - `"source_sha256": "3bdf4d14...9046"` - and this is the test that goes red.
        The committed fixture happens to carry the manifest's digest, which is why the pre-existing
        assertion cannot tell a computed field from a typed one."""
        kmz = write_kmz(tmp_path / "not-the-oracle.kmz")
        export = write_export(tmp_path / "subset.geojsonseq")
        fixture = tmp_path / "out.json"

        n, _stages = sel.build(fixture, export, kmz)
        assert n == 1

        written = json.loads(fixture.read_text(encoding="utf-8"))["source_sha256"]
        pinned = oracle.pinned_digest(PINNED_NAME, MANIFEST)
        assert pinned, "the manifest pins no sha256 for " + PINNED_NAME
        assert written == sha256_of(kmz), "build() did not record the digest of the file it read"
        assert written != pinned, (
            "build() wrote the manifest's pin for a KMZ that is not the pinned oracle - the field is a "
            "literal again, and the fixture is asserting its own provenance")

    def test_the_digest_moves_when_the_bytes_move(self, tmp_path):
        """A constant is also 'the file's digest' for exactly one file. Two different KMZs, two digests."""
        export = write_export(tmp_path / "subset.geojsonseq")
        first = write_kmz(tmp_path / "a.kmz", name="Road A")
        second = write_kmz(tmp_path / "b.kmz", name="Road B Is Longer")
        assert sha256_of(first) != sha256_of(second)

        out_a, out_b = tmp_path / "a.json", tmp_path / "b.json"
        sel.build(out_a, export, first)
        sel.build(out_b, export, second)
        got_a = json.loads(out_a.read_text(encoding="utf-8"))["source_sha256"]
        got_b = json.loads(out_b.read_text(encoding="utf-8"))["source_sha256"]
        assert (got_a, got_b) == (sha256_of(first), sha256_of(second))

    def test_two_large_kmzs_sharing_a_first_block_still_get_different_digests(self, tmp_path):
        """`_sha256` streams in 1 MiB blocks. Collapse it to one `fh.read(1 << 20)` and every other KMZ in
        this file still hashes correctly - all are smaller than one block - while two oracles differing only
        after their first megabyte hash to the same value, and neither value is the file's. The shared
        prefix is asserted, not assumed, so the case cannot quietly stop testing this."""
        first = write_kmz(tmp_path / "big-a.kmz", name="Road A", pad=1 << 20)
        second = write_kmz(tmp_path / "big-b.kmz", name="Road B Is Longer", pad=1 << 20)
        assert first.read_bytes()[:1 << 20] == second.read_bytes()[:1 << 20]
        assert first.read_bytes() != second.read_bytes()

        export = write_export(tmp_path / "subset.geojsonseq")
        out_a, out_b = tmp_path / "a.json", tmp_path / "b.json"
        assert sel.build(out_a, export, first)[0] == 1
        assert sel.build(out_b, export, second)[0] == 1
        got_a = json.loads(out_a.read_text(encoding="utf-8"))["source_sha256"]
        got_b = json.loads(out_b.read_text(encoding="utf-8"))["source_sha256"]
        assert got_a != got_b, "a partial read cannot tell two oracles apart"
        assert (got_a, got_b) == (sha256_of(first), sha256_of(second))


class TestTheFunnelExcludesRatherThanCopies:
    """A way each condition excludes must not survive into the fixture, and the funnel must say where it
    died. Round one asserted that for one condition out of three; the other two deleted green."""

    @pytest.mark.parametrize("extra", [{"junction": "roundabout"},
                                       {"traffic_calming": "table"},
                                       {"parking:lane:left": "parallel"}])
    def test_a_squash_tagged_way_is_excluded(self, tmp_path, extra):
        """Condition 3's first half, over all three shapes `way_is_squash_tagged` reads: a value-restricted
        WAY_TAGS entry, an any-value one, and a WAY_TAG_PREFIXES key. Round one covered only the first."""
        kmz = write_kmz(tmp_path / "not-the-oracle.kmz")
        export = write_export(tmp_path / "e.geojsonseq", props={"highway": "residential", **extra})
        fixture = tmp_path / "out.json"
        n, stages = sel.build(fixture, export, kmz)
        assert n == 0
        assert stages["single_way"] == 1 and stages["geometry_identical"] == 1
        assert stages["no_squash"] == 0
        assert json.loads(fixture.read_text(encoding="utf-8"))["ways"] == []

    def test_a_tagged_node_inside_the_squash_radius_excludes_the_way(self, tmp_path):
        """Condition 3's second half - `or near_tagged_node(ours, grid)`. Every export round one wrote had
        zero node features, so the grid was always empty and the call a no-op; deleting it was green. The
        pair is the point: same KMZ, same way, built twice, the only difference one `highway=traffic_signals`
        node ~11 m off the middle vertex. Without the clean half, `n == 0` cannot distinguish a way this
        condition excluded from one that was never eligible."""
        kmz = write_kmz(tmp_path / "not-the-oracle.kmz")
        clean = write_export(tmp_path / "clean.geojsonseq")
        n, stages = sel.build(tmp_path / "clean.json", clean, kmz)
        assert (n, stages["no_squash"]) == (1, 1), "the way is eligible when no tagged node is near it"

        lat, lon = COORDS[1]
        assert cv.distance_on_earth(lat, lon, lat - NUDGE, lon) <= sel.SQUASH_RADIUS_M
        near = write_export(tmp_path / "near.geojsonseq",
                            nodes=[(9001, {"highway": "traffic_signals"}, (lat - NUDGE, lon))])
        fixture = tmp_path / "near.json"
        n, stages = sel.build(fixture, near, kmz)
        assert stages["geometry_identical"] == 1, "the way must reach condition 3 to be excluded by it"
        assert (n, stages["no_squash"]) == (0, 0)
        assert json.loads(fixture.read_text(encoding="utf-8"))["ways"] == []

    @pytest.mark.parametrize("coords, why", [
        ([(44.0, -72.8), (44.001 + NUDGE, -72.8), (44.002, -72.8)], "a vertex ~11 m from the KML's"),
        (COORDS + [(44.003, -72.8)], "the KML's vertices plus a fourth"),
    ])
    def test_geometry_that_is_not_the_kmls_is_excluded(self, tmp_path, coords, why):
        """Condition 2 - the one the module says drops 726 of 3297 ways, which agree 29.6% of the time
        against 90.4% for unchanged geometry. Round one's export always matched the KMZ exactly, so deleting
        `if not same_geometry(...)` while leaving the counter it asserted on changed nothing. Case two is the
        adjacent route: drop `len(ours) != len(theirs)` inside `same_geometry` and `zip` compares the common
        prefix, so a way carrying an extra vertex passes as identical."""
        kmz = write_kmz(tmp_path / "not-the-oracle.kmz")
        export = write_export(tmp_path / "e.geojsonseq", coords=coords)
        fixture = tmp_path / "out.json"
        n, stages = sel.build(fixture, export, kmz)
        assert stages["have_geometry"] == 1, "the way must reach condition 2 to be excluded by it"
        assert (n, stages["geometry_identical"]) == (0, 0), why
        assert json.loads(fixture.read_text(encoding="utf-8"))["ways"] == []


class TestOnlySingleWayCollectionsAreComparable:
    """Condition 1, in both places that enforce it. Nothing in the suite named `single_way_collections`,
    `oracle.collections` or `kml_geometry`, and no test had built a KMZ with more than one way in a
    Placemark, so both copies of `if len(rows) != 1: continue` deleted green."""

    def test_a_two_way_placemark_reaches_neither_the_index_nor_the_geometry(self, tmp_path):
        """The copies are independent: the one in `single_way_collections` decides what `eligible()`
        iterates, the one in `kml_geometry` what condition 2 compares against. Delete either alone and the
        other still holds the line - which is why each needs its own assertion, not one shared one."""
        kmz = write_kmz(tmp_path / "not-the-oracle.kmz", ways=(WAY_ID, OTHER_WAY))
        assert len(list(oracle.collections(kmz))) == 1, "the Placemark itself must still parse"
        assert oracle.single_way_collections(kmz) == {}
        assert oracle.kml_geometry(kmz) == {}

    def test_build_writes_no_way_from_a_two_way_collection(self, tmp_path):
        """Driven through `build()`, because the damage is concrete: the collection's first way lands in the
        fixture carrying geometry and a curvature computed over BOTH ways joined end to end. That is the
        comparison condition 1 refuses, and the whole justification for the oracle being comparable."""
        kmz = write_kmz(tmp_path / "not-the-oracle.kmz", ways=(WAY_ID, OTHER_WAY))
        export = write_export(tmp_path / "e.geojsonseq")
        fixture = tmp_path / "out.json"
        n, stages = sel.build(fixture, export, kmz)
        assert (n, stages["single_way"]) == (0, 0)
        assert json.loads(fixture.read_text(encoding="utf-8"))["ways"] == []


class TestBuildRefusesAnUnpinnedOracle:
    def test_it_raises_and_names_both_digests(self, tmp_path):
        """Delete the refusal - `if want and digest != want:` -> `if False:` - and this goes red. The message
        has to name both sides: 'not the pinned oracle' with no numbers leaves the reader unable to tell a
        truncated download from a deliberate upstream regeneration, which is the one decision this refusal
        exists to hand to a human."""
        kmz = write_kmz(tmp_path / PINNED_NAME)
        export = write_export(tmp_path / "subset.geojsonseq")
        fixture = tmp_path / "out.json"

        with pytest.raises(SystemExit) as excinfo:
            sel.build(fixture, export, kmz)

        message = str(excinfo.value)
        assert oracle.pinned_digest(PINNED_NAME, MANIFEST) in message
        assert sha256_of(kmz) in message
        assert not fixture.exists(), "build() wrote a fixture from a KMZ it had refused"

    def test_the_refusal_fires_at_the_size_of_the_file_it_protects(self, tmp_path):
        """Every other KMZ here is a few hundred bytes; `inputs/vermont-curvature.kmz` is 2 557 952. A
        refusal narrowed to `... and kmz.stat().st_size < (1 << 20)` therefore kept refusing every test KMZ
        while accepting the one real file it exists for. Both scales are covered now."""
        kmz = write_kmz(tmp_path / PINNED_NAME, pad=1 << 20)
        assert kmz.stat().st_size > (1 << 20), "this case tests nothing unless it is above the threshold"
        export = write_export(tmp_path / "subset.geojsonseq")
        fixture = tmp_path / "out.json"

        with pytest.raises(SystemExit) as excinfo:
            sel.build(fixture, export, kmz)
        assert sha256_of(kmz) in str(excinfo.value)
        assert not fixture.exists(), "build() wrote a fixture from a large KMZ it had refused"

    def test_the_refusal_is_keyed_on_the_basename_not_on_the_path(self, tmp_path):
        """`build()` asks `oracle.pinned_digest(kmz.name)`, so the pin follows the NAME wherever the file is.
        Executed through the CLI as well as here (T-0069): `--kmz work/probe/vermont-curvature.kmz` ->
        refused, exit 1, no fixture. Two directories, one pinned name, both refused."""
        export = write_export(tmp_path / "subset.geojsonseq")
        for sub in ("one", "two"):
            kmz = write_kmz(tmp_path / sub / PINNED_NAME)
            with pytest.raises(SystemExit):
                sel.build(tmp_path / f"{sub}.json", export, kmz)

    def test_renaming_the_kmz_walks_straight_past_the_refusal(self, tmp_path):
        """The other direction of the same keying, and it is a hole - recorded here, not fixed here. Byte-
        identical file, non-pinned basename, `pinned_digest` returns None so `want` is falsy and the refusal
        never fires; through the CLI (T-0069) that was exit 0, one way written, no complaint. What contains
        it is the OTHER half: the digest written is the renamed file's, so the rebuilt fixture trips
        `test_the_fixture_was_built_from_the_pinned_oracle` - measured by overwriting the committed fixture
        with such a build, `c070142a...` != `3bdf4d14...`. The halves cover each other only while BOTH
        live, which is why this file calls `build()` twice over."""
        kmz = write_kmz(tmp_path / "vermont-curvature-copy.kmz")
        export = write_export(tmp_path / "subset.geojsonseq")
        fixture = tmp_path / "out.json"

        assert oracle.pinned_digest(kmz.name, MANIFEST) is None
        n, _ = sel.build(fixture, export, kmz)          # no refusal: the pin does not know this name
        assert n == 1
        written = json.loads(fixture.read_text(encoding="utf-8"))["source_sha256"]
        assert written == sha256_of(kmz)
        assert written != oracle.pinned_digest(PINNED_NAME, MANIFEST), (
            "a fixture built this way must NOT be able to claim the pinned digest - that claim is the only "
            "thing standing between the rename and a silently replaced oracle")

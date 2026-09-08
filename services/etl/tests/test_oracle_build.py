r"""`oracle_select.build()` under test - the provenance half of T-0025, exercised rather than asserted about.

T-0025 round 5 fixed two things: `build()` writes `source_sha256` computed from the file it read (it used to
be a hardcoded literal, so the fixture asserted its own provenance), and `build()` refuses a KMZ whose digest
is not the manifest's pin. `test_oracle_report.py::test_the_fixture_was_built_from_the_pinned_oracle` was
written as the guard that makes that stick.

It does not. Both halves were deleted with the whole suite green (T-0069, measured):

    "source_sha256": digest  ->  "source_sha256": "3bdf4d14...9046"    171 passed, nothing red
    if want and digest != want:  ->  if False:                         171 passed, nothing red

Because both sides of that assertion - the committed fixture's field and `inputs/manifest.yaml`'s pin - are
hand-editable text sitting in the same commit, and NO test in the suite called `build()` or `eligible()` at
all: `git grep -n 'build(\|eligible('` over `tests/` returned exactly one hit, inside a module docstring. An
assertion comparing two committed literals cannot reach a claim about what a function computes.

So this file calls `build()`. Everything here runs off a synthetic three-node KMZ built in `tmp_path`, so it
needs neither the 2.5 MB oracle nor osmium and runs everywhere the suite does.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from etl import oracle
from etl import oracle_select as sel

MANIFEST = Path(__file__).resolve().parents[1] / "inputs" / "manifest.yaml"
PINNED_NAME = "vermont-curvature.kmz"

# Three collinear nodes: enough to clear `len(ours) < 3` in eligible(), and their curvature value is never
# read here - this file is about provenance and the funnel, not about agreement.
COORDS = [(44.0, -72.8), (44.001, -72.8), (44.002, -72.8)]
WAY_ID = 123

_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<Placemark>
  <name>{name}</name>
  <description><![CDATA[Curvature: 500
    <table>
    <tr><td><a href="https://www.openstreetmap.org/way/{way}">{way}</a></td>
        <td>asphalt</td><td>500.0</td></tr>
    </table>]]></description>
  <LineString><coordinates>{coords}</coordinates></LineString>
</Placemark>
</Document></kml>
"""


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_kmz(path: Path, name: str = "Probe Road", way: int = WAY_ID) -> Path:
    """A KMZ with one single-way collection, in the shape `etl.oracle`'s regexes read."""
    path.parent.mkdir(parents=True, exist_ok=True)
    kml = _KML.format(name=name, way=way,
                      coords=" ".join(f"{lon},{lat}" for lat, lon in COORDS))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("doc.kml", kml)
    return path


def write_export(path: Path, props: dict | None = None, way: int = WAY_ID) -> Path:
    """An `osmium export -f geojsonseq` line whose geometry matches the KMZ's, so condition 2 passes."""
    path.write_text(json.dumps({
        "type": "Feature", "id": f"w{way}",
        "geometry": {"type": "LineString", "coordinates": [[lon, lat] for lat, lon in COORDS]},
        "properties": props if props is not None else {"highway": "residential"},
    }) + "\n", encoding="utf-8")
    return path


class TestBuildRecordsTheFileItRead:
    def test_the_written_digest_is_the_kmz_on_disk_and_not_the_manifest_pin(self, tmp_path):
        """The property round 5 claimed to introduce, and the one nothing exercised.

        Restore the literal - `"source_sha256": "3bdf4d14...9046"` - and this is the test that goes red. The
        committed fixture happens to carry the manifest's digest, which is why the existing assertion cannot
        tell a computed field from a typed one.
        """
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

    def test_build_runs_the_funnel_rather_than_copying_the_kmz(self, tmp_path):
        """`build()` -> `eligible()` was also uncalled by the suite. A way the squash conditions exclude must
        not survive into the fixture, and the funnel must say where it died."""
        kmz = write_kmz(tmp_path / "not-the-oracle.kmz")
        export = write_export(tmp_path / "e.geojsonseq",
                              props={"highway": "residential", "junction": "roundabout"})
        fixture = tmp_path / "out.json"
        n, stages = sel.build(fixture, export, kmz)
        assert n == 0
        assert stages["single_way"] == 1 and stages["geometry_identical"] == 1
        assert stages["no_squash"] == 0
        assert json.loads(fixture.read_text(encoding="utf-8"))["ways"] == []


class TestBuildRefusesAnUnpinnedOracle:
    def test_it_raises_and_names_both_digests(self, tmp_path):
        """Delete the refusal - `if want and digest != want:` -> `if False:` - and this is the test that goes
        red. Nothing else in the suite noticed, because nothing else called `build()`.

        The message has to name both sides: 'not the pinned oracle' with no numbers leaves the reader unable
        to tell a truncated download from a deliberate upstream regeneration, which is the one decision this
        refusal exists to hand to a human.
        """
        kmz = write_kmz(tmp_path / PINNED_NAME)
        export = write_export(tmp_path / "subset.geojsonseq")
        fixture = tmp_path / "out.json"

        with pytest.raises(SystemExit) as excinfo:
            sel.build(fixture, export, kmz)

        message = str(excinfo.value)
        assert oracle.pinned_digest(PINNED_NAME, MANIFEST) in message
        assert sha256_of(kmz) in message
        assert not fixture.exists(), "build() wrote a fixture from a KMZ it had refused"

    def test_the_refusal_is_keyed_on_the_basename_not_on_the_path(self, tmp_path):
        """`build()` asks `oracle.pinned_digest(kmz.name)`, so the pin follows the NAME wherever the file is.

        Executed through the CLI as well as here (T-0069):
          `--kmz work/probe/vermont-curvature.kmz` -> refused, exit 1, no fixture written.
        Two unrelated directories, one pinned name, both refused - so the guard is reachable for a
        differently-located file, which is the direction that protects.
        """
        export = write_export(tmp_path / "subset.geojsonseq")
        for sub in ("one", "two"):
            kmz = write_kmz(tmp_path / sub / PINNED_NAME)
            with pytest.raises(SystemExit):
                sel.build(tmp_path / f"{sub}.json", export, kmz)

    def test_renaming_the_kmz_walks_straight_past_the_refusal(self, tmp_path):
        """The other direction of the same keying, and it is a hole - recorded here, not fixed here.

        Byte-identical file, non-pinned basename, and `pinned_digest` returns None so `want` is falsy and the
        refusal never fires. Executed through the CLI (T-0069):
          `--kmz work/probe/not-the-oracle.kmz --build ...` -> exit 0, 1 way written, no complaint.

        What keeps it contained is the OTHER half: the digest written is the renamed file's, so the rebuilt
        fixture trips `test_the_fixture_was_built_from_the_pinned_oracle`. Measured, by overwriting the
        committed fixture with such a build: that test failed, `c070142a...` != `3bdf4d14...`. The two halves
        cover each other only while BOTH live, which is the whole reason this file calls `build()` twice over.
        """
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

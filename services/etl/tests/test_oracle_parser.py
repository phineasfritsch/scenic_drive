r"""Every reader in the oracle's two modules, fed the input nothing in the suite had fed it.

Three readers: the KML Placemark parser in `etl.oracle` (`collections` and `kml_geometry`), the osmium-export
parser in `etl.oracle_select` (`load_export`), and the manifest parser `etl.oracle.pinned_digest`. Each one
consumes a file this repository does not write, and each one had been tested only on input this repository
DID write - well-formed, complete, and produced by the same tests that then asserted about it.

THE FOUR PARSER GUARDS in `etl.oracle`, first.

`ops/etl-mutation` turned each of these `continue`s into `pass` and the suite stayed green:

    oracle.py:82    collections()    `if not m: continue`      - a Placemark with no <description>
    oracle.py:86    collections()    `if not rows: continue`   - a description with no constituent-way rows
    oracle.py:119   kml_geometry()   `if not m: continue`      - the same, in the geometry pass
    oracle.py:125   kml_geometry()   `if not cm: continue`     - a Placemark with no <coordinates>

Not because the guards are equivalent - three of the four are an `AttributeError` on `None.group(1)` the
moment they stop guarding - but because every KMZ the suite wrote was well-formed, so none of the four was
ever reached. A guard that has never been reached is untested no matter how obviously right it looks.

The input is 3318 Placemarks of somebody else's XML, pinned by digest precisely because it is expected to be
regenerated: T-0025 recorded that "an oracle that silently follows upstream is not an oracle. If they
regenerate it the fetch fails and a human re-pins it having looked at what changed." The human then looks at
a diff, and what these guards decide is whether one differently-shaped Placemark in it means "skipped a block
we cannot read" or means the rebuild dies - or, for :86, means a collection with an empty way table walks
into the funnel and is counted.

The four cases are separate because the guards are separate: `collections` decides what `single_way_
collections` indexes, `kml_geometry` decides what condition 2 compares against, and deleting either one
alone leaves the other still holding the line.
"""
from __future__ import annotations

import json

from etl import oracle
from etl import oracle_select as sel
from tests import oracle_kmz as ok

GOOD = 111
BROKEN = 222
FAR = [(45.0, -72.8), (45.001, -72.8), (45.002, -72.8)]   # the malformed block's way, when it has geometry


def _good_and(tmp_path, broken_block, name="k.kmz"):
    """A KMZ holding one well-formed single-way collection and one malformed Placemark.

    The good half is not decoration: without it, "the malformed block produced nothing" is indistinguishable
    from "the parser produced nothing", which is the state a crashed generator is also in.
    """
    return ok.write_kmz(tmp_path / name, ok.collection(GOOD), broken_block)


class TestCollectionsSkipsABlockItCannotRead:
    def test_a_placemark_with_no_description_is_skipped_and_not_dereferenced(self, tmp_path):
        """oracle.py:82. `DESCRIPTION.search` returns None, and the next statement is
        `html.unescape(m.group(1))`. Stop guarding and the whole generator raises on the first such block,
        so a single Placemark carrying only a name takes down `--list-ways`, and with it step 1 of
        `ops/etl-curvature-fixture`."""
        kmz = _good_and(tmp_path, ok.placemark("No Description", ways=(BROKEN,), description=False))
        got = list(oracle.collections(kmz))
        assert [rows[0][0] for _name, _total, rows in got] == [GOOD]

    def test_a_placemark_whose_table_holds_no_way_rows_is_skipped(self, tmp_path):
        """oracle.py:86, and the one guard of the four whose failure is silent.

        `WAY_ROW.findall` returns [] for a description that is not a constituent-ways table at all - a
        legend, a folder marker, a Placemark upstream added for something else. Stop guarding and that block
        is yielded as a collection with an empty way list. `single_way_collections` then drops it on
        `len(rows) != 1`, so nothing downstream changes and nothing raises; what changes is the count in
        `oracle: N collections, M of them single-way`, which is the number a human compares before and after
        a re-pin to decide whether the new KMZ is the same shape as the old one.
        """
        kmz = _good_and(tmp_path, ok.placemark("Legend", ways=()))
        got = list(oracle.collections(kmz))
        assert len(got) == 1, "a Placemark carrying no way rows was yielded as a collection"
        assert [rows[0][0] for _name, _total, rows in got] == [GOOD]
        assert all(rows for _name, _total, rows in got), "a collection with an empty way table"


class TestKmlGeometrySkipsABlockItCannotRead:
    def test_a_placemark_with_no_description_is_skipped(self, tmp_path):
        """oracle.py:119. The same shape as :82 and a genuinely separate guard: this pass decides what
        condition 2 compares against, and it runs over the whole KML again rather than over what
        `collections` yielded."""
        kmz = _good_and(tmp_path, ok.placemark("No Description", ways=(BROKEN,),
                                               coords=FAR, description=False))
        assert sorted(oracle.kml_geometry(kmz)) == [GOOD]

    def test_a_placemark_with_no_coordinates_is_skipped(self, tmp_path):
        """oracle.py:125, the guard with no counterpart in `collections`.

        A Placemark can carry a perfectly good constituent-ways table and no `<LineString>`, and then it is
        published WITHOUT the geometry Curvature computed over. `PLACEMARK_COORDS.search` returns None and
        the next statement is `cm.group(1).split()`. Skipping is the only correct answer: the way stays in
        `single_way_collections`, so it is still published, but `eligible()` finds no `theirs` for it and
        excludes it on condition 2 - a way whose geometry we cannot see is a way we cannot compare.
        """
        kmz = _good_and(tmp_path, ok.placemark("No Geometry", ways=(BROKEN,), coords=None))
        assert BROKEN in oracle.single_way_collections(kmz), "the way is still published"
        assert sorted(oracle.kml_geometry(kmz)) == [GOOD], "but it has no geometry to be compared against"

    def test_the_two_passes_disagree_only_where_the_geometry_is_missing(self, tmp_path):
        """The invariant that makes `eligible()`'s `not theirs` operand reachable at all: every key in
        `kml_geometry` is a key in `single_way_collections`, and the difference is exactly the blocks whose
        `<coordinates>` are absent."""
        kmz = _good_and(tmp_path, ok.placemark("No Geometry", ways=(BROKEN,), coords=None))
        published = set(oracle.single_way_collections(kmz))
        geometry = set(oracle.kml_geometry(kmz))
        assert geometry <= published
        assert published - geometry == {BROKEN}


class TestAMalformedNeighbourDoesNotStopTheRebuild:
    def test_the_good_collection_still_reaches_the_fixture(self, tmp_path):
        """All four shapes in one KMZ, driven through `build()`, because that is where the damage lands.

        The guards protect a rebuild of the committed fixture from one unreadable Placemark among thousands.
        With any of them removed this is not a smaller fixture, it is no fixture and a traceback - and
        `ops/etl-curvature-fixture` would report `BUILD FAILED` for a KMZ that is almost entirely fine.
        """
        kmz = ok.write_kmz(
            tmp_path / "mixed.kmz",
            ok.placemark("No Description", ways=(901,), description=False),
            ok.placemark("Legend", ways=()),
            ok.placemark("No Geometry", ways=(902,), coords=None),
            ok.collection(GOOD),
            ok.placemark("Pair", ways=(903, 904)),
        )
        export = ok.write_export(tmp_path / "e.geojsonseq",
                                 ways=[ok.road(GOOD)] + [ok.road(w, FAR) for w in (901, 902, 903, 904)])
        fixture = tmp_path / "fixture.json"
        n, stages = sel.build(fixture, export, kmz)
        assert (n, stages["single_way"]) == (1, 2), "only the good collection and the geometry-less one"
        assert [w["way_id"] for w in json.loads(fixture.read_text(encoding="utf-8"))["ways"]] == [GOOD]


class TestTheExportReaderTakesTheShapesTheFormatAllows:
    """`oracle_select.load_export` is the same defect in the other module: two opening guards and three
    defaults that no test had ever reached, because every export the suite wrote was a few clean objects."""

    def test_a_plain_geojson_collection_reads_the_same_as_a_sequence(self, tmp_path):
        r"""The guards are why one reader takes `-f geojsonseq` AND `-f geojson`: a FeatureCollection's
        opening `{"type": "FeatureCollection", "features": [` starts with `{` and is not valid JSON on its
        own, so the `except json.JSONDecodeError: continue` skips it; its closing `]}` does not start with
        `{`; and each member line's trailing comma is what `rstrip(",")` removes.

        The `or {}` defaults are RFC 7946, not paranoia: a Feature's `geometry` MAY be null and its
        `properties` MAY be null. The id-less features are the other real shape - an export produced without
        `--add-unique-id=type_id` carries no `id` at all - and the LineString one is what stops
        `ident.startswith("w")` from being dead: without it, ANY LineString feature is read as a way and
        `int(ident[1:])` is `int("")`.

        The `or ""` on the id itself is the one this case does NOT kill, and the attempt is what showed why.
        The reasoning was that dropping it leaves an id-less feature as `str(None)`, and that
        `"None".startswith("n")` would then collect it as a tagged node - but `str(None)` is `"None"` with a
        capital N, so it begins with neither `"w"` nor `"n"` and both branches skip it exactly as the empty
        string does. Every id that reaches a branch is a string beginning `w` or `n`, whose `str()` is
        itself; every falsy one stringifies to something that reaches neither. That mutation is equivalent,
        and it is recorded as one rather than chased.
        """
        members = [
            json.dumps({"type": "Feature", "id": "w1", "geometry": None,
                        "properties": {"highway": "residential"}}),
            json.dumps({"type": "Feature", "id": "w2",
                        "geometry": {"type": "LineString", "coordinates": [[-72.8, 44.0], [-72.79, 44.01]]},
                        "properties": None}),
            json.dumps({"type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": [[-72.7, 44.2], [-72.69, 44.21]]},
                        "properties": {"highway": "residential"}}),
            json.dumps({"type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-72.8, 44.0]},
                        "properties": {"highway": "traffic_signals"}}),
        ]
        path = tmp_path / "e.geojson"
        path.write_text('{"type": "FeatureCollection", "features": [\n' + ",\n".join(members) + "\n]}\n",
                        encoding="utf-8")

        ways, props, tagged = sel.load_export(path)
        assert sorted(ways) == [2], "the only readable way is the one with both an id and a LineString"
        assert ways[2][0] == (44.0, -72.8)
        assert props[2] == {}, "a null `properties` must arrive as an empty dict, not as None"
        assert tagged == [], "a feature with no id is not a node, whatever its geometry reads like"


class TestThePinReaderReadsTheManifestItIsGiven:
    """`pinned_digest` is the third reader in `etl/oracle.py`, and it parses `inputs/manifest.yaml` by hand.

    The `manifest` PARAMETER could be dropped - `path = manifest or (ROOT / "inputs" / "manifest.yaml")`
    reduced to the default alone - with the suite green, because every caller in the suite passes exactly
    that default path, so no case could tell an honoured argument from an ignored one. A parameter that is
    silently ignored is worse than one that does not exist: everything `oracle_select.build` refuses rests on
    this function answering about the manifest it was ASKED about.
    """

    def _manifest(self, tmp_path, body: str):
        path = tmp_path / "manifest.yaml"
        path.write_text(body, encoding="utf-8")
        return path

    def test_the_manifest_argument_is_the_file_that_is_read(self, tmp_path):
        other = self._manifest(tmp_path, "inputs:\n  - name: vermont-curvature.kmz\n"
                                         "    sha256: " + "0" * 64 + "\n")
        got = oracle.pinned_digest("vermont-curvature.kmz", other)
        assert got == "0" * 64
        assert got != oracle.pinned_digest("vermont-curvature.kmz"), (
            "pinned_digest ignored the manifest it was handed and read the repository's own instead")

    def test_a_sha256_line_with_nothing_after_it_names_no_digest(self, tmp_path):
        """`return want or None`. The docstring promises None when the manifest "names no digest", and an
        empty value names none - a half-written entry must read as unpinned rather than as pinned to the
        empty string, because `build()` decides whether to refuse on the truthiness of this answer and a
        reader deciding whether the input IS pinned gets `None` either way only if this says so."""
        empty = self._manifest(tmp_path, "inputs:\n  - name: vermont-curvature.kmz\n    sha256:\n")
        assert oracle.pinned_digest("vermont-curvature.kmz", empty) is None

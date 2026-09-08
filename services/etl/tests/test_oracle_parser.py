r"""The four parser guards in `etl.oracle`, fed the malformed Placemarks nothing in the suite fed them.

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

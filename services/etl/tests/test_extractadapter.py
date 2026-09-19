"""The committed waydoc -> extract path, over REAL Los Angeles ways, through the entry point production runs.

Until this file there was no committed converter between `etl.waydoc`'s document ({way_id, tags, coords})
and the extract `etl.extractway.load_extract` reads ({id, cls, highway, access_ok, oneway, nodes, ...}), so
nothing in CI had ever fed `corpus.build` a real way. T-0206 measured LA through a throwaway in a gitignored
work/ dir; this suite is the same conversion, shipped, asserted row by row against real tags.

EVERY ASSERTION BELOW IS READ OFF `extractadapter.main`, the entry point `python -m etl.extractadapter`
runs, not off a helper: the adapter is executed ONCE into a temp file and the tests read what the corpus
reader loads back from it. A defect-named test that bound to a helper would leave the shipping path
untested (CLAUDE.md, File discipline).

THE SLICE is tests/fixtures/canyon_adapter_slice.json: real ways, ODbL, way_id/tags/coords verbatim out of
T-0206's two LA documents (the canyon window and the eastern grid), the producer outputs this adapter never
reads dropped and named in the document's own `dropped_keys` field. The ids below are quoted in the task
Log's ruling R4 with what each one pins.
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import tempfile

import pytest

from etl import accessrule, assemble, extractadapter, surface
from etl.extractway import load_extract

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
SLICE = FIXTURES / "canyon_adapter_slice.json"

# The rows, by what each one is here to pin (task Log, R4).
PRIVATE_DIRT = 1206170836        # access=private + surface=dirt: BOTH answers, and `unpaved` fires first
PRIVATE_TRACK = 10724329         # access=private + highway=track: the track rule fires first
MOTOR_VEHICLE_NO = 1331140342    # the second access rule, alone, on an otherwise ungated way
ONEWAY_REVERSE = 1288190701      # Zuma Access Road, oneway=-1
ONEWAY_FORWARD = 13465412        # Calle de Sarah, oneway=yes, access=yes
ONEWAY_TWO_WAY = 42833983        # Vereda de la Montura, oneway=no
ROUNDABOUT_TAGGED = 1514080016   # junction=roundabout AND oneway=yes
ROUNDABOUT_UNTAGGED = 338438553  # junction=roundabout, no oneway tag, access=private, no name
CIRCULAR = 1025983659            # junction=circular (Seaver Drive): no oneway implication
TRACK_PLAIN = 179078676          # highway=track, no name, no surface tag
MOTORWAY_LINK = 299078436        # a motorway is penalised, never excluded
DESTINATION = 640857250          # access=destination IS in CLOSED_ACCESS
CUSTOMERS = 42798087             # access=customers is NOT
MOTOR_VEHICLE_PRIVATE = 221164479  # motor_vehicle refuses on `no` only
PERMIT = 799554704               # access=permit
NO_ACCESS = 426254440            # access=no
# The two ways T-0206's throwaway skipped, of 23,474: both highway=footway, Universal CityWalk Hollywood.
OUTSIDE_THE_TABLE = (1211805282, 1211805283)
# The slice's ONE synthetic row, labelled `synthetic` in the fixture itself: one coordinate. Neither real
# document carries a row under two coordinates (0 of 11,740 and 0 of 23,474), so `skipped_short` - a field
# of main's own count line - had no real row it could ever be seen red on (task Log, S2).
SHORT_SYNTHETIC = 9000000001

_RUN: dict = {}


def adapted() -> dict:
    """`python -m etl.extractadapter` over the slice, run once: {ways, region, stdout, path}."""
    if not _RUN:
        out = pathlib.Path(tempfile.mkdtemp(prefix="t0217-")) / "slice-extract.json"
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            code = extractadapter.main(["--input", str(SLICE), "--out", str(out)])
        region, ways = load_extract(out)
        _RUN.update(code=code, region=region, path=out, stdout=printed.getvalue(),
                    ways={way.way_id: way for way in ways})
    return _RUN


def way(way_id: int):
    ways = adapted()["ways"]
    assert way_id in ways, "way %d is not in the adapted extract; it carries %r" % (
        way_id, sorted(ways)[:5])
    return ways[way_id]


def tags_of(way_id: int) -> dict:
    doc = json.loads(SLICE.read_text(encoding="utf-8"))
    for row in doc["ways"]:
        if row["way_id"] == way_id:
            return row["tags"]
    raise AssertionError("way %d is not in the slice" % way_id)


def test_the_slice_is_real_odbl_data_and_says_which_document_each_way_came_from():
    doc = json.loads(SLICE.read_text(encoding="utf-8"))
    assert "ODbL" in doc["licence"] and "OpenStreetMap" in doc["licence"], doc.get("licence")
    assert doc["dropped_keys"], "the fixture must name what was dropped, not drop it in silence"
    real = [row for row in doc["ways"] if "synthetic" not in row]
    synthetic = [row for row in doc["ways"] if "synthetic" in row]
    assert {row["source"] for row in real} == {"la/window-doc.json", "la-grid/grid-b-doc.json"}
    assert len(real) == 18 and len(doc["ways"]) == 19
    assert [row["way_id"] for row in synthetic] == [SHORT_SYNTHETIC]
    assert synthetic[0]["synthetic"], "a row that is not a real way says so in its own field"


def test_the_whole_slice_is_accepted_by_the_reader_corpus_build_uses():
    run = adapted()
    assert run["code"] == 0
    assert run["region"] == "la"
    # 18 real ways and one synthetic short row in; two out-of-table and one short skipped; 16 through.
    assert len(run["ways"]) == 16, sorted(run["ways"])


def test_a_private_dirt_road_is_refused_although_gate_reason_answers_unpaved_surface():
    """The 06:13 panel's correction. `access_ok == (gate_reason(tags) != GATE_NO_ACCESS)` would grant this
    real way access: `gate_reason` returns the FIRST firing rule, and for way 1206170836 - access=private,
    surface=dirt - that rule is the surface one. The access question is answered on its own."""
    tags = tags_of(PRIVATE_DIRT)
    assert tags["access"] == "private" and tags["surface"] == "dirt"
    assert assemble.gate_reason(tags) == assemble.GATE_UNPAVED_SURFACE, assemble.gate_reason(tags)
    row = way(PRIVATE_DIRT)
    assert row.access_ok == 0, "a private road reached the corpus with access_ok=1"
    assert row.surface == "dirt"
    assert row.surface_state == surface.SURFACE_UNPAVED


def test_a_private_track_is_refused_by_the_access_rule_that_the_track_rule_hides():
    tags = tags_of(PRIVATE_TRACK)
    assert assemble.gate_reason(tags) == assemble.GATE_TRACK
    assert way(PRIVATE_TRACK).access_ok == 0
    # And a track with nothing said about access is NOT refused: tracks are gated by the router, not here.
    assert way(TRACK_PLAIN).access_ok == 1
    assert way(TRACK_PLAIN).cls == "track"


def test_motor_vehicle_no_refuses_a_way_no_other_rule_touches():
    tags = tags_of(MOTOR_VEHICLE_NO)
    assert "access" not in tags and tags["motor_vehicle"] == "no" and tags["surface"] == "asphalt"
    assert assemble.gate_reason(tags) == assemble.GATE_NO_ACCESS
    assert way(MOTOR_VEHICLE_NO).access_ok == 0


def test_the_access_rule_has_one_definition_and_gate_reason_is_the_caller():
    """No second copy (acceptance line 1). Identity, not equality: a re-import of the same literals would
    satisfy an `==` and drift the day one side is edited."""
    assert assemble.access_refused is accessrule.access_refused
    assert assemble.CLOSED_ACCESS is accessrule.CLOSED_ACCESS
    assert assemble.MOTOR_VEHICLE_KEY is accessrule.MOTOR_VEHICLE_KEY
    assert assemble.MOTOR_VEHICLE_REFUSED is accessrule.MOTOR_VEHICLE_REFUSED
    assert set(accessrule.CLOSED_ACCESS) == {"private", "no", "permit", "destination"}
    assert accessrule.MOTOR_VEHICLE_REFUSED == "no"


@pytest.mark.parametrize("access", [None, "private", "no", "permit", "destination", "customers",
                                    "permissive", "yes", "delivery", "military"])
@pytest.mark.parametrize("motor_vehicle", [None, "no", "private", "permit", "yes", "destination"])
def test_the_refactored_gate_reason_answers_exactly_what_the_two_branches_answered(access, motor_vehicle):
    """The equivalence the factoring has to preserve, over the whole value space both keys take in LA,
    against the two branches as `assemble.py` spelled them before T-0217 (Gates.swift:160, :161)."""
    tags = {"highway": "residential", "surface": "asphalt"}
    if access is not None:
        tags["access"] = access
    if motor_vehicle is not None:
        tags["motor_vehicle"] = motor_vehicle
    before = (access is not None and access in assemble.CLOSED_ACCESS) or motor_vehicle == "no"
    assert accessrule.access_refused(tags) is before
    assert (assemble.gate_reason(tags) == assemble.GATE_NO_ACCESS) is before


def test_the_adapters_access_ok_is_the_predicate_on_every_way_of_the_slice():
    for way_id, row in adapted()["ways"].items():
        expected = 0 if accessrule.access_refused(tags_of(way_id)) else 1
        assert row.access_ok == expected, "way %d: access_ok=%d" % (way_id, row.access_ok)


def test_customers_and_a_private_motor_vehicle_are_not_refused_the_way_the_throwaway_refused_them():
    """T-0206's throwaway read one list - {no, private, customers, delivery, permit, military} - against
    BOTH keys. `Gates.verdict` refuses neither of these, and a corpus stricter than the router is the same
    drift in the other direction (assemble.py's note on MOTOR_VEHICLE_KEY)."""
    assert way(CUSTOMERS).access_ok == 1
    assert way(MOTOR_VEHICLE_PRIVATE).access_ok == 1


def test_destination_permit_and_no_are_refused():
    for way_id in (DESTINATION, PERMIT, NO_ACCESS):
        assert way(way_id).access_ok == 0, way_id


def test_a_reverse_one_way_keeps_its_direction_and_a_two_way_keeps_both():
    assert way(ONEWAY_REVERSE).oneway == -1, "oneway=-1 collapsed to a two-way or a forward way"
    assert way(ONEWAY_FORWARD).oneway == 1
    assert way(ONEWAY_TWO_WAY).oneway == 0
    assert tags_of(ONEWAY_TWO_WAY)["oneway"] == "no"


def test_a_roundabout_is_one_way_with_or_without_the_tag_and_a_circular_junction_is_not():
    assert tags_of(ROUNDABOUT_UNTAGGED).get("oneway") is None
    assert way(ROUNDABOUT_UNTAGGED).oneway == 1, "OSM's roundabout implies one-way; the router reads this"
    assert way(ROUNDABOUT_TAGGED).oneway == 1
    assert tags_of(CIRCULAR)["junction"] == "circular" and "oneway" not in tags_of(CIRCULAR)
    assert way(CIRCULAR).oneway == 0, "junction=circular carries no one-way implication"


def test_a_class_outside_the_table_is_skipped_by_count_and_never_judged():
    """The two of 23,474 T-0206 skipped: way 1211805282 and way 1211805283, both highway=footway, kept by
    the osmium pass because they are tourism=attraction. Both carry motor_vehicle=no, so a silent skip
    would look exactly like two correctly refused roads."""
    for way_id in OUTSIDE_THE_TABLE:
        assert tags_of(way_id)["highway"] == "footway"
        assert way_id not in adapted()["ways"]
    line = adapted()["stdout"]
    assert "skipped_class=2" in line, line
    assert "ways=16" in line, line


def test_a_way_with_no_name_keeps_none_and_a_named_way_keeps_its_name():
    assert way(TRACK_PLAIN).name is None and "name" not in tags_of(TRACK_PLAIN)
    assert way(MOTORWAY_LINK).name is None
    assert way(ONEWAY_REVERSE).name == "Zuma Access Road"
    assert way(ONEWAY_TWO_WAY).name == "Vereda de la Montura"


def test_a_motorway_reaches_the_corpus_penalised_rather_than_excluded():
    row = way(MOTORWAY_LINK)
    assert row.cls == "motorway" and row.highway == "motorway_link"
    assert row.access_ok == 1 and row.oneway == 1


def test_the_surface_tag_travels_raw_and_the_three_states_are_counted_not_claimed():
    """`extractway` refuses a pre-derived surface column by name (RETIRED_WAY_KEYS), so the raw tag travels
    and `surface.surface_state` decides. The count line reports the three states it measured."""
    assert way(ONEWAY_FORWARD).surface is None
    assert way(MOTOR_VEHICLE_NO).surface == "asphalt"
    counts = extractadapter.adapt_document(json.loads(SLICE.read_text(encoding="utf-8")))[1]
    states = {surface.surface_state(highway=w.highway, surface=w.surface)
              for w in adapted()["ways"].values()}
    assert counts["surface_unpaved"] == sum(
        1 for w in adapted()["ways"].values() if w.surface_state == surface.SURFACE_UNPAVED)
    assert counts["surface_unpaved"] >= 1 and states >= {surface.SURFACE_UNPAVED}
    for name in extractadapter.COUNT_NAMES:
        assert "%s=%d" % (name, counts[name]) in adapted()["stdout"], (name, adapted()["stdout"])


def test_a_repeated_way_id_is_refused_by_name_rather_than_dropped():
    """The throwaway dropped a repeat in silence. Dropping one way moves every other way's rank."""
    doc = json.loads(SLICE.read_text(encoding="utf-8"))
    doc["ways"].append(dict(doc["ways"][0]))
    with pytest.raises(ValueError) as refusal:
        extractadapter.adapt_document(doc)
    assert str(doc["ways"][0]["way_id"]) in str(refusal.value), str(refusal.value)


def test_a_document_with_no_region_anywhere_is_refused_rather_than_guessed_at():
    doc = json.loads(SLICE.read_text(encoding="utf-8"))
    doc.pop("region")
    doc["meta"].pop("region")
    with pytest.raises(ValueError):
        extractadapter.adapt_document(doc)
    assert extractadapter.adapt_document(doc, region="la")[0]["region"] == "la"


def test_the_adapted_slice_builds_a_corpus_which_is_the_whole_point_of_the_path(tmp_path):
    from etl import corpus
    report = corpus.build(adapted()["path"], tmp_path / "slice.sqlite", "2026-09-18T00:00:00Z")
    assert report["ways"] == 16 and report["segments"] >= 16
    assert report["region"] == "la"


def test_the_nodes_are_the_documents_coordinates_in_document_order_on_every_row():
    """`oneway` is a FLAG, never a reordering: -1 means against the way's DRAWN direction, so the drawn
    direction has to survive the conversion or the router reads the flag against the wrong geometry.

    Read off the EXTRACT `main` WROTE - the artefact `python -m etl.corpus` reads, and the only place this
    order is observable - never off `ExtractWay.coords`, which `geom.canonical` has already oriented: the
    reader flips 8 of these 16 rows, 1288190701 among them, so an assertion there tests the READER (S1)."""
    doc = json.loads(SLICE.read_text(encoding="utf-8"))
    drawn = {row["way_id"]: [[float(lat), float(lon)] for lat, lon in row["coords"]]
             for row in doc["ways"]}
    written = json.loads(pathlib.Path(adapted()["path"]).read_text(encoding="utf-8"))
    assert len(written["ways"]) == 16
    for row in written["ways"]:
        assert row["nodes"] == drawn[row["id"]], "way %d: the nodes are not the document's" % row["id"]
    reverse = next(row for row in written["ways"] if row["id"] == ONEWAY_REVERSE)
    assert reverse["oneway"] == -1, "the flag and the geometry are read together or neither means anything"
    assert reverse["nodes"][0] == [34.016213, -118.8209048]
    assert reverse["nodes"][-1] == [34.0160665, -118.8196495]
    forward = next(row for row in written["ways"] if row["id"] == ONEWAY_FORWARD)
    assert forward["oneway"] == 1
    assert forward["nodes"][0] == [34.0772684, -118.5523092]
    assert forward["nodes"][-1] == [34.0771741, -118.5521751]


def test_a_one_node_way_is_skipped_by_count_and_never_reaches_the_reader():
    """`skipped_short` had never once been non-zero (S2). With the guard gone the failure mode is a
    refusal one module downstream - `load_extract` refuses the WHOLE document, "way 9000000001: needs at
    least 2 nodes, got 1" - not a silent write, so the count AND the absence are both asserted."""
    row = next(r for r in json.loads(SLICE.read_text(encoding="utf-8"))["ways"]
               if r["way_id"] == SHORT_SYNTHETIC)
    assert len(row["coords"]) == 1 and row["synthetic"]
    assert row["tags"]["highway"] in extractadapter.HIGHWAY_TO_CLS, "it must reach the short guard"
    assert "skipped_short=1" in adapted()["stdout"], adapted()["stdout"]
    assert SHORT_SYNTHETIC not in adapted()["ways"]
    written = json.loads(pathlib.Path(adapted()["path"]).read_text(encoding="utf-8"))
    assert SHORT_SYNTHETIC not in [row["id"] for row in written["ways"]]

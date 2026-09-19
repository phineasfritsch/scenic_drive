"""The 3DEP tile set must come from a region's bbox, not from a constant naming one region's tiles.

`dem.TILES` lists sfbay's eight, and `dem.tile_for` returns None for anything outside them - so in any
second region every point has NO elevation and the terrain terms of the scenic score are silently absent.
Absent, not wrong, which is the shape that does not announce itself.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl import dem  # noqa: E402
from etl import manifest as mf  # noqa: E402
from etl import region as rg  # noqa: E402

SFBAY = (-123.62, 36.85, -121.55, 38.92)
LA = (-119.00, 33.70, -117.85, 34.45)

ETL = Path(__file__).resolve().parents[1]
MANIFEST = ETL / "inputs" / "manifest.yaml"
LA_REGION_JSON = ETL / "regions" / "la" / "region.json"

# The two northern Orange County cities agent/rv-pr68 measured against the recorded bbox, with the
# coordinates that review quoted. Six more - Fullerton, Buena Park, Garden Grove, Westminster, Seal Beach,
# La Habra - are inside the same box; they are named in the region comment rather than typed here, because
# nothing in this tree records their coordinates and an agent must not invent one to pass its own test.
OC_CITIES_INSIDE_THE_BOX = [
    ("Anaheim", 33.8366, -117.9143),
    ("Santa Ana", 33.7455, -117.8677),
]

# LA's ACTIVE tile set, typed here rather than derived, because a check whose scope is the value under test
# passes over whatever that value shrinks to. Widening `dem.UNSERVED` by one name used to leave the whole
# suite green with LA down to three tiles; these four literals are what stops that.
LA_TILES = {"n34w118", "n34w119", "n35w118", "n35w119"}

# One point per LA tile, so no square is pinned only by the arithmetic that produced it. Every coordinate is
# already recorded in this tree - the bbox test below, or agent/rv-pr68's measured OC cities - except the
# first, which is the point PR #106's review names; none is invented to make this test pass.
LA_POINT_PER_TILE = [
    ("n35w118", 34.35, -117.86, "Angeles Crest Highway (SR-2) east of Red Box, toward Dawson Saddle"),
    ("n35w119", 34.1289, -118.4043, "Mulholland Drive at Coldwater Canyon"),
    ("n34w119", 33.7445, -118.3870, "the Palos Verdes peninsula, which Palos Verdes Drive rings"),
    ("n34w118", 33.8366, -117.9143, "Anaheim: a city point, not a road - nothing here records a road there"),
]


def test_derivation_reproduces_the_hand_typed_sfbay_list():
    """The oracle for a derivation is the list somebody already checked by hand.

    Anything sfbay pinned must be derived; the derivation may return MORE, because it does not know which
    tiles USGS actually serves.
    """
    derived = dem.tiles_for_bbox(*SFBAY)
    assert dem.TILES <= derived, f"derivation lost tiles sfbay pinned: {sorted(dem.TILES - derived)}"


def test_the_only_extra_over_sfbay_is_the_documented_ocean_tile():
    """n37w124 is entirely ocean and USGS 404s it - the one tile sfbay excludes on purpose.

    Pinning this stops the derivation quietly growing: a change that returned a ninth tile for sfbay would
    otherwise look like the same known exception.
    """
    assert dem.tiles_for_bbox(*SFBAY) - dem.TILES == {"n37w124"}


def test_la_needs_exactly_four_tiles():
    assert dem.tiles_for_bbox(*LA) == {"n34w118", "n34w119", "n35w118", "n35w119"}


def test_tile_name_uses_the_north_west_corner():
    """Getting this backwards yields a name that exists, for the wrong square - plausibly wrong elevations
    everywhere rather than missing ones."""
    assert dem.tile_name(34.07, -118.45) == "n35w119"   # UCLA
    assert dem.tile_name(37.78, -122.42) == "n38w123"   # San Francisco


def test_interior_squares_are_not_missed():
    """A corner-only implementation looks correct on any bbox narrower than a degree and drops the middle of
    a wide one. sfbay is 2.07 degrees wide, so it has interior squares no corner is in."""
    wide = dem.tiles_for_bbox(-124.5, 36.5, -121.5, 39.5)
    assert "n38w123" in wide and "n38w124" in wide and "n37w123" in wide
    # 3 x 3 degrees straddling the integer lines touches FOUR columns and FOUR rows, not three: the box
    # starts mid-square and ends mid-square. I first wrote 12 here and the code was right.
    assert len(wide) == 16, sorted(wide)


def test_a_bbox_touching_a_border_does_not_claim_the_next_square():
    """Exactly on the line is not overlap. `<=` on the far edge would add a whole row of squares."""
    assert dem.tiles_for_bbox(-118.0, 34.0, -117.0, 35.0) == {"n35w118"}


def test_the_la_region_file_loads_and_its_counts_come_from_a_real_extract():
    """This test used to assert la had NO counts, which was right until the extract ran.

    It ran on 2026-09-08 - 2m32s, 312 MB of California PBF cut to the la bbox - and recorded the counts, so
    the old assertion became a guard against the thing that had just correctly happened. It is replaced by
    the assertion that was always the real requirement: counts may exist, but only tied to the extract that
    produced them. Deleting the guard outright would have left nothing between here and an invented baseline.
    """
    la = rg.load("la")
    assert la.id == "la"
    assert la.bbox.problems() == []
    assert la.counts, "la's counts were recorded on 2026-09-08; an empty block means they were lost"
    assert la.counts_from is not None, "counts with no provenance cannot be checked against anything"
    assert la.counts_from.source_bytes > 1_000_000_000, "the California PBF is ~1.3 GB"
    measured = tuple(float(v) for v in la.counts_from.bbox.split(","))
    assert measured == (la.bbox.min_lon, la.bbox.min_lat, la.bbox.max_lon, la.bbox.max_lat)


def test_the_la_counts_are_the_shape_a_city_extract_has():
    """Not a transcription check - a sanity check on what the numbers mean.

    Any of these being wrong-way-round means the tag filter or the bbox is not doing what it says: LA has
    far more residential than motorway, and service roads (parking aisles, driveways) outnumber everything.
    """
    c = rg.load("la").counts
    assert c["residential"] > c["motorway"] * 4
    assert c["service"] > c["residential"]
    assert c["motorway"] > c["trunk"], "LA is a freeway city; trunk is the rarer tag here"
    assert c["viewpoint"] > 100, "the Santa Monicas and the San Gabriels are full of them"


def test_the_la_bbox_covers_ucla_and_the_santa_monicas():
    """The region exists so the developer can drive the routes; if it does not contain where they live and
    the mountains next to it, it is the wrong box."""
    la = rg.load("la").bbox
    for name, lat, lon in [
        ("UCLA", 34.0689, -118.4452),
        ("Mulholland at Coldwater", 34.1289, -118.4043),
        ("Malibu Canyon", 34.0700, -118.6960),
        ("Angeles Crest at Red Box", 34.2411, -118.0906),
        ("Palos Verdes", 33.7445, -118.3870),
    ]:
        assert la.min_lat <= lat <= la.max_lat and la.min_lon <= lon <= la.max_lon, f"{name} is outside"


def test_a_westwood_point_resolves_to_its_tile_when_la_is_active():
    """The defect [[T-0142]] closes. `tile_for` gated on TILES - sfbay's eight - so every point in LA had no
    tile, every elevation was absent, and the terrain terms of the scenic score were silently zero over the
    one region the developer can actually drive."""
    assert dem.tile_for(34.07, -118.45, tiles=dem.tiles_for_region("la")) == "n35w119"


def test_the_la_active_tile_set_is_exactly_the_four_typed_tiles():
    """sfbay's active set is pinned by equality; LA's was pinned by nothing.

    `tiles_for_bbox(*LA)` pins the arithmetic BEFORE `- UNSERVED`, and the manifest check used to iterate
    `tiles_for_region("la")`, which is the value under test - shrink it and it iterates fewer and passes,
    empty it and it iterates nothing and passes. This is the equality that closes that: four typed names
    against what `tile_for` actually gates LA on.
    """
    assert dem.tiles_for_region("la") == LA_TILES


def test_every_la_tile_carries_a_point_the_region_exists_for():
    """Set equality alone would not catch a tile that resolves for nobody, so each square is witnessed.

    n35w118 is the one the reviewer's mutant removed: Angeles Crest east of Red Box, which is why the bbox
    reaches -117.85 at all. A point with no tile is None, and None means no elevation - the terrain terms of
    the scenic score silently absent over exactly the roads this region was drawn to carry.
    """
    box = rg.load("la").bbox
    active = dem.tiles_for_region("la")
    assert {t for t, _lat, _lon, _w in LA_POINT_PER_TILE} == LA_TILES, "one witness per tile, no more, no less"
    for tile, lat, lon, where in LA_POINT_PER_TILE:
        assert box.min_lon <= lon <= box.max_lon and box.min_lat <= lat <= box.max_lat, \
            f"{where} ({lat},{lon}) is outside the la bbox - the box moved, re-argue this point"
        assert dem.tile_for(lat, lon, tiles=active) == tile, \
            f"{where} ({lat},{lon}) has no elevation: {tile} is not in LA's active set"


def test_served_tiles_notices_a_region_added_after_its_first_call(tmp_path):
    """The cache was keyed on the regions root alone, so a root's first answer was its only answer.

    `region_ids` saw a region added mid-process and `served_tiles` did not - two functions in this module
    disagreeing about which regions exist, with the stale one deciding whether a point gets elevation.

    Deliberately on the Dakota plains, not in California: this check is about the cache, so its answer must
    not move when a mutant edits `UNSERVED` or a region's bbox.
    """
    def write(region_id: str, min_lon: float, max_lon: float) -> None:
        d = tmp_path / region_id
        d.mkdir()
        (d / "region.json").write_text(json.dumps({
            "id": region_id, "name": region_id, "counties": ["nowhere"],
            "bbox": {"min_lon": min_lon, "min_lat": 44.1, "max_lon": max_lon, "max_lat": 44.3},
        }), encoding="utf-8")

    write("west", -100.5, -100.2)
    assert dem.served_tiles(root=tmp_path) == {"n45w101"}
    write("east", -99.9, -99.6)
    assert dem.region_ids(tmp_path) == ["east", "west"]
    assert dem.served_tiles(root=tmp_path) == {"n45w100", "n45w101"}, \
        "served_tiles answered from its cache while region_ids already saw the new region"


def test_the_sfbay_golden_set_is_exactly_what_the_derivation_serves():
    """TILES stays as the hand-checked sfbay list, but it is no longer what `tile_for` gates on. Pinning the
    two against each other is what stops the derivation drifting away from the list somebody verified."""
    assert dem.tiles_for_region("sfbay") == dem.TILES


def test_naming_no_region_no_longer_means_sfbay():
    """With no region named the answer is every tile WE SERVE, not one region's constant. A caller that
    forgets to name its region therefore gets LA's terrain rather than silent absence - the failure mode
    here is absence that looks like flat ground, so the default must not be able to produce it."""
    assert dem.tile_for(34.07, -118.45) == "n35w119"    # UCLA
    assert dem.tile_for(37.78, -122.42) == "n38w123"    # San Francisco, unchanged


def test_absence_is_still_absence_outside_the_active_region():
    """The flag semantics do not move: no tile is None, never 0 m, and 0 m is sea level - a real elevation."""
    assert dem.tile_for(45.0, -100.0, tiles=dem.tiles_for_region("la")) is None
    assert dem.tile_for(37.78, -122.42, tiles=dem.tiles_for_region("la")) is None
    assert dem.tile_for(36.5, -123.5) is None, "n37w124 is ocean, USGS 404s it, nobody serves it"


def test_grouping_and_sampling_carry_the_active_region_through():
    """`tile_for` learning the region is useless if the call the pipeline actually makes cannot pass it."""
    groups = dem.group_by_tile([(34.07, -118.45), (37.78, -122.42)], tiles=dem.tiles_for_region("la"))
    assert groups["n35w119"] == [0]
    assert groups[None] == [1]
    assert dem.sample([(34.07, -118.45)], runner=None, tiles=frozenset()) == [None]


def test_the_manifest_pins_every_tile_la_needs():
    """A derived tile set with nothing behind it is still no elevation: the file has to be fetchable and
    verifiable. Each of LA's four needs an entry pinned by sha256, like sfbay's eight.

    Iterates the FOUR TYPED NAMES, not `tiles_for_region("la")`. Iterating the function's own value made
    this loop's scope the value under test: a shrunken set iterated fewer tiles and passed, an empty one
    checked nothing and passed. `test_the_la_active_tile_set_is_exactly_the_four_typed_tiles` is what ties
    these names back to what `tile_for` gates on.
    """
    entries = {i.name: i for i in mf.parse(MANIFEST.read_text(encoding="utf-8"))}
    for tile in sorted(LA_TILES):
        entry = entries.get(f"3dep-{tile}.tif")
        assert entry is not None, f"3dep-{tile}.tif is not in inputs/manifest.yaml"
        assert entry.verify == "sha256", f"{entry.name} is not pinned by digest"
        assert re.fullmatch(r"[0-9a-f]{64}", entry.sha256 or ""), \
            f"{entry.name} sha256 is not 64 hex characters: {entry.sha256!r}"


def test_the_sfbay_eight_are_untouched():
    """This task adds four entries; it must not edit the eight that were already verified."""
    entries = {i.name: i for i in mf.parse(MANIFEST.read_text(encoding="utf-8"))}
    for tile in sorted(dem.TILES):
        entry = entries.get(f"3dep-{tile}.tif")
        assert entry is not None and entry.consumed_by == "T-0026", f"3dep-{tile}.tif moved"
        assert re.fullmatch(r"[0-9a-f]{64}", entry.sha256 or "")


def test_the_bbox_comment_does_not_claim_to_exclude_cities_the_box_contains():
    """Finding 1 of agent/rv-pr68's review of PR #68, as a check rather than a note.

    `_comment_bbox` said the box deliberately EXCLUDES Orange County while eight OC cities sit inside it.
    The bbox is what the counts were measured over (`counts_from`), so the fix is the sentence, not the box -
    but a region whose own file describes a different region than it cuts is how sfbay's baseline came to
    be a quarter Central Valley. These are JSON FIELDS of a committed config file, not code comments: they
    survive a strip, which is what makes them anchorable.
    """
    box = rg.load("la").bbox
    for name, lat, lon in OC_CITIES_INSIDE_THE_BOX:
        assert box.min_lon <= lon <= box.max_lon and box.min_lat <= lat <= box.max_lat, \
            f"{name} {lat},{lon} is no longer inside the la bbox - re-argue this test, do not delete it"
    raw = json.loads(LA_REGION_JSON.read_text(encoding="utf-8"))
    comment = raw["_comment_bbox"]
    assert "EXCLUDES" in comment, "the bbox comment must still say what the box leaves out"
    head, _, excluded = comment.partition("EXCLUDES")
    assert "Orange County" not in excluded, \
        "the comment claims to exclude Orange County; Anaheim and Santa Ana are inside the box"
    for name, _lat, _lon in OC_CITIES_INSIDE_THE_BOX:
        assert name in head, f"{name} is inside the box and the comment does not say so"
    assert "Orange" in raw["_comment_counties"], \
        "_comment_counties names the clipped neighbours; northern Orange County is one of them"

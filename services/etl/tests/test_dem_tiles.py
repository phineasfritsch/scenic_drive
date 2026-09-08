"""The 3DEP tile set must come from a region's bbox, not from a constant naming one region's tiles.

`dem.TILES` lists sfbay's eight, and `dem.tile_for` returns None for anything outside them - so in any
second region every point has NO elevation and the terrain terms of the scenic score are silently absent.
Absent, not wrong, which is the shape that does not announce itself.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl import dem  # noqa: E402
from etl import region as rg  # noqa: E402

SFBAY = (-123.62, 36.85, -121.55, 38.92)
LA = (-119.00, 33.70, -117.85, 34.45)


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


def test_the_la_region_file_loads_and_records_no_counts():
    """The counts block is deliberately absent until a real extract records it, and checkbounds must be
    able to tell that apart from 'in bounds'."""
    la = rg.load("la")
    assert la.id == "la"
    assert not la.counts, "la must ship with NO counts until an extract records them"
    assert la.bbox.problems() == []


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

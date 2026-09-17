"""region.json is read by the extract, by ops/sane and eventually by the corpus publisher.

A bbox typo there is not a crash, it is a smaller region that still builds, still routes, and is missing the
half of the Bay Area nobody looked at. So the loader refuses rather than shrugs.
"""
from __future__ import annotations

import json

import pytest

from etl import region as rg


def bbox(**kw):
    base = dict(min_lon=-123.62, min_lat=36.85, max_lon=-121.20, max_lat=38.92)
    base.update(kw)
    return rg.BBox(**base)


class TestTheCommittedRegion:
    def test_sfbay_loads_and_validates(self):
        r = rg.load("sfbay")
        assert r.id == "sfbay"
        assert r.problems() == []

    def test_sfbay_names_all_nine_counties(self):
        # The county list is what makes the bbox arguable. Nine ABAG counties; if someone trims the bbox,
        # the list is the thing that says what it was supposed to cover.
        assert len(rg.load("sfbay").counties) == 9

    def test_the_bbox_actually_contains_the_places_the_product_promises(self):
        b = rg.load("sfbay").bbox
        for name, lon, lat in [
            ("San Francisco", -122.419, 37.775),
            ("Skyline Blvd at CA-92", -122.353, 37.507),
            ("Mount Diablo summit", -121.914, 37.881),
            ("Half Moon Bay", -122.428, 37.463),
            ("Santa Cruz", -122.031, 36.974),
            ("Napa", -122.286, 38.297),
            ("Point Reyes lighthouse", -123.022, 37.996),
            ("Altamont Pass", -121.658, 37.732),
        ]:
            assert b.min_lon <= lon <= b.max_lon and b.min_lat <= lat <= b.max_lat, f"{name} is outside"

    def test_the_bbox_does_not_reach_into_the_central_valley(self):
        """The regression guard for the bug agent/reviewer-23 measured.

        max_lon was -121.20, about 40 km east of Altamont Pass, while the file's own comment said the edge
        was the Altamont. That pulled Tracy and Stockton into the extract and made 23.8% of every way - and
        28.6% of residential - Central Valley sprawl, so the counts ops/sane gates against described a
        different region than the one named. Nothing failed: the pipeline ran, the PBF was valid, the numbers
        looked plausible. Only counting what was inside the box found it.
        """
        b = rg.load("sfbay").bbox
        for name, lon, lat in [
            ("Tracy", -121.425, 37.740),
            ("Stockton", -121.290, 37.958),
            ("Modesto", -120.997, 37.639),
            ("Sacramento", -121.494, 38.582),
        ]:
            inside = b.min_lon <= lon <= b.max_lon and b.min_lat <= lat <= b.max_lat
            assert not inside, f"{name} is inside the Bay Area bbox"


class TestBBoxRefusesNonsense:
    def test_a_swapped_longitude_pair_is_refused(self):
        assert any("not west of" in p for p in bbox(min_lon=-121.2, max_lon=-123.62).problems())

    def test_a_swapped_latitude_pair_is_refused(self):
        assert any("not south of" in p for p in bbox(min_lat=38.92, max_lat=36.85).problems())

    def test_nan_is_not_a_coordinate(self):
        assert any("not a number" in p for p in bbox(min_lat=float("nan")).problems())

    def test_out_of_range_is_refused(self):
        assert any("outside" in p for p in bbox(min_lon=-181.0).problems())

    def test_a_degenerate_region_is_refused(self):
        """A truncated literal gives a valid, tiny, useless bbox."""
        assert any("below the" in p for p in bbox(max_lon=-123.61).problems())

    def test_the_whole_planet_is_not_an_extract(self):
        assert any("above the" in p for p in bbox(min_lon=-140.0).problems())

    def test_a_valid_bbox_has_no_problems(self):
        assert bbox().problems() == []

    def test_the_osmium_form_is_left_bottom_right_top(self):
        assert bbox().as_osmium() == "-123.62,36.85,-121.2,38.92"


class TestLoading:
    def write(self, tmp_path, doc):
        d = tmp_path / "probe"
        d.mkdir()
        (d / "region.json").write_text(json.dumps(doc), encoding="utf-8")
        return tmp_path

    def good(self):
        return {"id": "probe", "name": "Probe", "counties": ["Somewhere"],
                "bbox": {"min_lon": -123.62, "min_lat": 36.85, "max_lon": -121.2, "max_lat": 38.92}}

    def test_a_typoed_field_name_is_refused_rather_than_ignored(self, tmp_path):
        doc = self.good() | {"bounds": {}}
        with pytest.raises(ValueError, match="unknown field"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_underscore_prefixed_prose_is_allowed(self, tmp_path):
        doc = self.good() | {"_comment_bbox": "why this shape"}
        assert rg.load("probe", root=self.write(tmp_path, doc)).id == "probe"

    def test_an_empty_county_list_is_refused(self, tmp_path):
        doc = self.good() | {"counties": []}
        with pytest.raises(ValueError, match="counties is empty"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_a_missing_bbox_is_refused_rather_than_defaulted(self, tmp_path):
        doc = {k: v for k, v in self.good().items() if k != "bbox"}
        with pytest.raises(ValueError, match="not a number"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_a_non_integer_count_is_refused(self, tmp_path):
        doc = self.good() | {"counts": {"viewpoint": "many"}}
        with pytest.raises(ValueError, match="not a count"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_a_boolean_is_not_a_count(self, tmp_path):
        """bool is a subclass of int in Python; `True` must not read as 1 viewpoint."""
        doc = self.good() | {"counts": {"viewpoint": True}}
        with pytest.raises(ValueError, match="not a count"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_every_problem_is_reported_at_once(self, tmp_path):
        doc = self.good() | {"name": "", "counties": []}
        with pytest.raises(ValueError) as e:
            rg.load("probe", root=self.write(tmp_path, doc))
        assert "name is empty" in str(e.value) and "counties is empty" in str(e.value)

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


class TestCountsProvenance:
    """counts_from, and the one defect it exists for.

    On 2026-09-08 the first real sfbay extract came in 18-26% low on every single class. Nothing was broken:
    the bbox had been corrected months earlier from max_lon -121.20 to -121.55, removing Tracy and Stockton,
    and the recorded counts were never re-measured. The baseline had quietly become a description of a region
    the code no longer cuts, and it read exactly like a broken tag filter.

    The uniformity across classes is what identifies it, and no assertion in the codebase looked at that. So
    instead of a check on the counts, the fix is a check on their PROVENANCE: record the bbox they were
    measured over and refuse it disagreeing with the region's own bbox.
    """

    def write(self, tmp_path, doc):
        d = tmp_path / "probe"
        d.mkdir()
        (d / "region.json").write_text(json.dumps(doc), encoding="utf-8")
        return tmp_path

    def good(self):
        return {"id": "probe", "name": "Probe", "counties": ["Somewhere"],
                "bbox": {"min_lon": -123.62, "min_lat": 36.85, "max_lon": -121.2, "max_lat": 38.92},
                "counts": {"viewpoint": 746},
                "counts_from": {"source": "california-osm.pbf", "source_bytes": 1327206195,
                                "built_at": "2026-09-08T12:10:39Z",
                                "bbox": "-123.62,36.85,-121.2,38.92"}}

    def test_matching_provenance_loads(self, tmp_path):
        r = rg.load("probe", root=self.write(tmp_path, self.good()))
        assert r.counts == {"viewpoint": 746}
        assert r.counts_from.source == "california-osm.pbf"

    def test_counts_without_provenance_are_refused(self, tmp_path):
        doc = {k: v for k, v in self.good().items() if k != "counts_from"}
        with pytest.raises(ValueError, match="counts_from is absent"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_no_counts_and_no_provenance_is_fine(self, tmp_path):
        """A region with no baseline is honest. checkbounds reports 'cannot tell' and nothing pretends."""
        doc = {k: v for k, v in self.good().items() if k not in ("counts", "counts_from")}
        assert rg.load("probe", root=self.write(tmp_path, doc)).counts == {}

    def test_the_sfbay_defect_itself_a_corrected_bbox_with_stale_counts(self, tmp_path):
        """The exact historical state: the bbox is edited, the counts are left alone."""
        doc = self.good()
        doc["bbox"] = dict(doc["bbox"], max_lon=-121.55)     # the correction that was actually made
        with pytest.raises(ValueError, match="describes a different region than the code cuts"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_provenance_bbox_is_compared_numerically_not_as_a_string(self, tmp_path):
        """-121.20 and -121.2 are the same edge. A string compare would call this a stale baseline."""
        doc = self.good()
        doc["counts_from"] = dict(doc["counts_from"], bbox="-123.620,36.85,-121.20,38.920")
        assert rg.load("probe", root=self.write(tmp_path, doc)).counts_from is not None

    def test_a_provenance_block_with_no_source_is_refused(self, tmp_path):
        doc = self.good()
        doc["counts_from"] = dict(doc["counts_from"], source="")
        with pytest.raises(ValueError, match="counts_from.source is empty"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_a_zero_byte_source_is_not_a_source(self, tmp_path):
        doc = self.good()
        doc["counts_from"] = dict(doc["counts_from"], source_bytes=0)
        with pytest.raises(ValueError, match="source_bytes is not a size"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_a_malformed_provenance_bbox_is_refused(self, tmp_path):
        doc = self.good()
        doc["counts_from"] = dict(doc["counts_from"], bbox="-123.62,36.85,-121.2")
        with pytest.raises(ValueError, match="not four numbers"):
            rg.load("probe", root=self.write(tmp_path, doc))

    def test_every_shipped_region_ties_its_counts_to_the_bbox_they_were_measured_over(self):
        """The regression guard on the real files, not on a fixture.

        This is the assertion that would have caught the stale sfbay baseline the moment the bbox was
        edited. It runs over whatever regions exist rather than a hardcoded list, so a third region cannot
        be added without provenance, and it fails if there are no regions at all - a check that silently
        iterates over nothing proves nothing.
        """
        ids = sorted(p.name for p in rg.REGIONS.iterdir()
                     if p.is_dir() and (p / "region.json").is_file())
        assert len(ids) >= 2, f"expected at least sfbay and la, found {ids}"
        for rid in ids:
            r = rg.load(rid)                       # load() raises on any mismatch; this is the real check
            if r.counts:
                assert r.counts_from is not None, f"{rid} has counts with no provenance"
                measured = tuple(float(v) for v in r.counts_from.bbox.split(","))
                assert measured == (r.bbox.min_lon, r.bbox.min_lat, r.bbox.max_lon, r.bbox.max_lat), \
                    f"{rid}: counts measured over {r.counts_from.bbox}, bbox is {r.bbox.as_osmium()}"

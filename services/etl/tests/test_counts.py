"""Counts are the extract's self-report, and bounds are what stop it lying by omission.

The failure this guards is not a crash. It is an extract that runs, writes a valid PBF, and quietly contains
40% fewer residential ways than last week because a filter was "tidied". Everything downstream succeeds.
"""
from __future__ import annotations

import pytest

from etl import counts as ct

# Shape of a real `osmium fileinfo --extended --json` document, trimmed to what is read.
FILEINFO = """
{
  "file": {"name": "sfbay.osm.pbf", "format": "PBF"},
  "header": {"boxes": ["(-123.62,36.85,-121.2,38.92)"]},
  "data": {"count": {"nodes": 4210331, "ways": 512044, "relations": 8123}}
}
"""


class TestParsingFileinfo:
    def test_it_reads_the_three_object_counts(self):
        assert ct.parse_fileinfo(FILEINFO) == {"nodes": 4210331, "ways": 512044, "relations": 8123}

    def test_total_sums_them(self):
        assert ct.total(ct.parse_fileinfo(FILEINFO)) == 4210331 + 512044 + 8123

    def test_a_missing_kind_counts_as_zero_not_as_an_error(self):
        assert ct.parse_fileinfo('{"data":{"count":{"nodes":5}}}') == {"nodes": 5, "ways": 0, "relations": 0}

    @pytest.mark.parametrize("text,match", [
        ("not json at all", "not JSON"),
        ("[1,2,3]", "not an object"),
        ('{"file":{"name":"x"}}', "no data.count"),
        ('{"data":{"count":{"nodes":"lots"}}}', "not a count"),
        ('{"data":{"count":{"nodes":-1}}}', "not a count"),
        ('{"data":{"count":{"nodes":true}}}', "not a count"),
    ])
    def test_unreadable_output_raises_rather_than_reporting_zero(self, text, match):
        # Zero objects and "we could not read the report" are the same number and opposite meanings. Only one
        # of them is allowed to be silent, and it is neither.
        with pytest.raises(ValueError, match=match):
            ct.parse_fileinfo(text)


class TestBounds:
    RECORDED = {"motorway": 12000, "residential": 240000, "viewpoint": 620, "waterfall": 9}

    def test_an_unchanged_extract_is_in_bounds(self):
        assert ct.check_bounds(dict(self.RECORDED), self.RECORDED) == []

    def test_normal_weekly_drift_is_in_bounds(self):
        actual = self.RECORDED | {"residential": 248000, "viewpoint": 640}
        assert ct.check_bounds(actual, self.RECORDED) == []

    def test_a_collapse_is_reported_with_the_percentage(self):
        problems = ct.check_bounds(self.RECORDED | {"residential": 140000}, self.RECORDED)
        assert len(problems) == 1
        assert "residential" in problems[0] and "-41.7%" in problems[0]

    def test_a_class_that_vanished_is_named_as_missing_not_as_minus_100_percent(self):
        actual = {k: v for k, v in self.RECORDED.items() if k != "motorway"}
        problems = ct.check_bounds(actual, self.RECORDED)
        assert any("motorway" in p and "not present in this extract at all" in p for p in problems)

    def test_an_unexpected_new_class_is_reported_rather_than_accepted(self):
        problems = ct.check_bounds(self.RECORDED | {"steps": 400}, self.RECORDED)
        assert any("steps" in p and "never recorded" in p for p in problems)

    def test_a_small_class_gets_an_absolute_band_not_a_percentage(self):
        # 9 waterfalls -> 8 is -11%, inside tolerance anyway; 9 -> 5 is not, and percentage bands on tiny
        # numbers are noise either way. The absolute band is what makes the check mean something here.
        assert ct.check_bounds(self.RECORDED | {"waterfall": 8}, self.RECORDED) == []
        assert any("waterfall" in p for p in ct.check_bounds(self.RECORDED | {"waterfall": 5}, self.RECORDED))

    def test_a_growth_spike_is_reported_too(self):
        """Doubling is as suspicious as halving - usually a filter that started matching everything."""
        assert any("motorway" in p for p in ct.check_bounds(self.RECORDED | {"motorway": 30000},
                                                            self.RECORDED))

    def test_the_tolerance_is_configurable_and_actually_applied(self):
        actual = self.RECORDED | {"residential": 264000}   # +10%
        assert ct.check_bounds(actual, self.RECORDED) == []
        assert ct.check_bounds(actual, self.RECORDED, tolerance=0.05) != []

    def test_nothing_recorded_yet_means_nothing_to_check_but_new_classes_still_surface(self):
        # The first extract has no recorded counts. That must not read as "everything is fine forever".
        problems = ct.check_bounds({"motorway": 12000}, {})
        assert any("never recorded" in p for p in problems)

"""Parsing the two byway pulls.

The failure worth guarding is a filter that silently stops filtering: more rows, all of them wrong. In
California that means every Bay Area designation counted twice, once from Caltrans and once from FHWA's
re-publication of the same line under a federal FID.
"""
from __future__ import annotations

from etl import byway_source as bs
from etl import byways as bw


def feature(geometry, **props):
    return {"type": "Feature", "properties": props, "geometry": geometry}


LINE = {"type": "LineString", "coordinates": [[-122.35, 37.50], [-122.35, 37.49], [-122.35, 37.48]]}
MULTI = {"type": "MultiLineString",
         "coordinates": [[[-122.35, 37.50], [-122.35, 37.49]], [[-122.10, 37.20], [-122.10, 37.19]]]}


class TestRouteKey:
    def test_a_route_number_becomes_the_key(self):
        assert bs.route_key("280") == {"280"}
        assert bs.route_key(280) == {"280"}

    def test_a_padded_number_is_the_same_route(self):
        assert bs.route_key("0280") == {"280"}

    def test_anything_that_is_not_a_route_number_yields_no_key(self):
        """A key we cannot read must be absent, not guessed - `byways.problems` reports the absence, and a
        wrong key would silently match the wrong corridor."""
        assert bs.route_key(None) == set()
        assert bs.route_key("") == set()
        assert bs.route_key("35A") == set()


class TestAdminOrg:
    def test_it_is_read_as_a_token_set_not_a_string(self):
        """`Admin_Org` has 22 distinct values in the pull, most of them comma-separated combinations.
        String-matching 'NSB' would also match nothing sensible when the order changes."""
        assert bs.admin_orgs("NSB, STATE") == {"NSB", "STATE"}
        assert bs.admin_orgs("NSB, USFS, STATE") == {"NSB", "USFS", "STATE"}
        assert bs.admin_orgs("STATE") == {"STATE"}
        assert bs.admin_orgs(None) == set()


class TestCaltrans:
    def test_a_feature_becomes_an_entry_with_its_status_and_route(self):
        doc = {"features": [feature(LINE, Status="OD", RTE="35", CO="SM")]}
        got = bs.parse_caltrans(doc)
        assert len(got) == 1
        assert got[0]["status"] == "OD"
        assert got[0]["routes"] == {"35"}
        assert got[0]["source"] == bs.CALTRANS_SOURCE

    def test_coordinates_arrive_as_lat_lon_not_lon_lat(self):
        """GeoJSON is [lon, lat] and every distance function here takes (lat, lon). Swapped, the whole layer
        lands in the Southern Ocean and matches nothing, which looks exactly like 'no byways near here'."""
        got = bs.parse_caltrans({"features": [feature(LINE, Status="E", RTE="1", CO="SM")]})
        assert got[0]["geometry"][0] == (37.50, -122.35)

    def test_a_multilinestring_is_exploded_into_one_entry_per_part(self):
        """The parts are disjoint. Concatenating them puts a phantom straight segment between two real
        pieces of road, and anything lying under that phantom would snap to a corridor it is nowhere near -
        here the phantom would run 33 km across the Santa Cruz mountains."""
        got = bs.parse_caltrans({"features": [feature(MULTI, Status="OD", RTE="9", CO="SCL")]})
        assert len(got) == 2
        assert all(len(e["geometry"]) == 2 for e in got)
        assert all(e["routes"] == {"9"} for e in got)

    def test_a_status_arrives_upper_cased_and_stripped(self):
        got = bs.parse_caltrans({"features": [feature(LINE, Status=" od ", RTE="35", CO="SM")]})
        assert got[0]["status"] == bw.DESIGNATED

    def test_a_part_with_fewer_than_two_points_is_dropped(self):
        thin = {"type": "MultiLineString", "coordinates": [[[-122.35, 37.5]], [[-122.35, 37.5],
                                                                               [-122.35, 37.4]]]}
        assert len(bs.parse_caltrans({"features": [feature(thin, Status="OD", RTE="35", CO="SM")]})) == 1


class TestFhwa:
    def _doc(self):
        return {"features": [
            feature(LINE, Admin_Org="STATE", Type="National Scenic Byway", Trail_Name="Route 35--Skyline"),
            feature(LINE, Admin_Org="NSB, STATE", Type="National Scenic Byway", Trail_Name="Volcanic"),
            feature(LINE, Admin_Org="USFS", Type="National Scenic Byway", Trail_Name="Bigfoot"),
        ]}

    def test_only_rows_fhwa_itself_designated_are_kept(self):
        """A STATE row is that state's own byway republished federally. In California it is the Caltrans row
        arriving a second time, and keeping it double-counts every Bay Area designation."""
        got = bs.parse_fhwa(self._doc())
        assert [e["name"] for e in got] == ["Volcanic"]

    def test_a_kept_row_carries_the_designated_status(self):
        assert bs.parse_fhwa(self._doc())[0]["status"] == bw.DESIGNATED

    def test_a_kept_row_has_no_route_key(self):
        """Layer 107 has four fields and none is a route number, so an FHWA entry can only be matched on
        geometry. That is the weaker mode and it must not be mistaken for the strong one."""
        assert bs.parse_fhwa(self._doc())[0]["routes"] == set()

    def test_an_empty_layer_yields_nothing_rather_than_raising(self):
        assert bs.parse_fhwa({"features": []}) == []


class TestSourceProblems:
    def test_a_healthy_parse_has_no_problems(self):
        entries = (bs.parse_caltrans({"features": [feature(LINE, Status="OD", RTE="35", CO="SM")]})
                   + bs.parse_fhwa({"features": [feature(LINE, Admin_Org="NSB", Trail_Name="x")]}))
        assert bs.source_problems(entries) == []

    def test_an_fhwa_entry_with_a_route_key_is_reported(self):
        entries = [{"source": bs.FHWA_SOURCE, "routes": {"35"}, "geometry": []}]
        assert any("route key" in p for p in bs.source_problems(entries))

    def test_a_parse_with_no_caltrans_entries_at_all_is_reported(self):
        """California's designations come from Caltrans. An FHWA-only result means the Caltrans pull failed
        and the overlay is now silently missing 248 Bay Area entries."""
        entries = bs.parse_fhwa({"features": [feature(LINE, Admin_Org="NSB", Trail_Name="x")]})
        assert any("no Caltrans entries" in p for p in bs.source_problems(entries))

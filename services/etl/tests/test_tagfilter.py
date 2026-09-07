"""The filter decides what exists downstream. Everything it drops is invisible for the rest of the pipeline.

The product invariant these tests defend, from CLAUDE.md: motorway and trunk ways carry scenic_score 0 and are
PENALISED, not hard-excluded. An agent tidying up "we do not want freeways" at the extract stage does not make
routes prettier, it makes half the Bay Area's commutes unroutable - and nothing else in the pipeline notices,
because a missing way looks exactly like a way that was never there.
"""
from __future__ import annotations

import pytest

from etl import tagfilter as tf


class TestTheShippedFilter:
    def test_it_is_structurally_sound(self):
        assert tf.problems() == []

    def test_motorways_and_trunks_are_kept(self):
        """The invariant. They score 0; they are not excluded."""
        for cls in ("motorway", "trunk"):
            assert cls in tf.WAY_CLASSES
            assert tf.WAY_CLASSES[cls], f"{cls} keeps no highway values"

    def test_link_roads_are_kept_with_their_parent_class(self):
        # Dropping *_link disconnects every freeway from every surface street; the graph stays valid and the
        # routes silently stop using either.
        for cls in ("motorway", "trunk", "primary", "secondary", "tertiary"):
            assert any(v.endswith("_link") for v in tf.WAY_CLASSES[cls]), cls

    def test_track_is_kept_because_the_router_gates_it(self):
        """`road_class == TRACK` is a zero-gate in the profile (P-SAFE-01). A gate needs data to gate."""
        assert "track" in tf.WAY_CLASSES

    def test_viewpoints_are_kept_since_surprise_me_is_built_on_them(self):
        assert "viewpoint" in tf.POI_CLASSES

    def test_no_highway_value_is_claimed_by_two_classes(self):
        seen = [v for values in tf.WAY_CLASSES.values() for v in values]
        assert len(seen) == len(set(seen)), "a duplicated value would be double-counted"

    def test_every_class_has_an_expression(self):
        for cls in tf.all_classes():
            assert tf.class_expression(cls)

    def test_an_unknown_class_raises_rather_than_returning_an_empty_filter(self):
        # An empty expression passed to osmium tags-filter matches nothing, which would read as "that class
        # has zero objects" - the exact silent-drop this module exists to prevent.
        with pytest.raises(KeyError):
            tf.class_expression("gravel_goat_path")


class TestExpressionShape:
    def test_a_way_class_becomes_a_w_slash_highway_expression(self):
        assert tf.way_expression("motorway") == "w/highway=motorway,motorway_link"

    def test_a_poi_class_carries_its_object_types(self):
        assert tf.poi_expression("viewpoint") == "n/tourism=viewpoint"
        assert tf.poi_expression("park") == "wr/leisure=park"

    def test_a_way_class_matches_only_ways(self):
        assert tf.class_types("motorway") == ("w",)

    def test_a_mixed_poi_class_reports_both_of_its_types(self):
        assert tf.class_types("beach") == ("n", "w")

    def test_a_typed_expression_restricts_to_one_object_type(self):
        # Counting reads one type at a time: an nw/ filter keeps the nodes a matching way refers to, so its
        # node tally is tagged nodes plus geometry, which is not a count of anything.
        assert tf.typed_expression("beach", "n") == "n/natural=beach"
        assert tf.typed_expression("beach", "w") == "w/natural=beach"
        assert tf.typed_expression("motorway", "w") == "w/highway=motorway,motorway_link"

    def test_asking_for_a_type_a_class_cannot_match_raises(self):
        with pytest.raises(KeyError):
            tf.typed_expression("motorway", "n")

    def test_every_class_types_entry_is_a_real_osmium_type(self):
        for cls in tf.all_classes():
            assert set(tf.class_types(cls)) <= set("nwr"), cls

    def test_the_keep_pass_covers_every_class_in_one_run(self):
        assert len(tf.keep_expressions()) == len(tf.all_classes())


class TestTheStructuralCheckActuallyFires:
    """`problems()` is only worth having if it goes red. Each of these is a plausible bad edit."""

    def test_deleting_motorway_is_reported(self, monkeypatch):
        classes = {k: v for k, v in tf.WAY_CLASSES.items() if k != "motorway"}
        monkeypatch.setattr(tf, "WAY_CLASSES", classes)
        assert any("motorway is missing" in p for p in tf.problems())

    def test_emptying_a_routing_critical_class_is_reported(self, monkeypatch):
        monkeypatch.setattr(tf, "WAY_CLASSES", tf.WAY_CLASSES | {"trunk": ()})
        assert any("trunk keeps no highway values" in p for p in tf.problems())

    def test_a_value_claimed_twice_is_reported(self, monkeypatch):
        monkeypatch.setattr(tf, "WAY_CLASSES", tf.WAY_CLASSES | {"road": ("road", "residential")})
        assert any("double-count" in p for p in tf.problems())

    def test_a_bad_object_type_is_reported(self, monkeypatch):
        monkeypatch.setattr(tf, "POI_CLASSES", tf.POI_CLASSES | {"peak": ("x", "natural", ("peak",))})
        assert any("must be a non-empty subset" in p for p in tf.problems())

    def test_a_poi_class_with_no_values_is_reported(self, monkeypatch):
        monkeypatch.setattr(tf, "POI_CLASSES", tf.POI_CLASSES | {"peak": ("n", "natural", ())})
        assert any("needs a key and at least one value" in p for p in tf.problems())

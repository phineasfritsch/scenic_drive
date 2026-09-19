"""The OSM XML stream between osmium and the tag pass: everything survives, and twice is the same twice."""
from __future__ import annotations

import hashlib
import pathlib
import xml.etree.ElementTree as ET

import pytest

from etl import osmxml

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "scenic_clip.osm.xml"


def test_every_top_level_element_survives_a_read_write_round_trip(tmp_path):
    out = tmp_path / "copy.osm.xml"
    with osmxml.Writer(out) as writer:
        for elem in osmxml.iter_top_level(FIXTURE):
            writer.write(elem)
    before = ET.parse(FIXTURE).getroot()
    after = ET.parse(out).getroot()
    assert [e.tag for e in after] == [e.tag for e in before]
    assert [e.get("id") for e in after] == [e.get("id") for e in before]
    assert [(e.get("lat"), e.get("lon")) for e in after] == [(e.get("lat"), e.get("lon")) for e in before]


def test_a_ways_tags_and_node_refs_are_read_off_it():
    tags, refs = None, None
    for elem in osmxml.iter_top_level(FIXTURE):
        if elem.tag == osmxml.WAY and elem.get("id") == "101":
            tags, refs = osmxml.tags_of(elem), osmxml.refs_of(elem)
    assert tags == {"highway": "tertiary", "name": "Latigo Canyon Road"}
    assert refs == [11, 12, 13, 14]


def test_two_writes_of_the_same_document_are_byte_identical(tmp_path):
    digests = []
    for name in ("first", "second"):
        out = tmp_path / (name + ".osm.xml")
        with osmxml.Writer(out) as writer:
            for elem in osmxml.iter_top_level(FIXTURE):
                writer.write(elem)
        digests.append(hashlib.sha256(out.read_bytes()).hexdigest())
    assert digests[0] == digests[1]


def test_an_added_tag_lands_in_the_order_it_was_given(tmp_path):
    out = tmp_path / "tagged.osm.xml"
    with osmxml.Writer(out) as writer:
        for elem in osmxml.iter_top_level(FIXTURE):
            if elem.tag == osmxml.WAY and elem.get("id") == "101":
                osmxml.add_tags(elem, {"scenic_score": "7", "scenic_canopy": "0.5000"})
            writer.write(elem)
    way = [w for w in ET.parse(out).getroot().findall("way") if w.get("id") == "101"][0]
    assert [t.get("k") for t in way.findall("tag")] == \
        ["highway", "name", "scenic_score", "scenic_canopy"]


def test_adding_a_tag_the_way_already_carries_is_refused():
    for elem in osmxml.iter_top_level(FIXTURE):
        if elem.tag == osmxml.WAY and elem.get("id") == "101":
            with pytest.raises(ValueError, match="highway"):
                osmxml.add_tags(elem, {"highway": "motorway"})


def test_a_value_with_xml_syntax_in_it_survives_the_round_trip(tmp_path):
    """OSM names carry `&` and quotes; a writer that concatenates strings corrupts them silently."""
    src = tmp_path / "amp.osm.xml"
    src.write_text("<?xml version='1.0' encoding='UTF-8'?>\n<osm version=\"0.6\">\n"
                   "<way id=\"1\" version=\"1\"><tag k=\"name\" v=\"Bow &amp; Arrow &quot;Cut-off&quot;\"/>"
                   "</way>\n</osm>\n", encoding="utf-8")
    out = tmp_path / "copy.osm.xml"
    with osmxml.Writer(out) as writer:
        for elem in osmxml.iter_top_level(src):
            writer.write(elem)
    way = ET.parse(out).getroot().find("way")
    assert way.find("tag").get("v") == 'Bow & Arrow "Cut-off"'
